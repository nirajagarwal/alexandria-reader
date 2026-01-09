# Audio Generation for Podcast Scripts

## Setup

1. **Install dependencies**:
   ```bash
   source venv/bin/activate
   pip install openai pydub audioop-lts
   ```
   
   Note: `audioop-lts` is required for Python 3.13+ compatibility with pydub.

2. **Install FFmpeg** (required by pydub):
   ```bash
   brew install ffmpeg
   ```

3. **Set your OpenAI API key**:
   
   Add to `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Generate audio from a script

```bash
source venv/bin/activate
python3 scripts/generate_podcast_audio.py --collection mental-models --entry anchoring
```

### Use a custom script file

```bash
python3 scripts/generate_podcast_audio.py --script path/to/script.md --output path/to/output.mp3
```

## How It Works

1. **Script Parsing**: Extracts speaker turns from markdown script
2. **Voice Mapping**: Maps each speaker to an appropriate OpenAI voice
3. **TTS Generation**: Generates audio for each turn using OpenAI TTS HD
4. **Audio Mixing**: Concatenates turns with appropriate pauses
5. **Enhancement**: Normalizes audio levels
6. **Metadata**: Adds ID3 tags (title, artist, album)

## OpenAI Voices

The script uses OpenAI's TTS voices:
- **nova**: Warm, clear female voice (moderators, psychologists)
- **shimmer**: Calm female voice (economists, practitioners)
- **alloy**: Neutral voice (general purpose)
- **echo**: Thoughtful male voice (historians, consultants)
- **fable**: Wise, measured voice (theologians)
- **onyx**: Deep, authoritative male voice (biologists, chemists)

## Output

Audio files are saved to: `outputs/{collection}/podcasts/{entry}.mp3`

- Format: MP3, 192kbps
- Includes ID3 metadata
- Normalized audio levels
- Natural pauses between speakers

## Cost

Using OpenAI TTS HD:
- ~$0.03 per 1000 characters
- ~$1.50-3.00 per 20-minute episode
- ~$40-80 for full collection (27 entries)

Much more affordable than ElevenLabs while still maintaining good quality!
