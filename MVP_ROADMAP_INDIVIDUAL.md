# 🚀 StoryForge MVP Roadmap - Individual User Focus

## 🎯 MVP Vision: Individual Creator Tool

**Goal**: Deliver a working video generation tool for individual content creators in the **shortest time** with **minimal budget** and **essential functionality only**.

**Target User**: Individual YouTuber, blogger, or content creator who wants to generate videos from text without technical complexity.

**Success Metric**: User can input text and get a complete video file ready for upload.

---

## 📊 Current Reality Check

### ✅ What's Already Working (80% of MVP!)
1. **Text → Script**: Claude AI generates structured content ✅
2. **Script → Voice**: Gemini TTS creates audio files ✅  
3. **Voice → B-roll Selection**: AI selects relevant video clips ✅
4. **B-roll → Timeline**: JSON timing data for video editing ✅

### 🔴 What's Missing for MVP (20% remaining)
1. **Final Video Assembly**: Combine audio + B-roll into MP4 file
2. **Simple User Interface**: Basic way to input text and get video
3. **Error Handling**: Graceful failures and user feedback

**The good news**: You're much closer than you think! The AI intelligence is done.

---

## 🛣️ Ultra-Fast MVP Roadmap (1-2 weeks)

### Week 1: Video Assembly Engine (Priority #1) - 5-7 days
**Goal**: Create the missing video assembly component

#### **Day 1-2: Analysis & Setup**
1. **Understand the data flow**:
   ```bash
   # Audio files location:
   projects/my-project-06/english/audio/bullet_001.mp3
   projects/my-project-06/english/audio/bullet_002.mp3
   
   # B-roll timing data:
   temp/broll_timing.json
   
   # B-roll videos:
   b-roll/*.mp4
   ```

2. **Install video processing dependencies**:
   ```bash
   pip install moviepy opencv-python
   ```

#### **Day 3-5: Create Video Assembler**
**File**: `simple_video_assembler.py`

```python
#!/usr/bin/env python3
"""
Simple Video Assembler - The Missing MVP Component
Combines audio + B-roll into final MP4 using existing JSON timing data.
"""

import json
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import logging

def create_video_from_project(project_name, language="english", output_path=None):
    """
    Main function that creates final video from existing components.
    
    Args:
        project_name (str): Project name (e.g., "my-project-06")
        language (str): Language (e.g., "english")
        output_path (str): Output file path (default: project_name.mp4)
    
    Returns:
        str: Path to created video file
    """
    # 1. Load timing data
    timing_file = Path("temp/broll_timing.json")
    if not timing_file.exists():
        raise FileNotFoundError("broll_timing.json not found. Run B-roll selection first.")
    
    with open(timing_file) as f:
        timing_data = json.load(f)
    
    # 2. Load audio files
    audio_dir = Path(f"projects/{project_name}/{language}/audio")
    audio_files = sorted(audio_dir.glob("bullet_*.mp3"))
    
    if not audio_files:
        raise FileNotFoundError(f"No audio files found in {audio_dir}")
    
    # 3. Create video timeline
    video_clips = []
    audio_clips = []
    current_time = 0
    
    for rush_id, rush_data in timing_data["rushes"].items():
        rush_duration = rush_data["duration"]
        brolls = rush_data.get("brolls", [])
        
        # Add audio clip
        audio_file = audio_files[int(rush_id.replace("rush", "")) - 1]
        audio_clip = AudioFileClip(str(audio_file))
        audio_clips.append(audio_clip.set_start(current_time))
        
        # Add B-roll clips for this rush
        for broll in brolls:
            broll_path = Path("b-roll") / broll["filename"]
            if broll_path.exists():
                video_clip = VideoFileClip(str(broll_path))
                # Trim to specified duration and set timing
                video_clip = video_clip.subclip(0, min(broll["duration"], video_clip.duration))
                video_clip = video_clip.set_start(current_time + broll["start_time"])
                video_clips.append(video_clip)
        
        current_time += rush_duration
    
    # 4. Combine everything
    if not video_clips:
        raise ValueError("No B-roll clips found to create video")
    
    final_video = CompositeVideoClip(video_clips)
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.set_audio(final_audio)
    
    # 5. Export final video
    if output_path is None:
        output_path = f"{project_name}_final.mp4"
    
    logging.info(f"Exporting final video to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac'
    )
    
    # 6. Cleanup
    final_video.close()
    for clip in video_clips + audio_clips:
        clip.close()
    
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create final video from project components")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--language", default="english", help="Language")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        output_file = create_video_from_project(args.project, args.language, args.output)
        print(f"✅ Video created successfully: {output_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
```

