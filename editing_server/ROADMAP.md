# 🗺️ ROADMAP: Editing Server Improvements for Erwin

## **Philosophy: Keep It Simple, Stupid (KISS)**

**Goal**: Make the existing `editing_server/` work reliably with minimal changes, then integrate with dashboard.

---

## **Phase 1: VERIFY & FIX (Priority: CRITICAL)**
*Goal: Make it work standalone with real data*

### ✅ **Task 1.1: Validate JSON Format Compatibility**
**Problem**: Need to ensure server handles Erwin's actual JSON format
- **Action**: Test with real `broll_timing.json` from Erwin
- **Files**: `editing_server/server.py` (lines 150-210 - format detection)
- **Expected**: Array format `[{...}, {...}]` should work
- **Edge Case**: Handle missing fields gracefully (`broll2`, `broll3`, `image`)
- **Estimate**: 30 min

### ✅ **Task 1.2: Fix Path Resolution**
**Problem**: Server may not find files in project structure
- **Action**: 
  - Verify `projects/<name>/temp/broll_timing.json` path works
  - Verify `projects/<name>/temp/audio/bullet01.mp3` paths work
  - Verify `b-roll/<video>.mp4` paths work
- **Files**: `editing_server/server.py` (lines 364-400 - file serving)
- **Test**: Use one of Erwin's real projects
- **Estimate**: 45 min

### ✅ **Task 1.3: Audio Preview Path Fix**
**Problem**: Interface expects specific audio path structure
- **Action**: Verify audio path generation in interface.html (line ~360)
  ```javascript
  const audioPath = '/projects/' + projectName + '/temp/audio/bullet' + bulletNum + '.mp3';
  ```
- **Files**: `editing_server/interface.html` (lines 350-370)
- **Test**: Play audio for bullet01.mp3, bullet02.mp3
- **Estimate**: 20 min

### ✅ **Task 1.4: Error Handling & Logging**
**Problem**: Need better error messages for debugging
- **Action**: Add detailed logging for:
  - Missing files (JSON, audio, video, images)
  - Invalid JSON format
  - Permission errors
- **Files**: `editing_server/server.py` (throughout)
- **Benefit**: Faster troubleshooting
- **Estimate**: 30 min

---

## **Phase 2: DATA VALIDATION (Priority: HIGH)**
*Goal: Ensure data integrity and user feedback*

### ✅ **Task 2.1: Validate Required Fields**
**Problem**: Prevent crashes from incomplete data
- **Action**: Check each timeline entry has:
  - `rush`, `phrase`, `audio_file`
  - At least one B-roll (`broll`)
  - Valid `start_time`, `end_time`
- **Files**: `editing_server/server.py` (add validation function)
- **UI**: Show warning in interface if data incomplete
- **Estimate**: 45 min

### ✅ **Task 2.2: Handle Missing B-roll Files**
**Problem**: Server crashes if video file doesn't exist
- **Action**: 
  - Check if file exists before serving
  - Show placeholder image with error message
  - Log missing files clearly
- **Files**: `editing_server/server.py` (lines 440-470)
- **Estimate**: 30 min

### ✅ **Task 2.3: Validate Audio Files Exist**
**Problem**: Audio preview fails silently
- **Action**: 
  - Pre-check audio files on timeline load
  - Show indicator for missing audio files
  - Provide helpful error message
- **Files**: `editing_server/interface.html` (add validation on load)
- **Estimate**: 30 min

---

## **Phase 3: USABILITY IMPROVEMENTS (Priority: MEDIUM)**
*Goal: Match Erwin's workflow expectations*

### ✅ **Task 3.1: Improve Visual Feedback**
**Problem**: User needs clear indication of current state
- **Action**:
  - Highlight currently selected B-roll more clearly
  - Show save status (auto-saved at HH:MM:SS)
  - Add loading spinner during operations
- **Files**: `editing_server/interface.html` (CSS + JS)
- **Estimate**: 45 min

### ✅ **Task 3.2: Keyboard Shortcuts**
**Problem**: Speed up editing workflow
- **Action**: Add shortcuts:
  - `1`, `2`, `3` - Select B-roll 1/2/3
  - `Space` - Play/pause audio
  - `↑`/`↓` - Navigate bullets
  - `Delete` - Remove image overlay
- **Files**: `editing_server/interface.html` (add keydown handler)
- **Estimate**: 1 hour

