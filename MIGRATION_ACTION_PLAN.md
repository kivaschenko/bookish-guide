# 🎯 Legacy Code Migration Complete - Action Plan

## ✅ Completed Tasks

### 1. Directory Structure Migration
- ✅ Created `editing_server/` directory
- ✅ Copied legacy premontage server files to `editing_server/`
- ✅ Moved b-roll examples to `b-roll/` directory
- ✅ Moved broll_timing.json examples to `temp/examples/`
- ✅ Removed unused `backend/` and `frontend/` directories

### 2. Code Cleanup
- ✅ Updated import paths in `editing_server/server.py`
- ✅ Renamed `PremontageHandler` → `TimelineEditingHandler`
- ✅ Updated comments from French to English
- ✅ Fixed config.yml path resolution
- ✅ Created `editing_server/README.md` documentation

### 3. Files Migrated
```
Legacy Location → New Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
legacy_code_and_examples/premontage/server.py 
  → editing_server/server.py ✅

legacy_code_and_examples/premontage/interface.html 
  → editing_server/interface.html ✅

legacy_code_and_examples/b-roll-examples/
  → b-roll/*.mp4, *.jpg, *.txt ✅

legacy_code_and_examples/broll_timing.json examples/
  → temp/examples/*.json ✅
```

## 🔧 Next Steps

### Priority 1: Make Editing Server Fully Functional

#### A. Fix Dependencies Issue
The server uses deprecated `cgi` module. Need to update to modern form parsing.

**File to update:** `editing_server/server.py`
**Lines affected:** ~248-260 (upload handling)

**Solution:**
```python
# Replace cgi.FieldStorage with modern approach
from email.parser import BytesParser
from email import message_from_bytes

# In _handle_upload method, replace:
form = cgi.FieldStorage(...)

# With:
content_type = self.headers.get('Content-Type', '')
if 'multipart/form-data' in content_type:
    # Parse multipart data properly
    ...
```

#### B. Test the Server
```bash
# 1. Create test broll_timing.json
cp "temp/examples/project 9 broll_timing.json" temp/broll_timing.json

# 2. Start server
python3 editing_server/server.py

# 3. Access in browser
http://localhost:47393

# 4. Test features:
   - Load timeline ✓
   - Pick B-roll choices ✓
   - Upload custom image ✓
   - Save changes ✓
```

#### C. Create Startup Script
**File:** `start_editing_server.sh`
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 editing_server/server.py
```

### Priority 2: Improve Claude Script Generation

Based on Erwin's request to "improve Claude script generation", we need to:

#### A. Review Current Script Generation
**Location:** `script_and_voice/`
**Files to audit:**
- `module_script_and_voice.py` - Main script generation logic
- `ai_client_interface.py` - Claude API integration
- `paraphraser.py` - Text processing

#### B. Identify Improvements Needed
**Questions to clarify with Erwin:**
1. What's wrong with current script generation?
   - Quality issues?
   - Structure problems?
   - Language/tone issues?
   - Length problems?

2. What should be improved?
   - Better outlines?
   - More engaging hooks?
   - Better paragraph structure?
   - Improved call-to-actions?

3. Current workflow issues?
   - Too slow?
   - Too many iterations?
   - Manual editing needed?

#### C. Potential Improvements (Pending Clarification)
1. **Better Prompts:** Optimize Claude prompts for YouTube content
2. **Template System:** Add video script templates (intro/body/outro)
3. **Quality Checks:** Automated validation of script structure
4. **Iteration Support:** Easy re-generation of specific sections
5. **Multi-Language:** Better support for 10+ languages (future)

### Priority 3: Documentation

#### A. Create User Guide
**File:** `WORKFLOW_GUIDE.md`
```markdown
# StoryForge Video Production Workflow

## For Erwin (Admin)
1. Create new project
2. Generate script & audio
3. Run B-roll selection
4. Assign to assistant
5. Review final timeline
6. Assemble video