#### **Day 6-7: Test & Refine**
```bash
# Test with existing project
python simple_video_assembler.py --project my-project-06 --language english

# Expected output: my-project-06_final.mp4 (ready to upload)
```

### Week 2: All-in-One Interface (Priority #2) - 3-5 days
**Goal**: Create dead-simple user interface

#### **Option A: Single Command MVP (Day 1-2)**
**File**: `generate_video.py`

```python
#!/usr/bin/env python3
"""
One-Command Video Generator - Complete MVP
Input text → Final video in one command
"""

import argparse
import subprocess
import sys
import logging
from pathlib import Path
import tempfile

def generate_complete_video(input_text, output_name, language="english"):
    """
    Complete video generation pipeline.
    
    Args:
        input_text (str): Text content for the video
        output_name (str): Name for the project and output file
        language (str): Language for generation
    
    Returns:
        str: Path to final video file
    """
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # Step 1: Save input text
    input_file = temp_dir / "input.txt"
    with open(input_file, "w", encoding="utf-8") as f:
        f.write(input_text)
    
    print("🔄 Step 1/4: Generating script and voice...")
    try:
        cmd = [
            sys.executable, "script_and_voice/module_script_and_voice.py",
            "--project", output_name,
            "--language", language,
            "--input-file", str(input_file)
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Script and voice completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Script generation failed: {e.stderr}")
        return None
    
    print("🔄 Step 2/4: Extracting B-roll metadata (first time only)...")
    try:
        cmd = [sys.executable, "-m", "b_roll.cli", "extract-metadata"]
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ B-roll metadata ready")
    except subprocess.CalledProcessError:
        print("⚠️ B-roll metadata extraction skipped (may already exist)")
    
    print("🔄 Step 3/4: Selecting B-roll footage...")
    try:
        cmd = [sys.executable, "-m", "b_roll.cli", "prepare-vectors"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ B-roll selection completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ B-roll selection failed: {e.stderr}")
        return None
    
    print("🔄 Step 4/4: Creating final video...")
    try:
        cmd = [
            sys.executable, "simple_video_assembler.py",
            "--project", output_name,
            "--language", language,
            "--output", f"{output_name}.mp4"
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Final video created: {output_name}.mp4")
        return f"{output_name}.mp4"
    except subprocess.CalledProcessError as e:
        print(f"❌ Video assembly failed: {e.stderr}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate complete video from text")
    parser.add_argument("--input", required=True, help="Input text content")
    parser.add_argument("--output", required=True, help="Output video name")
    parser.add_argument("--language", default="english", help="Language")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting video generation for '{args.output}'...")
    
    result = generate_complete_video(args.input, args.output, args.language)
    
    if result:
        print(f"🎉 SUCCESS! Your video is ready: {result}")
        print(f"📺 Upload it to YouTube, TikTok, or wherever you want!")
    else:
        print("❌ Video generation failed. Check the errors above.")
```

**Usage**:
```bash
python generate_video.py \
    --input "Your amazing content here..." \
    --output "my-awesome-video" \
    --language english

# Output: my-awesome-video.mp4 (ready to upload!)
```

#### **Option B: Simple Web Interface (Day 3-5, if time permits)**
**File**: `web_interface.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>StoryForge Video Generator</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        textarea { width: 100%; height: 200px; margin: 10px 0; }
        button { background: #007cba; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .progress { display: none; margin: 20px 0; }
        .result { margin: 20px 0; padding: 15px; background: #f0f0f0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🎬 StoryForge - AI Video Generator</h1>
    <p>Transform your text into a complete video with AI-powered script, voice, and B-roll footage.</p>
    
    <form id="videoForm">
        <label><strong>Your Content:</strong></label><br>
        <textarea id="content" placeholder="Paste your text, ideas, or script here..."></textarea>
        
        <label><strong>Video Name:</strong></label><br>
        <input type="text" id="videoName" placeholder="my-awesome-video" style="width: 300px; padding: 5px;">
        
        <label><strong>Language:</strong></label><br>
        <select id="language" style="padding: 5px;">
            <option value="english">English</option>
            <option value="french">French</option>
            <option value="german">German</option>
            <option value="spanish">Spanish</option>
        </select>
        
        <br><br>
        <button type="submit">🚀 Generate Video</button>
    </form>
    
    <div id="progress" class="progress">
        <h3>🔄 Processing your video...</h3>
        <div id="status">Starting generation...</div>
    </div>
    
    <div id="result" class="result" style="display: none;">
        <h3>🎉 Your video is ready!</h3>
        <p>Download: <a id="downloadLink" href="#">Download Video</a></p>
    </div>

    <script>
        document.getElementById('videoForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const content = document.getElementById('content').value;
            const videoName = document.getElementById('videoName').value;
            const language = document.getElementById('language').value;
            
            if (!content || !videoName) {
                alert('Please fill in all fields');
                return;
            }
            
            // Show progress
            document.getElementById('progress').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content, videoName, language})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('downloadLink').href = result.videoPath;
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
            
            document.getElementById('progress').style.display = 'none';
        };
    </script>
</body>
</html>
```

