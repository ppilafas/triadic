# Streamlit 1.51+ Native Material Symbols Support

## ✅ Native Support

Streamlit 1.51.0+ has **native support** for Material Symbols in various components.

### Format
```
:material/icon_name:
```
Where `icon_name` is the **snake_case** name of the Material Symbol.

## 🎯 Supported Components

### 1. **Navigation (st.navigation & st.Page)**
```python
# st.Page accepts Material Symbols in :material/icon_name: format
pages = [
    st.Page(home_page, title="Home", icon=":material/podcasts:", default=True),
    st.Page("pages/1_Settings.py", title="Settings", icon=":material/settings:"),
    st.Page("pages/2_Vector_Stores.py", title="Vector Stores", icon=":material/storage:"),
    st.Page("pages/3_Telemetry.py", title="Telemetry", icon=":material/analytics:"),
]

# Create navigation
current_page = st.navigation(pages, position="sidebar", expanded=True)
current_page.run()
```

**Important Notes:**
- ✅ Use `:material/icon_name:` format (NOT shortcodes like `"podcasts"` or `"settings"`)
- ✅ Material Symbol format works with `st.Page` icon parameter
- ❌ Shortcodes (plain text like `"podcasts"`) will throw `StreamlitAPIException`
- ❌ Emoji characters (like `"🎙️"`) also work, but Material Symbols are preferred for consistency

### 2. **Status Messages**
```python
st.info('Message', icon=":material/info:")
st.warning('Message', icon=":material/warning:")
st.error('Message', icon=":material/error:")
st.success('Message', icon=":material/check_circle:")
```

### 3. **Toast Notifications**
```python
st.toast('Message', icon=":material/check_circle:")
```

### 4. **Progress Bars**
```python
st.progress(50, text=":material/upload: Processing...")
```

### 5. **Tabs**
```python
tab1, tab2 = st.tabs([":material/memory: Brain", ":material/settings: Studio"])
```

### 6. **Chat Messages**
```python
with st.chat_message("user", avatar=":material/person:"):
    st.write("Hello")
```

### 7. **Page Config**
```python
st.set_page_config(
    page_icon=":material/podcasts:",
    ...
)
```

### 8. **Buttons** (via icon parameter if available)
```python
st.button("Play", icon=":material/play_arrow:")
```

## ❌ Known Limitations

### 1. **st.markdown() with unsafe_allow_html=True**
**Issue**: Material Symbols may NOT render correctly in `st.markdown()` when using `unsafe_allow_html=True`.

**Status**: Known bug tracked on GitHub ([#9945](https://github.com/streamlit/streamlit/issues/9945))

**Workaround**: 
- Use native Streamlit components that support `icon` parameter
- Avoid using Material Symbols in raw HTML within `st.markdown()`
- Use emojis or Unicode symbols as fallback

### 2. **Newer Material Symbols**
**Issue**: Some recently added Material Symbols may not be recognized if Streamlit's internal icon list hasn't been updated.

**Status**: Reported issue ([#9810](https://github.com/streamlit/streamlit/issues/9810))

**Workaround**: 
- Use well-established Material Symbols
- Check Streamlit release notes for icon updates
- Use emojis as fallback for newer icons

## 📋 Current Usage in Codebase

### ✅ Already Using Native Support:
- `st.navigation()` with `st.Page(..., icon=":material/icon_name:")` ✅
- `st.set_page_config(page_icon=":material/podcasts:")` ✅
- `st.progress(..., text=":material/history_edu: ...")` ✅
- `st.tabs([":material/memory: Brain", ...])` ✅
- `st.toast(..., icon=":material/broadcast_on_home:")` ✅
- `st.chat_message(..., avatar=":material/person:")` ✅
- `st.button(..., icon=":material/play_arrow:")` ✅

### ⚠️ Potential Issues:
- Material Symbols in `SPEAKER_INFO` avatars are used in `st.chat_message()` - **This is correct!** ✅
- Material Symbols in progress text - **This is correct!** ✅

## 🎨 Best Practices

1. **Use Native Components**: Prefer components with built-in `icon` parameter
2. **Avoid HTML**: Don't use Material Symbols in `st.markdown()` with `unsafe_allow_html=True`
3. **Check Availability**: Verify icon names match Material Symbols library
4. **Fallback Strategy**: Have emoji alternatives for critical UI elements
5. **Stay Updated**: Keep Streamlit updated for latest Material Symbols support

## 📚 Resources

- [Streamlit 1.51.0 Release Notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2024)
- [Material Symbols Library](https://fonts.google.com/icons)
- [Streamlit Status Components Docs](https://docs.streamlit.io/1.51.0/develop/api-reference/status/st.info)
- [GitHub Issue: Material Icons in markdown](https://github.com/streamlit/streamlit/issues/9945)

## 🔍 Finding Icon Names

1. Visit [Material Symbols Library](https://fonts.google.com/icons)
2. Search for desired icon
3. Click on icon to see details
4. Use the **snake_case** name in format `:material/icon_name:`

Example:
- Icon: "Psychology" → Name: `psychology` → Use: `:material/psychology:`
- Icon: "Smart Toy" → Name: `smart_toy` → Use: `:material/smart_toy:`
- Icon: "Sentiment Satisfied" → Name: `sentiment_satisfied` → Use: `:material/sentiment_satisfied:`

