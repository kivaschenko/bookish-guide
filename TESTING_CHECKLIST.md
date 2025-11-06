# 🧪 Testing Checklist - Editing Server

## ✅ Server Status

### Server Started Successfully
- ✅ **URL:** http://localhost:47393
- ✅ **Port:** 47393 (configured)
- ✅ **Authentication:** Disabled (as per Erwin's choice)
- ⚠️ **Warning:** `cgi` module deprecated (non-blocking, server works)

## 🔍 Manual Testing Required

### 1. Access Interface
```
Action: Open http://localhost:47393 in browser
Expected: Timeline editing interface loads
Status: [ ] PENDING
```

### 2. Load Timeline Data
```
Action: Interface should load temp/broll_timing.json automatically
Expected: See script sentences with B-roll options
Status: [ ] PENDING
```

### 3. Select B-roll Choices
```
Action: Click on B-roll thumbnails to select for each sentence
Expected: Selection highlights, changes save
Status: [ ] PENDING
```

### 4. Upload Custom Image
```
Action: Use upload button to add custom image
Expected: Image uploads to b-roll/ressources/, appears in options
Status: [ ] PENDING
```

### 5. Preview Audio
```
Action: Click audio preview buttons
Expected: Audio plays for each phrase
Status: [ ] PENDING
```

### 6. Save Changes
```
Action: Make selections, auto-save should trigger
Expected: Changes persist in broll_timing.json
Status: [ ] PENDING
```

### 7. Test API Endpoints

**GET /api/timeline**
```bash
curl http://localhost:47393/api/timeline
# Expected: JSON with timeline data
```

**POST /api/update_timeline**
```bash
curl -X POST http://localhost:47393/api/update_timeline \
  -H "Content-Type: application/json" \
  -d '{"phrases":[...]}'
# Expected: Success response
```

## 🐛 Known Issues

### 1. Deprecation Warning (Low Priority)
**Issue:** `cgi` module deprecated in Python 3.13
**File:** `editing_server/server.py` line 20
**Impact:** None currently, but will break in future Python versions
**Fix Required:** Replace `cgi.FieldStorage` with modern form parsing

**Current Code (Line ~248):**
```python
form = cgi.FieldStorage(
    fp=self.rfile,
    headers=self.headers,
    environ={'REQUEST_METHOD': 'POST'}
)
```

**Recommended Fix:**
```python
from email import message_from_bytes
import io

# Parse multipart form data
content_length = int(self.headers.get('Content-Length', 0))
body = self.rfile.read(content_length)

# Use email parser for multipart/form-data
# Or use third-party library like python-multipart
```

### 2. French Language in Console Output
**Issue:** Console messages in French
**File:** `editing_server/server.py` lines with print statements
**Impact:** Minor UX issue for non-French speakers
**Fix Required:** Translate console output to English

**Examples to translate:**
- "Serveur de prémontage démarré" → "Timeline editing server started"
- "Authentification: DÉSACTIVÉE" → "Authentication: DISABLED"
- "Interface d'édition de timeline ouverte" → "Timeline editing interface opened"

### 3. Unused Imports
**Issue:** Several imports not used
**File:** `editing_server/server.py`
**Imports to remove:**
- `os` (if not used elsewhere)
- `shutil` (if not used)
- `webbrowser` (if not used)
- `parse_qs`, `urlparse` (if not used)

## 📊 Current File Structure

```
temp/
├── broll_timing.json         ← Timeline being edited ✅
├── broll_timing_backup.json  ← Backup ✅
└── examples/                  ← Sample files
    ├── project 8 broll_timing.json
    ├── project 9 broll_timing.json
    └── project 10 broll_timing.json

b-roll/
├── *.mp4                      ← Video files ✅
├── *.jpg                      ← Thumbnails ✅
├── *.txt                      ← Descriptions ✅
└── ressources/                ← Custom uploads ✅
```

## 🎯 Next Steps

### Immediate (This Session)
1. [ ] Open interface in browser and verify it works
2. [ ] Test basic functionality (load, select, save)
3. [ ] Document any bugs found
4. [ ] If working: Move to Task #2 (Script Generation)

### Short Term (This Week)
1. [ ] Fix deprecation warning (replace cgi module)
2. [ ] Translate French messages to English
3. [ ] Remove unused imports
4. [ ] Add error handling improvements

### Medium Term (Next Week)
1. [ ] Add unit tests
2. [ ] Add integration tests
3. [ ] Performance optimization
4. [ ] Enhanced error messages

## 🚀 If Tests Pass → Move to Script Generation

Once editing server is confirmed working, focus shifts to:

### Task #2: Improve Claude Script Generation

**Files to Review:**
- `script_and_voice/module_script_and_voice.py`
- `script_and_voice/ai_client_interface.py`
- `script_and_voice/paraphraser.py`

**Questions for Erwin:**
1. What's wrong with current scripts?
2. What improvements are needed?
3. Example of good vs bad output?

**Potential Improvements:**
- Better Claude prompts
- Script templates (intro/body/outro)
- Quality validation
- Easier iteration/re-generation
- Better structure for YouTube content

---

**Current Status:** Server running, ready for manual testing
**Next Action:** Open http://localhost:47393 and test interface
**Timeline:** If tests pass → Move to script generation improvements today