---

## 💰 Ultra-Low Budget Implementation

### Free/Cheap Tools Strategy
1. **No Database**: Use file system for projects (zero cost)
2. **No Complex UI**: Simple HTML form or CLI (zero cost)
3. **Existing APIs**: Leverage your current API keys (existing cost)
4. **Local Processing**: No cloud servers needed (zero hosting cost)
5. **Open Source**: MoviePy, Python built-ins (zero licensing)

### Cost Analysis
| Component | Cost | Notes |
|-----------|------|-------|
| API calls (Claude, OpenAI, Gemini) | $5-20/month | Only pay for usage |
| Development tools | $0 | Python, VS Code, git |
| Hosting | $0 | Run locally |
| UI Framework | $0 | Simple HTML or CLI |
| **Total Monthly Cost** | **$5-20** | Scales with usage |

---

## 🔧 Minimal Viable Feature Set

### Core Features (MUST HAVE)
- [x] Text input → Script generation ✅ (script_and_voice module)
- [x] Script → Voice synthesis ✅ (Gemini TTS)
- [x] Voice → B-roll selection ✅ (b_roll module with AI intelligence)
- [x] B-roll timing → JSON timeline ✅ (broll_timing.json generation)
- [ ] **JSON timeline → Final MP4 video** ❌ **THIS IS THE ONLY MISSING PIECE**
- [ ] Simple user interface (CLI or basic web form) ❌

### Current Workflow That Works
```bash
# Step 1: Generate script and voice (WORKS ✅)
cd script_and_voice
python module_script_and_voice.py --project my-video --language english --input-file input.txt

# Step 2: Generate B-roll selection (WORKS ✅)  
cd ..
python -m b_roll.cli extract-metadata    # First time only
python -m b_roll.cli prepare-vectors     # Creates broll_timing.json

# Step 3: Final video assembly (MISSING ❌)
# Need: python create_final_video.py --project my-video --language english
```

### **Analysis: What's Really Missing**

After analyzing the codebase, I found:
1. **Script generation**: ✅ 100% complete and working
2. **Voice synthesis**: ✅ 100% complete and working  
3. **B-roll intelligence**: ✅ 100% complete and working
4. **Timeline JSON**: ✅ Generated correctly in `temp/broll_timing.json`
5. **Video assembly**: ❌ **Missing entirely**

The `fin_montage()` function in `jouer_son.py` is just an audio notification, not actual video assembly code.

### Nice-to-Have (SKIP FOR MVP)
- ~~Multi-user support~~
- ~~Advanced editing interface~~
- ~~Database storage~~
- ~~User authentication~~
- ~~Video preview~~
- ~~Batch processing~~
- ~~Advanced configuration~~

### MVP User Flow
```
1. User inputs text: "Your amazing content here..."
2. User runs: python generate_video.py --input "..." --output "my-video"
3. System generates script (existing: script_and_voice module) ✅
4. System creates voice audio (existing: Gemini TTS) ✅
5. System selects B-roll videos (existing: b_roll module) ✅
6. System combines everything into MP4 (NEW: simple_video_assembler.py) ❌
7. User gets: my-video.mp4 (ready to upload)
```

**Total user time**: 3-8 minutes  
**Total development time**: 1-2 weeks  
**User experience**: One command → ready video

---

## 📋 Immediate Action Plan (Next 7 Days)

### Day 1: Set up video processing environment
```bash
# Install required dependencies
pip install moviepy opencv-python

# Test with sample project
ls projects/my-project-06/english/audio/    # Should show bullet_*.mp3 files
cat temp/broll_timing.json                  # Should show timing data
ls b-roll/*.mp4                            # Should show B-roll videos
```

### Day 2-3: Create the video assembler
```bash
# Create the missing component
touch simple_video_assembler.py

# Implement the MoviePy logic (see code above)
# Test with: python simple_video_assembler.py --project my-project-06 --language english
```

