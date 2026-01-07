#!/usr/bin/env python3
"""
Convert podcast scripts to audio using text-to-speech.

Usage:
    python generate_podcast_audio.py --collection mental-models --entry anchoring
    python generate_podcast_audio.py --script path/to/script.md --output path/to/output.mp3
"""

import json
import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple
from openai import OpenAI
from pydub import AudioSegment
from pydub.effects import normalize
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def load_config():
    """Load podcast configuration."""
    config_path = Path(__file__).parent / "podcast_config.json"
    with open(config_path) as f:
        return json.load(f)


def parse_script(script_path: Path) -> List[Dict[str, str]]:
    """
    Parse a podcast script and extract speaker turns.
    
    Returns list of dicts with 'speaker' and 'text' keys.
    """
    with open(script_path) as f:
        content = f.read()
    
    turns = []
    
    # Match speaker labels like **SPEAKER_NAME:** or **Speaker Name:**
    pattern = r'\*\*([^*]+):\*\*\s*(.+?)(?=\n\*\*[^*]+:\*\*|\n###|\Z)'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        speaker = match.group(1).strip()
        text = match.group(2).strip()
        
        # Skip empty turns or segment markers
        if text and not text.startswith('#'):
            # Clean up the text
            text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            
            turns.append({
                'speaker': speaker,
                'text': text
            })
    
    return turns


def get_voice_for_speaker(speaker: str, collection: str, config: dict) -> str:
    """
    Map speaker name to OpenAI voice.
    
    OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
    """
    # Get panelists for this collection
    panelists = config['collections'][collection]['panelists']
    
    # Default voice mapping (can be customized in config later)
    voice_map = {
        'moderator': 'nova',      # Warm, clear female voice
        'biologist': 'onyx',      # Deep, authoritative male voice
        'historian': 'echo',      # Thoughtful male voice
        'psychologist': 'shimmer', # Calm female voice
        'theologian': 'fable',    # Wise, measured voice
        'practitioner': 'alloy',  # Neutral, experienced voice
        'chemist': 'onyx',
        'science historian': 'echo',
        'behavioral economist': 'shimmer',
        'strategy consultant': 'echo',
        'cognitive psychologist': 'nova'
    }
    
    # Find the panelist's role
    for panelist in panelists:
        if panelist['name'].lower() in speaker.lower():
            role = panelist['role'].lower()
            return voice_map.get(role, 'alloy')
    
    # Default fallback
    return 'alloy'


def generate_speech(text: str, voice: str, output_path: Path) -> Path:
    """
    Generate speech audio using OpenAI TTS.
    
    Returns path to generated audio file.
    """
    client = OpenAI()
    
    response = client.audio.speech.create(
        model="tts-1-hd",  # High quality model
        voice=voice,
        input=text,
        speed=1.0
    )
    
    response.stream_to_file(output_path)
    return output_path


def add_pause(duration_ms: int = 500) -> AudioSegment:
    """Create a silent pause."""
    return AudioSegment.silent(duration=duration_ms)


def mix_audio(turns: List[Dict], collection: str, config: dict, temp_dir: Path) -> AudioSegment:
    """
    Generate TTS for each turn and mix into final audio.
    """
    print(f"Generating audio for {len(turns)} speaker turns...")
    
    segments = []
    
    for i, turn in enumerate(turns):
        speaker = turn['speaker']
        text = turn['text']
        
        # Get voice for this speaker
        voice = get_voice_for_speaker(speaker, collection, config)
        
        # Generate TTS
        temp_file = temp_dir / f"turn_{i:03d}.mp3"
        print(f"  [{i+1}/{len(turns)}] {speaker} ({voice}): {text[:50]}...")
        
        generate_speech(text, voice, temp_file)
        
        # Load audio
        audio = AudioSegment.from_mp3(temp_file)
        
        # Add to segments with pause
        segments.append(audio)
        
        # Add pause between speakers (shorter if same speaker continues)
        if i < len(turns) - 1:
            next_speaker = turns[i + 1]['speaker']
            pause_duration = 300 if speaker == next_speaker else 700
            segments.append(add_pause(pause_duration))
    
    print("Mixing audio segments...")
    
    # Concatenate all segments
    final_audio = sum(segments)
    
    # Normalize audio levels
    print("Normalizing audio...")
    final_audio = normalize(final_audio)
    
    return final_audio


def add_intro_outro(audio: AudioSegment, collection: str) -> AudioSegment:
    """
    Add intro and outro music/silence.
    For now, just adds silence. Can be enhanced with actual music later.
    """
    intro = add_pause(1000)  # 1 second intro
    outro = add_pause(2000)  # 2 second outro
    
    return intro + audio + outro


def save_audio(audio: AudioSegment, output_path: Path, metadata: dict):
    """
    Save audio with metadata.
    """
    print(f"Saving audio to {output_path}...")
    
    # Export as MP3 with high quality
    audio.export(
        output_path,
        format="mp3",
        bitrate="192k",
        tags={
            'title': metadata.get('title', 'Podcast Episode'),
            'artist': metadata.get('artist', 'Alexandria Press'),
            'album': metadata.get('album', 'Mental Models Podcast'),
            'comments': metadata.get('description', '')
        }
    )
    
    print(f"✓ Audio saved: {output_path}")
    print(f"  Duration: {len(audio) / 1000:.1f} seconds ({len(audio) / 60000:.1f} minutes)")
    print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Convert podcast scripts to audio")
    parser.add_argument("--collection", help="Collection name (e.g., mental-models)")
    parser.add_argument("--entry", help="Entry slug (e.g., anchoring)")
    parser.add_argument("--script", help="Path to script file (alternative to collection/entry)")
    parser.add_argument("--output", help="Output audio file path")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Determine script path
    if args.script:
        script_path = Path(args.script)
        collection = args.collection or "unknown"
    elif args.collection and args.entry:
        script_path = Path(__file__).parent.parent / "outputs" / args.collection / "scripts" / f"{args.entry}.md"
        collection = args.collection
    else:
        print("Error: Must specify either --script or both --collection and --entry")
        return 1
    
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "outputs" / collection / "podcasts"
        output_dir.mkdir(parents=True, exist_ok=True)
        entry_name = args.entry or script_path.stem
        output_path = output_dir / f"{entry_name}.mp3"
    
    # Create temp directory for intermediate files
    temp_dir = Path("/tmp") / "podcast_audio" / script_path.stem
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Parse script
        print(f"Parsing script: {script_path}")
        turns = parse_script(script_path)
        print(f"Found {len(turns)} speaker turns")
        
        if not turns:
            print("Error: No speaker turns found in script")
            return 1
        
        # Generate and mix audio
        audio = mix_audio(turns, collection, config, temp_dir)
        
        # Add intro/outro
        audio = add_intro_outro(audio, collection)
        
        # Save with metadata
        metadata = {
            'title': f"{args.entry.replace('-', ' ').title() if args.entry else script_path.stem}",
            'artist': 'Alexandria Press',
            'album': f"{collection.replace('-', ' ').title()} Podcast",
            'description': f"A panel discussion exploring {args.entry or script_path.stem}"
        }
        
        save_audio(audio, output_path, metadata)
        
        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print(f"Audio file: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Clean up temp files
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())