### ✅ **Task 3.3: Better Duplicate Highlighting**
**Problem**: Red overlay can be confusing
- **Action**:
  - Add counter badge showing "Used X times"
  - Show WHERE else it's used (click to jump)
  - Option to "Use anyway" (confirm dialog)
- **Files**: `editing_server/interface.html` (enhance duplicate logic)
- **Estimate**: 1.5 hours

### ✅ **Task 3.4: Timeline Statistics**
**Problem**: No overview of editing progress
- **Action**: Add header showing:
  - Total sentences: X
  - Using alternative B-rolls: Y
  - Image overlays: Z
  - Duplicate warnings: W
- **Files**: `editing_server/interface.html` (add stats panel)
- **Estimate**: 45 min

---

## **Phase 4: INTEGRATION (Priority: HIGH)**
*Goal: Connect with dashboard server*

### ✅ **Task 4.1: API Module for Dashboard**
**Problem**: Dashboard needs programmatic control
- **Action**: Create `editing_server/__init__.py` with:
  ```python
  def start_editor_for_project(project_name: str, port: int = 47393):
      """Launch editing server for specific project"""
  
  def get_editing_status(project_name: str) -> dict:
      """Check if editing is complete"""
  
  def validate_timeline(project_name: str) -> dict:
      """Validate broll_timing.json completeness"""
  ```
- **Files**: `editing_server/__init__.py`
- **Estimate**: 1 hour

### ✅ **Task 4.2: Dashboard Launch Button**
**Problem**: Need easy way to open editor from dashboard
- **Action**: Dashboard should:
  - Show "Edit Timeline" button per project
  - Start editing_server if not running
  - Open browser to editing interface
- **Files**: Dashboard code (provided by Erwin)
- **Note**: This requires Erwin's dashboard codebase
- **Estimate**: 2 hours

### ✅ **Task 4.3: Status Callback/Webhook**
**Problem**: Dashboard doesn't know when editing is done
- **Action**: Add optional webhook:
  - POST to dashboard when timeline modified
  - Send validation results
  - Update project status
- **Files**: `editing_server/server.py` (add webhook config)
- **Estimate**: 1 hour

---

## **Phase 5: ROBUSTNESS (Priority: MEDIUM)**
*Goal: Handle edge cases and errors gracefully*

### ✅ **Task 5.1: Concurrent Access Protection**
**Problem**: Multiple users editing same project
- **Action**:
  - Add file locking mechanism
  - Show "Read-only" mode if locked
  - Warn if external changes detected
- **Files**: `editing_server/server.py` (file locking)
- **Estimate**: 1.5 hours

### ✅ **Task 5.2: Backup Before Save**
**Problem**: Risk of data corruption
- **Action**:
  - Auto-backup to `broll_timing.json.backup`
  - Keep last 5 backups with timestamps
  - Add "Restore backup" function
- **Files**: `editing_server/server.py` (backup logic)
- **Estimate**: 45 min

### ✅ **Task 5.3: Configuration Validation**
**Problem**: Server fails silently with bad config
- **Action**:
  - Validate config.yml on startup
  - Show helpful error messages
  - Provide config examples
- **Files**: `editing_server/server.py` (config validation)
- **Estimate**: 30 min

---

## **Phase 6: POLISH (Priority: LOW)**
*Goal: Professional finishing touches*

### ✅ **Task 6.1: Internationalization (i18n)**
**Problem**: Interface currently in French
- **Action**:
  - Extract all UI strings
  - Create English version (priority)
  - Support config-based language selection
- **Files**: `editing_server/interface.html` (full review)
- **Estimate**: 2 hours

### ✅ **Task 6.2: Mobile Responsive Design**
**Problem**: May need to edit on tablet
- **Action**:
  - Test on tablet/mobile
  - Adjust layout for smaller screens
  - Touch-friendly controls
- **Files**: `editing_server/interface.html` (CSS media queries)
- **Estimate**: 2 hours

### ✅ **Task 6.3: Performance Optimization**
**Problem**: Large projects may be slow
- **Action**:
  - Lazy load video thumbnails
  - Paginate timeline (50 items per page)
  - Cache file existence checks
- **Files**: `editing_server/server.py` + `interface.html`
- **Estimate**: 2 hours

---

## **ESTIMATED TIMELINE**

