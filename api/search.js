/**
 * Alexandria Press - Serverless Search API
 * Full-text search endpoint querying MongoDB Atlas.
 */

const { MongoClient } = require('mongodb');

let cachedClient = null;

async function getMongoClient() {
    if (cachedClient) return cachedClient;
    const uri = process.env.MONGODB_URI;
    if (!uri) throw new Error('MONGODB_URI environment variable is missing');
    cachedClient = new MongoClient(uri);
    await cachedClient.connect();
    return cachedClient;
}

module.exports = async function handler(req, res) {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    const query = req.query.q || req.query.query;
    if (!query || typeof query !== 'string' || !query.trim()) {
        return res.status(400).json({ error: 'Search query parameter "q" is required' });
    }

    try {
        const client = await getMongoClient();
        const db = client.db('alexandria');
        const chapters = db.collection('chapters');

        const results = await chapters
            .find(
                { $text: { $search: query.trim() } },
                { projection: { score: { $meta: 'textScore' } } }
            )
            .sort({ score: { $meta: 'textScore' } })
            .limit(15)
            .toArray();

        const formatted = results.map(item => {
            // Find snippet around query term
            const body = item.body || '';
            const lowerBody = body.toLowerCase();
            const firstTerm = query.trim().split(/\s+/)[0].toLowerCase();
            const idx = lowerBody.indexOf(firstTerm);
            let snippet = '';
            if (idx !== -1) {
                const start = Math.max(0, idx - 80);
                const end = Math.min(body.length, idx + 160);
                snippet = (start > 0 ? '...' : '') + body.slice(start, end).trim() + (end < body.length ? '...' : '');
            } else {
                snippet = body.slice(0, 180).trim() + '...';
            }

            return {
                book_key: item.book_key,
                book_title: item.book_title,
                category: item.category,
                chapter_index: item.chapter_index,
                label: item.label,
                title: item.title,
                subtitle: item.subtitle,
                snippet: snippet,
                score: item.score
            };
        });

        return res.status(200).json({
            query: query.trim(),
            count: formatted.length,
            results: formatted
        });

    } catch (err) {
        console.error('Search API error:', err);
        return res.status(500).json({ error: 'Internal search engine error', details: err.message });
    }
};
