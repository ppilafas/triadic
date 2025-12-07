# `utils/streamlit_ui.py` Distribution Assessment

## Current State

**File Size:** 800 lines  
**Primary Purpose:** Streamlit-specific UI helpers, styling, and settings management

## Analysis by Category

### 1. **DUPLICATE FUNCTIONS** (Should be removed)

#### `render_text_input()` (lines 690-741)
- **Status:** ❌ DUPLICATE
- **Exists in:** `utils/streamlit_chat_input.py` (lines 18-70)
- **Action:** Remove from `streamlit_ui.py`
- **Impact:** Low - `streamlit_chat_input.py` version is more complete and actively used

#### `render_voice_input()` (lines 744-787)
- **Status:** ❌ DUPLICATE
- **Exists in:** `utils/streamlit_chat_input.py` (lines 112-156)
- **Action:** Remove from `streamlit_ui.py`
- **Impact:** Low - `streamlit_chat_input.py` version is more complete and actively used

#### `render_topic_suggestions()` (lines 645-687)
- **Status:** ⚠️ POTENTIALLY LEGACY
- **Exists in:** `utils/streamlit_topics.py` (dialog-based, different implementation)
- **Action:** Check if still used, if not remove
- **Impact:** Medium - May be legacy code from before dialog implementation

#### `render_generate_topics_button()` (lines 630-642)
- **Status:** ⚠️ POTENTIALLY LEGACY
- **Action:** Check if still used, if not remove
- **Impact:** Low - Simple button, likely replaced by dialog

---

### 2. **AVATAR FUNCTIONS** (Should stay or move to dedicated module)

#### `_load_avatar_image()` (lines 33-66)
#### `_encode_avatar_data_uri()` (lines 69-84)
#### `get_avatar_path()` (lines 87-135)
- **Status:** ✅ Well-organized, heavily used
- **Used by:** `streamlit_messages.py`, `streamlit_bubbles.py`, `streamlit_irc.py`, `turn_renderer.py`
- **Recommendation:** 
  - **Option A:** Keep in `streamlit_ui.py` (current location is fine)
  - **Option B:** Move to `utils/streamlit_avatars.py` (if we want stricter separation)
- **Impact:** Low - Well-encapsulated, clear purpose

---

### 3. **AUDIO FUNCTIONS** (Should move to dedicated module)

#### `autoplay_audio()` (lines 198-212)
#### `transcribe_streamlit_audio()` (lines 215-246)
- **Status:** ⚠️ Should be in dedicated audio module
- **Used by:** `streamlit_chat_input.py`, `turn_renderer.py`
- **Recommendation:** Move to `utils/streamlit_audio.py`
- **Rationale:** Audio functions are a distinct concern, should be separated
- **Impact:** Medium - Improves organization, reduces coupling

---

### 4. **BANNER FUNCTIONS** (Should move to dedicated module)

#### `_load_banner_image()` (lines 476-494)
#### `_encode_banner_data_uri()` (lines 497-509)
#### `render_app_banner()` (lines 512-623)
#### `render_broadcast_banner()` (lines 251-285)
- **Status:** ⚠️ Should be in dedicated banner module
- **Used by:** `app.py` (likely)
- **Recommendation:** Move to `utils/streamlit_banners.py`
- **Rationale:** Banner rendering is a distinct UI concern
- **Impact:** Low - Self-contained, minimal dependencies

---

### 5. **SETTINGS FUNCTIONS** (Should move to session module)

#### `_validate_settings()` (lines 290-322)
#### `get_settings()` (lines 325-361)
- **Status:** ⚠️ Should be in session/settings module
- **Used by:** `turn_executor.py`, `pages/1_⚙️_Settings.py`
- **Recommendation:** Move to `utils/streamlit_session.py` or create `utils/streamlit_settings.py`
- **Rationale:** Settings management is session-related, not general UI
- **Impact:** Medium - Better organization, aligns with session state management

---

### 6. **TOPIC FUNCTIONS** (Should move to topic module)