## For Assistant (Editor)
1. Receive project assignment
2. Open editing server
3. Review script sentences
4. Pick best B-roll for each
5. Upload custom images if needed
6. Save timeline
```

#### B. Create Testing Guide
**File:** `TESTING.md`
- How to test editing server
- How to test script generation
- How to test full pipeline
- Sample projects for testing

## 📊 Current Project Structure

```
storyforge/
├── editing_server/          ← NEW! Timeline editing interface
│   ├── server.py           ← Cleaned up legacy server
│   ├── interface.html      ← Visual timeline editor
│   └── README.md           ← Documentation
│
├── script_and_voice/        ← Script generation (needs improvement)
│   ├── module_script_and_voice.py
│   ├── ai_client_interface.py
│   └── paraphraser.py
│
├── b_roll/                  ← B-roll matching logic
│   ├── broll_finder.py
│   ├── vector_matcher.py
│   └── meta_extractor.py
│
├── b-roll/                  ← B-roll video files
│   ├── *.mp4               ← Video files (from legacy)
│   ├── *.jpg               ← Thumbnails (from legacy)
│   ├── *.txt               ← Descriptions (from legacy)
│   └── ressources/         ← Custom uploaded images
│
├── projects/                ← Project files
│   └── {project_name}/
│       ├── input.txt
│       └── {language}/
│           └── audio/
│
├── temp/                    ← Temporary files
│   ├── broll_timing.json   ← Current timeline
│   └── examples/           ← Sample timelines
│
├── legacy_code_and_examples/  ← Keep for reference (don't delete)
│
├── simple_video_assembler.py ← Final video assembly
├── config.yml              ← Configuration
└── requirements.txt        ← Dependencies
```

## 🚀 Quick Start Commands

### Start Editing Server
```bash
python3 editing_server/server.py
# Access: http://localhost:47393
```

### Generate Script & Audio (Example)
```bash
cd script_and_voice/
python3 module_script_and_voice.py --project test-video-01 --language english
```

### Run B-roll Selection (Example)
```bash
cd b_roll/
python3 cli.py prepare-vectors --project test-video-01
```

### Assemble Final Video (Example)
```bash
python3 simple_video_assembler.py --project test-video-01 --language english
```

## 📝 Immediate Action Items

### This Week (Ultra-Minimal Approach)

**Tuesday (Today):**
1. ✅ Migration complete
2. ⏳ Fix `cgi` deprecation warning
3. ⏳ Test editing server with sample data
4. ⏳ Document any bugs found

**Wednesday:**
1. ⏳ Review script generation code
2. ⏳ Identify specific improvement areas
3. ⏳ Discuss with Erwin what needs improvement
4. ⏳ Create improvement plan

**Thursday:**
1. ⏳ Implement script generation improvements
2. ⏳ Test end-to-end workflow
3. ⏳ Fix any blocking issues

**Friday:**
1. ⏳ Final testing
2. ⏳ Create user documentation
3. ⏳ Ready for first video production!

## 🎯 Success Criteria

### Editing Server Works When:
- ✓ Server starts without errors
- ✓ Interface loads in browser
- ✓ Can load broll_timing.json
- ✓ Can select B-roll choices
- ✓ Can upload custom images
- ✓ Changes save correctly
- ✓ Preview works

### Script Generation Works When:
- ✓ Generates engaging YouTube scripts
- ✓ Proper structure (intro/body/outro)
- ✓ Appropriate length (8-12 minutes)
- ✓ Natural language flow
- ✓ Includes hooks and CTAs
- ✓ Minimal manual editing needed

### Full Pipeline Works When:
- ✓ Input text → Script (Claude)
- ✓ Script → Audio (Gemini TTS)
- ✓ Audio → B-roll selection (Vector DB + LLM)
- ✓ B-rolls → Timeline editing (Visual interface)
- ✓ Timeline → Final video (MoviePy)
- ✓ Total time: <2 hours per video

## 💰 Development Cost Estimate

### Migration Work (Completed)
- Directory restructuring: 1 hour
- Code cleanup: 1 hour
- Documentation: 0.5 hours
**Total: 2.5 hours** ✅

### Remaining Work (This Week)
- Fix editing server issues: 2-4 hours
- Script generation improvements: 4-6 hours  
- Testing & documentation: 2-3 hours
**Total: 8-13 hours**

### Grand Total: ~15 hours maximum
**At €100-200 budget: Very achievable!** 🎉

## 📞 Questions for Erwin

### About Editing Server:
1. Does the current interface.html look good?
2. Any specific features needed?
3. Should we keep authentication or remove it?

### About Script Generation:
1. What specific problems with current scripts?
2. Example of good vs. bad script?
3. What's the target video length?
4. Any specific content structure needed?

### About Workflow:
1. How many videos per week target?
2. Who will be the assistant?
3. When to start production?

---

**Status:** Migration Complete, Ready for Testing & Improvements
**Next Step:** Test editing server + Clarify script improvement needs
**Timeline:** Ready for first video by Friday (Nov 8, 2025)
