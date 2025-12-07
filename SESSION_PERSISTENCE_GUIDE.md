# Session State Persistence Guide

## Overview

The application now supports persisting session state across browser refreshes. This means your conversation history, settings, and other important state will be restored when you refresh the page.

## How It Works

### Storage Location

Session state is persisted to a JSON file:
- **Location**: `.streamlit/persisted_state/session_state.json`
- **Format**: JSON with human-readable formatting

### What Gets Persisted

**Persisted State:**
- ✅ Conversation history (`show_messages`)
- ✅ Speaker rotation (`next_speaker`)
- ✅ Turn metrics (`total_turns`, `last_latency`)
- ✅ All settings (TTS, auto-mode, model selection, etc.)
- ✅ Knowledge base data (`vector_store_id`, `uploaded_file_index`)
- ✅ Topic suggestions (`topic_suggestions`)

**Excluded State (Temporary/Internal):**
- ❌ Internal flags (`_manual_next`, `_auto_generate_topics`, etc.)
- ❌ Turn-in-progress flags (`turn_in_progress`)
- ❌ Widget state keys (regenerated on each run)
- ❌ Audio playback state (per-message, regenerated)
- ❌ Dialog open/close flags

### Auto-Save Triggers

State is automatically saved after:
1. **Turn completion** - After each AI response
2. **Topic generation** - After topics are auto-generated
3. **Topic selection** - After selecting a discussion topic
4. **Settings changes** - When viewing the Settings page

### Manual Control

You can also manually control persistence:

```python
from utils.streamlit_persistence import (
    save_session_state,      # Save current state
    load_session_state,       # Load saved state
    restore_session_state,    # Restore to session state
    clear_persisted_state     # Clear saved state
)
```

## Usage

### Automatic Restoration

State is automatically restored when the app starts. No action required!

### Clearing Persisted State

To clear persisted state (start fresh):

```python
from utils.streamlit_persistence import clear_persisted_state
clear_persisted_state()
```

Or manually delete: `.streamlit/persisted_state/session_state.json`

## Technical Details

### Serialization

- Only JSON-serializable values are persisted
- Non-serializable objects (functions, file handles) are skipped
- Complex objects (dicts, lists) are preserved

### State Merging

On app startup:
- Saved state is **merged** with defaults
- Existing session state takes precedence
- Missing keys are initialized with defaults

### Performance

- Auto-save only triggers when state actually changes
- Uses hash comparison to detect changes
- Minimal performance impact

## Security Considerations

⚠️ **Important**: The persisted state file contains:
- Conversation history (may contain sensitive information)
- Settings and preferences

**Recommendations:**
- Add `.streamlit/persisted_state/` to `.gitignore` (if not already)
- Consider encrypting sensitive data if needed
- Be aware of data privacy implications

## Troubleshooting

### State Not Restoring

1. Check if `.streamlit/persisted_state/session_state.json` exists
2. Check application logs for errors
3. Verify file permissions

### State File Too Large

If the state file grows too large:
- Clear old conversation history
- Use `clear_persisted_state()` to start fresh
- Consider implementing conversation history limits

### Settings Not Persisting

- Ensure settings are updated via Streamlit widgets (not direct assignment)
- Check that settings keys are in `_PERSISTED_KEYS` set
- Verify auto-save is being called

## Future Enhancements

Potential improvements:
- [ ] Per-user state files (if multi-user support added)
- [ ] State encryption for sensitive data
- [ ] State versioning/migration
- [ ] Browser localStorage option (client-side)
- [ ] Database backend option (for production)