### Day 4-5: Create the all-in-one interface  
```bash
# Create the one-command solution
touch generate_video.py

# Test complete pipeline:
python generate_video.py --input "Test content for my video" --output "test-video"
```

### Day 6-7: Test with real content
```bash
# Test with various content types
python generate_video.py \
    --input "Today I'll show you 3 simple investing strategies..." \
    --output "investing-tips" \
    --language english

# Verify output quality and fix issues
```

---

## 📋 Immediate Action Plan (Next 7 Days)

### Day 1-2: Analyze Video Assembly
```bash
# Study existing video generation code
cd /home/kostiantyn/projects/storyforge
grep -r "moviepy\|ffmpeg\|video" . --include="*.py"

# Find the video assembly logic in exponential_video.py
# Extract reusable components
```

### Day 3-5: Create Simple Video Assembler
```python
# Create: simple_video_assembler.py
from moviepy.editor import *
import json

def create_video_from_project(project_name, language="english"):
    """Main function that combines everything into final video"""
    # 1. Load audio files from projects/{project_name}/{language}/audio/
    # 2. Load B-roll timing from temp/broll_timing.json
    # 3. Create video timeline with MoviePy
    # 4. Export as MP4
    
# Test with existing project
create_video_from_project("my-project-06", "english")
```

### Day 6-7: Create All-in-One Script
```python
# Create: generate_video.py (single entry point)
import argparse
from script_and_voice.module_script_and_voice import main as generate_script_voice
from b_roll.cli import main as generate_broll
from simple_video_assembler import create_video_from_project

def generate_complete_video(input_text, project_name, language="english"):
    """One function that does everything"""
    # 1. Save input_text to file
    # 2. Call script_and_voice module
    # 3. Call b_roll module  
    # 4. Call video assembler
    # 5. Return path to final video
```

---

## 🧪 MVP Testing Strategy

### Manual Testing (Day 6-7)
```bash
# Test complete pipeline
echo "Your test content here" > input.txt
python generate_video.py --input input.txt --project test-video --language english

# Expected output: test-video.mp4 (ready to upload)
# Time: 2-5 minutes
```

### Success Criteria
- [ ] Script generation works (should already work)
- [ ] Voice synthesis works (should already work)  
- [ ] B-roll selection works (should already work)
- [ ] Video assembly produces valid MP4 file
- [ ] Total process completes in under 10 minutes
- [ ] Output video is upload-ready quality

---

## 🚀 Week 2+ Enhancements (Optional)

### If Extra Time Available
1. **Simple Web Interface**:
   ```html
   <!-- Single HTML file with basic form -->
   <input type="file" accept=".txt">
   <button onclick="generateVideo()">Create Video</button>
   <div id="status">Ready</div>
   ```

2. **Progress Feedback**:
   ```bash
   ✅ Generating script... (30 seconds)
   ✅ Creating voice audio... (60 seconds)  
   ✅ Selecting B-roll footage... (45 seconds)
   ✅ Assembling final video... (90 seconds)
   ✅ Done! Your video is ready.
   ```

3. **Basic Error Recovery**:
   ```python
   try:
       generate_script()
   except Exception as e:
       print(f"Script generation failed: {e}")
       print("Try simplifying your input text")
   ```

---

## 💡 Why This MVP Strategy Works

### Advantages
1. **Builds on Existing Strengths**: 80% is already done
2. **Minimal Risk**: Small changes to working system
3. **Fast Time to Market**: 2-4 weeks vs 3-4 months
4. **Low Cost**: Under $20/month to operate
5. **Real User Value**: Complete working solution
6. **Easy to Iterate**: Add features after MVP proves valuable

### Validation Approach
1. **Week 1**: Get basic video generation working
2. **Week 2**: Test with 3-5 real users (friends, colleagues)
3. **Week 3**: Gather feedback and fix critical issues
4. **Week 4**: Document and prepare for wider testing

### Future Scaling
Once MVP proves valuable:
- Add web interface for easier use
- Improve video quality and customization
- Add user accounts and project management
- Consider commercial features

---

## 🎯 Bottom Line

**You're 1 component away from a working MVP**: Video assembly.

**Everything else already works**: Script generation, voice synthesis, B-roll intelligence.

**Fastest path**: Extract video assembly from existing `exponential_video.py` and create simple all-in-one script.

**Timeline**: 1-2 weeks for working MVP, 2-4 weeks for polished version.

**Budget**: $5-20/month operational cost.

This approach gets you to a **working product fastest** while keeping costs minimal and complexity low. Perfect for individual user validation before scaling up!