#### `_get_current_topic()` (lines 376-399)
#### `render_top_controls()` (lines 402-471)
- **Status:** ⚠️ Should be in topic/topics module
- **Used by:** Unknown (may be legacy)
- **Recommendation:** 
  - If `render_top_controls()` is still used, move to `utils/streamlit_topics.py` or `utils/topic_handler.py`
  - If not used, remove
- **Impact:** Low - Check usage first

---

### 7. **CONSTANTS** (Should stay or move to constants module)

#### `SPEAKER_INFO` (lines 140-180)
- **Status:** ✅ Heavily used, central constant
- **Used by:** `streamlit_messages.py`, `streamlit_bubbles.py`, `streamlit_irc.py`, `turn_executor.py`, `turn_renderer.py`
- **Recommendation:** 
  - **Option A:** Keep in `streamlit_ui.py` (current location is fine)
  - **Option B:** Move to `utils/streamlit_constants.py` (if we want stricter separation)
- **Impact:** Low - Well-established, many dependencies

#### `VOICE_FOR_SPEAKER` (line 183)
- **Status:** ✅ Simple constant
- **Used by:** `streamlit_messages.py`, `turn_renderer.py`
- **Recommendation:** Same as `SPEAKER_INFO`
- **Impact:** Low

---

## Recommended Distribution Plan

### Phase 1: Remove Duplicates (Low Risk, High Value)
1. ✅ Remove `render_text_input()` from `streamlit_ui.py`
2. ✅ Remove `render_voice_input()` from `streamlit_ui.py`
3. ⚠️ Check usage of `render_topic_suggestions()` and `render_generate_topics_button()`, remove if unused

**Estimated Reduction:** ~150 lines

### Phase 2: Create Dedicated Modules (Medium Risk, Medium Value)
1. ✅ Create `utils/streamlit_audio.py` and move audio functions
2. ✅ Create `utils/streamlit_banners.py` and move banner functions
3. ✅ Move settings functions to `utils/streamlit_session.py` or create `utils/streamlit_settings.py`

**Estimated Reduction:** ~250 lines

### Phase 3: Topic Functions Cleanup (Low Risk, Low Value)
1. ⚠️ Check if `render_top_controls()` and `_get_current_topic()` are used
2. ✅ If used, move to `utils/streamlit_topics.py` or `utils/topic_handler.py`
3. ✅ If unused, remove

**Estimated Reduction:** ~100 lines

### Phase 4: Constants Organization (Optional, Low Priority)
1. ⚠️ Consider moving `SPEAKER_INFO` and `VOICE_FOR_SPEAKER` to `utils/streamlit_constants.py`
2. ⚠️ Update all imports (many files affected)

**Estimated Reduction:** ~50 lines (but many import updates needed)

---

## Final Size Estimate

**Current:** 800 lines  
**After Phase 1:** ~650 lines  
**After Phase 2:** ~400 lines  
**After Phase 3:** ~300 lines  
**After Phase 4:** ~250 lines (if constants moved)

---

## Priority Recommendations

### High Priority (Do First)
1. ✅ Remove duplicate `render_text_input()` and `render_voice_input()`
2. ✅ Check and remove unused topic functions

### Medium Priority (Do Next)
1. ✅ Create `utils/streamlit_audio.py` and move audio functions
2. ✅ Create `utils/streamlit_banners.py` and move banner functions
3. ✅ Move settings functions to `utils/streamlit_session.py`

### Low Priority (Optional)
1. ⚠️ Move constants to dedicated module (many import updates)
2. ⚠️ Move avatar functions to dedicated module (if desired)

---

## Dependencies to Update

After moving functions, update imports in:
- `app.py`
- `utils/streamlit_messages.py`
- `utils/streamlit_chat_input.py`
- `utils/streamlit_bubbles.py`
- `utils/streamlit_irc.py`
- `services/turn_executor.py`
- `services/turn_renderer.py`
- `pages/1_⚙️_Settings.py`

