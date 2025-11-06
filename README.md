# StoryForge - YouTube Content Creator Tool

Simple AI-powered tool for individual YouTube vloggers to transform text ideas into complete videos with voice narration and B-roll footage.

## 🎬 For YouTube Creators

**Perfect for:** Solo content creators, vloggers, educators who want to quickly turn their ideas into polished videos.

**What it does:** You write your content → AI generates script → AI adds voice → AI selects B-roll → You get a finished video.

## 🚀 Quick Start

### 1. Setup

```bash
# Install and configure
python3 setup.py

# Add your API keys to config.yml
# Add B-roll videos to b-roll/ folder
```

### 2. Create Your Video

```bash
# Write your content in a text file, then:
python generate_video.py --input "Today I'll share 3 tips for better sleep..." --output "sleep-tips"

# Or use the web editor:
python editing_server/server.py
```

### 3. That's it! 

Your video will be in the projects folder, ready to upload to YouTube.

## 📱 Usage Options

**Command Line (fastest):**
```bash
python generate_video.py --input "Your video content..." --output "my-video"
```

**Web Interface (visual editing):**
```bash
python editing_server/server.py
# Opens browser interface for timeline editing
```

## 🛠 What You Need

- Python 3.8+
- API keys (get free trials):
  - Anthropic (Claude) - for script writing
  - OpenAI (GPT-4V) - for B-roll selection  
  - Gemini - for voice synthesis
- Some B-roll videos in the `b-roll/` folder

## 🎯 Perfect For

- **Educational content** - Turn your knowledge into videos
- **Vlogs** - Quick daily/weekly content creation
- **Reviews** - Product or service review videos
- **Tutorials** - How-to and guide videos
- **Commentary** - News or trend commentary

## 💡 Pro Tips

- Write naturally - the AI will make it flow better
- Add your own B-roll videos for better relevance
- Use the web editor to fine-tune timing
- Supports multiple languages for international audience

---

**Keep it simple.** One tool, one purpose: turn your ideas into YouTube videos fast.