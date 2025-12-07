# Message Rendering Logic Simplification Analysis

## Current State

### Functions Involved:
1. `render_styled_bubble(text, speaker)` - Static message bubbles
2. `render_streaming_bubble(speaker)` - Initial streaming bubble placeholder
3. `update_streaming_bubble(container, text, speaker, show_cursor)` - Update streaming bubble
4. `render_message_history(messages)` - Render all messages with controls
5. Helper functions: `_get_bubble_style_attrs()`, `_get_bubble_base_style()`, `_get_bubble_css()`

## Code Duplication Identified

### 1. **HTML Escaping** (Repeated in 2 places)
- `render_styled_bubble()`: Line 294
- `update_streaming_bubble()`: Line 364
- **Solution**: Extract to `_escape_html(text: str) -> str` helper

### 2. **Bubble HTML Template** (Repeated in 3 places)
- All three functions build similar HTML structure:
  ```html
  <div class="message-bubble-enhanced {bubble_class}" style="{base_style}">
      <div style="position: relative; z-index: 1;">
          {content}
      </div>
  </div>
  <style>
      .message-bubble-enhanced.{bubble_class}::after {{
          {after_style}
      }}
  </style>
  ```
- **Solution**: Extract to `_build_bubble_html(content, speaker, is_streaming=False, show_cursor=False) -> str`

### 3. **After Style Generation** (Repeated in 3 places)
- All three functions generate: `f"background: {attrs['bg_gradient']}; background-color: {attrs['bg_fallback']};"`
- **Solution**: Extract to `_get_bubble_after_style(attrs) -> str` helper

### 4. **TTS Logic in `render_message_history()`** (Lines 771-801)
- Inline TTS generation logic could be extracted
- **Solution**: Extract to `_handle_message_audio(message, message_idx, speaker_key) -> None`

### 5. **Column Layout Repetition**
- Header columns, action columns repeated
- **Solution**: Use helper or simplify layout

## Proposed Simplifications

### Phase 1: Extract Common Helpers (Low Risk)

```python
def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

def _get_bubble_after_style(attrs: Dict[str, str]) -> str:
    """Get CSS for ::after pseudo-element background."""
    return f"background: {attrs['bg_gradient']}; background-color: {attrs['bg_fallback']};"

def _build_bubble_html(
    content: str, 
    speaker: str, 
    is_streaming: bool = False, 
    show_cursor: bool = False
) -> str:
    """Build complete bubble HTML with styles."""
    attrs = _get_bubble_style_attrs(speaker)
    base_style = _get_bubble_base_style(attrs)
    if is_streaming:
        base_style = base_style.replace("transition:", "min-height: 40px;\n            transition:")
    
    cursor_html = '<span class="streaming-cursor">|</span>' if show_cursor else ''
    after_style = _get_bubble_after_style(attrs)
    streaming_class = " streaming-bubble" if is_streaming else ""
    
    return f"""
        <div class="message-bubble-enhanced {attrs['bubble_class']}{streaming_class}" style="{base_style}">
            <div style="position: relative; z-index: 1;">
                {content}{cursor_html}
            </div>
        </div>
        <style>
            .message-bubble-enhanced.{attrs['bubble_class']}::after {{
                {after_style}
            }}
        </style>
    """
```

### Phase 2: Simplify Bubble Rendering Functions

```python
def render_styled_bubble(text: str, speaker: str) -> None:
    """Render a static message bubble."""
    html_text = _escape_html(text)
    bubble_html = _build_bubble_html(html_text, speaker, is_streaming=False)
    st.markdown(bubble_html, unsafe_allow_html=True)

def render_streaming_bubble(speaker: str) -> st.empty:
    """Create initial streaming bubble placeholder."""
    bubble_container = st.empty()
    bubble_html = _build_bubble_html("", speaker, is_streaming=True, show_cursor=True)
    bubble_container.markdown(bubble_html, unsafe_allow_html=True)
    return bubble_container

def update_streaming_bubble(container: st.empty, text: str, speaker: str, show_cursor: bool = True) -> None:
    """Update streaming bubble with new content."""
    html_text = _escape_html(text)
    bubble_html = _build_bubble_html(html_text, speaker, is_streaming=True, show_cursor=show_cursor)
    container.markdown(bubble_html, unsafe_allow_html=True)
```

### Phase 3: Extract TTS Logic (Medium Risk)

```python
def _handle_message_audio(message: Dict[str, Any], message_idx: int, speaker_key: str) -> None:
    """Handle TTS generation and playback for a message."""
    message_id = f"msg_{message_idx}"
    button_key = f"audio_btn_{message_id}"
    play_state_key = f"play_state_{message_id}"
    
    # Initialize play state
    if play_state_key not in st.session_state:
        st.session_state[play_state_key] = False
    
    # Audio button
    if st.button(":material/volume_up:", key=button_key, help="Generate and play audio"):
        if not message.get("audio_bytes"):
            try:
                voice = VOICE_FOR_SPEAKER.get(speaker_key, "alloy")
                audio_bytes = tts_stream_to_bytes(message["content"], voice=voice)
                st.session_state.show_messages[message_idx]["audio_bytes"] = audio_bytes
                st.toast("Audio generated!", icon=":material/volume_up:")
            except Exception as e:
                logger.error(f"TTS generation failed: {e}", exc_info=True)
                st.error(f"Failed to generate audio: {str(e)}", icon=":material/error:")
        
        st.session_state[play_state_key] = True
        st.rerun()
    
    # Audio player
    should_play = st.session_state.get(play_state_key, False)
    if message.get("audio_bytes") and should_play:
        st.audio(message["audio_bytes"], format="audio/mp3", autoplay=True)
        st.session_state[play_state_key] = False
```

## Expected Benefits

### Code Reduction:
- **Before**: ~150 lines across bubble rendering functions
- **After**: ~80 lines (47% reduction)
- **Maintainability**: Single source of truth for bubble HTML structure
- **Consistency**: All bubbles use same template

### Risk Assessment:
- **Phase 1**: ✅ Low risk - Pure extraction, no logic changes
- **Phase 2**: ✅ Low risk - Same output, cleaner code
- **Phase 3**: ⚠️ Medium risk - TTS logic extraction, needs testing

## UX Preservation Checklist

- ✅ Bubble styling remains identical
- ✅ Streaming animation unchanged
- ✅ Audio functionality preserved
- ✅ Message layout unchanged
- ✅ All speaker colors maintained
- ✅ Hover effects preserved

## Recommendation

**Start with Phase 1 & 2** - These are low-risk refactorings that significantly reduce duplication without changing behavior. Phase 3 can be done separately if needed.