| Phase | Tasks | Hours | Priority |
|-------|-------|-------|----------|
| Phase 1: Verify & Fix | 4 | 2.0h | 🔴 CRITICAL |
| Phase 2: Validation | 3 | 1.75h | 🟠 HIGH |
| Phase 3: Usability | 4 | 4.25h | 🟡 MEDIUM |
| Phase 4: Integration | 3 | 4h | 🟠 HIGH |
| Phase 5: Robustness | 3 | 2.75h | 🟡 MEDIUM |
| Phase 6: Polish | 3 | 6h | 🟢 LOW |
| **TOTAL** | **20 tasks** | **~21h** | |

---

## **EXECUTION ORDER (Recommended)**

### **Sprint 1: Make It Work (MUST DO)**
1. Phase 1 (all tasks) - Get server running
2. Phase 2 (all tasks) - Ensure data integrity
3. Test with real Erwin data

**Deliverable**: Working editor with one real project
**Time**: ~4 hours

### **Sprint 2: Make It Better (SHOULD DO)**
1. Phase 3.1, 3.2 (feedback + shortcuts)
2. Phase 4.1 (API for dashboard)
3. Phase 5.2 (backups)

**Deliverable**: Professional editor ready for daily use
**Time**: ~3 hours

### **Sprint 3: Integration (WHEN DASHBOARD READY)**
1. Phase 4.2, 4.3 (dashboard integration)
2. Test full workflow

**Deliverable**: Seamless dashboard → editor flow
**Time**: ~3 hours

### **Sprint 4: Polish (IF TIME/BUDGET)**
1. Phase 3.3, 3.4 (advanced features)
2. Phase 5.1, 5.3 (robustness)
3. Phase 6.1 (English translation - important!)

**Deliverable**: Production-ready system
**Time**: ~7 hours

---

## **TESTING CHECKLIST**

### **Before Starting Development**
- [X] Get Erwin's dashboard codebase
- [X] Get 200+ B-roll videos with .txt metadata
- [X] Get 1 complete project with all files:
  - `broll_timing.json` (finished)
  - Audio files (`bullet01.mp3`, etc.)
  - Script and metadata
- [X] Verify current Python environment

### **After Each Phase**
- [ ] Test with real project data
- [ ] Check all file paths resolve correctly
- [ ] Verify JSON saves correctly
- [ ] Test in Chrome, Firefox, Safari
- [ ] Run without errors for 30 minutes

### **Before Delivery**
- [ ] Full workflow test (load → edit → save → verify)
- [ ] Dashboard integration test (if applicable)
- [ ] Stress test with large project (200+ sentences)
- [ ] Document any known limitations
- [ ] Update README.md with changes

---

## **RISK MITIGATION**

### **Risk 1: Erwin's Data Format Different**
- **Mitigation**: Request sample files FIRST (already planned)
- **Fallback**: Write format converter script

### **Risk 2: Dashboard Integration Complex**
- **Mitigation**: Keep editor standalone-functional
- **Fallback**: Simple "Open in Browser" button

### **Risk 3: Performance Issues**
- **Mitigation**: Test with large project early
- **Fallback**: Implement pagination (Phase 6.3)

### **Risk 4: Scope Creep**
- **Mitigation**: Stick to roadmap, document "future features"
- **Fallback**: Focus on Sprint 1 + 2 only

---

## **SUCCESS CRITERIA**

✅ **Minimum Viable Product (MVP)**
- Erwin can load his projects
- Erwin can select B-rolls and add images
- Changes save correctly
- Audio preview works
- No crashes or data loss

✅ **Production Ready**
- All MVP features +
- Dashboard integration working
- English translation
- Good error messages
- Backup system

✅ **Delightful**
- All above +
- Keyboard shortcuts
- Smart duplicate detection
- Progress statistics
- Fast and responsive

---

## **NOTES FOR IMPLEMENTATION**

1. **Code Style**: Follow existing patterns in `server.py`
2. **Testing**: Manual testing with real data (no unit tests for prototype)
3. **Documentation**: Update README.md after each phase
4. **Version Control**: Commit after each task completion
5. **Communication**: Screenshot + brief status update to Erwin after each sprint

---

## **DECISION LOG**

| Decision | Rationale |
|----------|-----------|
| Keep separate editing_server | Faster than refactoring into dashboard |
| Use existing HTML interface | Already 90% complete, just needs fixes |
| No database, just JSON | Simple, fits Erwin's local workflow |
| HTTP Basic Auth | Simple, sufficient for local/small team |
| No WebSocket initially | HTTP polling simpler, add later if needed |
| English translation priority | Erwin is English speaker, videos in English |

---

**This roadmap prioritizes getting Erwin productive FAST (Sprint 1+2 = 7 hours) while maintaining flexibility for future improvements.**
