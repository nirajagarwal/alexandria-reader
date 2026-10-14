#!/usr/bin/env node
/**
 * Alexandria Press - MongoDB Synchronization & Full-Text Search Indexer
 * Syncs all 7 markdown volumes and their chapters to MongoDB Atlas.
 */

const dns = require('dns');
try { dns.setServers(['8.8.8.8', '1.1.1.1']); } catch (e) {}

const fs = require('fs');
const path = require('path');
const { MongoClient } = require('mongodb');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const MONGODB_URI = process.env.MONGODB_URI;
if (!MONGODB_URI) {
    console.error('Error: MONGODB_URI not found in .env');
    process.exit(1);
}

const BASE_DIR = path.join(__dirname, '..');

const BOOKS_METADATA = [
    { key: 'non-linear-engines', file: 'non_linear_engines.md', category: 'Startups' },
    { key: 'latent-fragility', file: 'latent_fragility.md', category: 'Failures' },
    { key: 'singular-minds', file: 'singular_minds.md', category: 'Thinkers' },
    { key: 'radical-subtraction', file: 'radical_subtraction.md', category: 'Christian Mystics' },
    { key: 'liminal-thresholds', file: 'liminal_thresholds.md', category: 'Physics' },
    { key: 'autonomous-engine', file: 'autonomous_engine.md', category: 'Physiology' },
    { key: 'elemental-asymmetries', file: 'elemental_asymmetries.md', category: 'Material Science' },
    { key: 'affective-topologies', file: 'affective_topologies.md', category: 'Neuroscience' },
    { key: 'architectures-of-choice', file: 'architectures_of_choice.md', category: 'Decision Science' },
    { key: 'tales-of-audacity', file: 'tales_of_audacity.md', category: 'History & Strategy' },
    { key: 'alexandria-manifesto', file: 'alexandria_manifesto.md', category: 'Platform' }
];

function parseAlexandriaMarkdown(mdText) {
    const sections = mdText.split(/\n---\n/);
    const chapters = [];
    let bookTitle = "Alexandria Volume";
    let bookSubtitle = "";

    sections.forEach((sec, idx) => {
        sec = sec.trim();
        if (!sec) return;

        if (idx === 0 && sec.startsWith('# ')) {
            const firstLines = sec.split('\n');
            bookTitle = firstLines[0].replace(/^#\s+/, '').trim();
            if (firstLines.length > 1 && firstLines[1].startsWith('## ')) {
                bookSubtitle = firstLines[1].replace(/^##\s+/, '').trim();
            }
            return;
        }

        const lines = sec.split('\n');
        let label = "";
        let title = "";
        let subtitle = "";
        let bodyStartIndex = 0;

        for (let i = 0; i < lines.length; i++) {
            const l = lines[i].trim();
            if (l.startsWith('### ')) {
                label = l.replace(/^###\s+/, '').trim();
                if (i + 1 < lines.length && lines[i + 1].trim().startsWith('# ')) {
                    title = lines[i + 1].trim().replace(/^#\s+/, '').trim();
                }
                if (i + 2 < lines.length && lines[i + 2].trim().startsWith('## ')) {
                    subtitle = lines[i + 2].trim().replace(/^##\s+/, '').trim();
                }
                bodyStartIndex = i + 3;
                break;
            }
        }

        const rawBody = lines.slice(bodyStartIndex).join('\n').trim();
        chapters.push({
            chapter_index: chapters.length,
            label: label || (idx === 0 ? "Introduction" : `Chapter ${idx}`),
            title: title || "Untitled Chapter",
            subtitle: subtitle || "",
            body: rawBody,
            word_count: rawBody.split(/\s+/).filter(Boolean).length
        });
    });

    return {
        title: bookTitle,
        subtitle: bookSubtitle,
        chapters: chapters
    };
}

async function syncToMongoDB() {
    console.log('Connecting to MongoDB Atlas...');
    const client = new MongoClient(MONGODB_URI);

    try {
        await client.connect();
        const db = client.db('alexandria');
        console.log('Connected successfully. Target database: "alexandria"');

        const booksCollection = db.collection('books');
        const chaptersCollection = db.collection('chapters');

        // 1. Ingest books and chapters
        for (const meta of BOOKS_METADATA) {
            const filePath = path.join(BASE_DIR, meta.file);
            if (!fs.existsSync(filePath)) {
                console.warn(`File not found: ${meta.file}`);
                continue;
            }

            const mdContent = fs.readFileSync(filePath, 'utf-8');
            const parsed = parseAlexandriaMarkdown(mdContent);

            console.log(`Syncing "${parsed.title}" (${meta.key}) - ${parsed.chapters.length} chapters...`);

            // Upsert book record
            await booksCollection.updateOne(
                { key: meta.key },
                {
                    $set: {
                        key: meta.key,
                        title: parsed.title,
                        subtitle: parsed.subtitle,
                        category: meta.category,
                        filename: meta.file,
                        chapter_count: parsed.chapters.length,
                        updated_at: new Date()
                    }
                },
                { upsert: true }
            );

            // Upsert chapters
            for (const ch of parsed.chapters) {
                await chaptersCollection.updateOne(
                    { book_key: meta.key, chapter_index: ch.chapter_index },
                    {
                        $set: {
                            book_key: meta.key,
                            book_title: parsed.title,
                            category: meta.category,
                            chapter_index: ch.chapter_index,
                            label: ch.label,
                            title: ch.title,
                            subtitle: ch.subtitle,
                            body: ch.body,
                            word_count: ch.word_count,
                            updated_at: new Date()
                        }
                    },
                    { upsert: true }
                );
            }
        }

        // 2. Create full-text search indexes
        console.log('Building full-text search index on chapters collection...');
        await chaptersCollection.createIndex(
            {
                title: 'text',
                subtitle: 'text',
                label: 'text',
                body: 'text'
            },
            {
                weights: {
                    title: 10,
                    subtitle: 5,
                    label: 3,
                    body: 1
                },
                name: 'chapter_full_text_search'
            }
        );

        console.log('Building metadata index on books collection...');
        await booksCollection.createIndex({ key: 1 }, { unique: true });

        const bookCount = await booksCollection.countDocuments();
        const chapterCount = await chaptersCollection.countDocuments();

        console.log('\n--- MONGODB SYNC COMPLETE ---');
        console.log(`Indexed ${bookCount} books and ${chapterCount} chapters with full-text search.`);

    } catch (err) {
        console.error('MongoDB Sync Error:', err);
    } finally {
        await client.close();
    }
}

if (require.main === module) {
    syncToMongoDB();
}

module.exports = { syncToMongoDB, parseAlexandriaMarkdown };
