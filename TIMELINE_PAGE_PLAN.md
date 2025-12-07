# Discussion Timeline Page - Implementation Plan

## Overview
Create a new Streamlit page that displays **AI-generated conversation summaries** in a clean, chronological timeline view. This provides a high-level overview of the discussion progression without showing individual messages.

## Current State
- Summaries are generated every N turns (default: 5)
- Only the **latest summary** is stored in `st.session_state.conversation_summary`
- Summaries are incremental (build upon previous summary)

## Required Changes
1. **Store Summary History**: Instead of overwriting, store all summaries in a list
2. **Summary Metadata**: Each summary needs:
   - `summary_text`: The AI-generated summary
   - `turn_number`: Turn number when summary was generated
   - `timestamp`: Time when summary was generated
   - `message_count`: Number of messages covered by this summary
3. **Timeline Display**: Show summaries chronologically with clear progression

## UI Components

### 1. Page Header
- Title: "Discussion Timeline"
- Icon: `:material/timeline:` or `:material/summarize:`
- Brief description: "Chronological view of conversation summaries"

### 2. Timeline Visualization
**Recommended: Vertical Timeline**
- Vertical line/bar on the left showing progression
- Summary cards on the right
- Each summary represents a "checkpoint" in the conversation
- Turn numbers clearly displayed
- Timestamps for each summary

### 3. Summary Cards
Each summary card should show:
- **Turn Range**: "Turns 1-5", "Turns 6-10", etc.
- **Timestamp**: When summary was generated
- **Summary Text**: The AI-generated summary (2-3 sentences)
- **Message Count**: Number of messages covered
- **Visual Indicator**: Progress indicator showing position in timeline

### 4. Controls & Filters
- **Search**: Filter summaries by content
- **Turn Range Filter**: Show summaries for specific turn ranges
- **View Options**: 
  - Compact vs Expanded view
  - Show/Hide metadata
  - Group by time periods (if conversation spans multiple sessions)

### 5. Statistics Summary
- Total summaries generated
- Total turns covered
- Conversation duration (first to last summary)
- Average turns per summary
- Latest summary preview

## Implementation Steps

### Phase 1: Store Summary History
1. **Modify summary storage** in `app.py`:
   - Change from single `conversation_summary` to `summary_history` list
   - Each summary entry: `{summary_text, turn_number, timestamp, message_count}`
   - Keep latest summary for backward compatibility (homepage display)

2. **Update `services/conversation_summarizer.py`**:
   - Return summary with metadata (turn number, timestamp)
   - Or modify `app.py` to add metadata after generation

### Phase 2: Basic Timeline View
1. Create new page file: `pages/4_📅_Timeline.py`
2. Add page to navigation in `app.py`
3. Implement basic vertical timeline with summary cards
4. Show turn ranges, timestamps, and summary text
5. Add visual progression indicators

### Phase 3: Enhanced UX
1. Add search functionality (filter summaries by content)
2. Add turn range filtering
3. Add statistics summary section
4. Add expandable cards for longer summaries

### Phase 4: Advanced Features
1. Add export functionality (copy timeline, export to markdown)
2. Add time-based grouping (if conversation spans multiple sessions)
3. Add "jump to turn" navigation
4. Add summary comparison view (show progression)

## Technical Details

### File Structure
```
pages/4_📅_Timeline.py          # Main timeline page
utils/streamlit_timeline.py     # Timeline rendering logic (optional, if complex)
```

### Key Functions
- `render_timeline_view(summary_history)`: Main timeline rendering
- `render_summary_card(summary, index)`: Individual summary card
- `render_timeline_statistics(summary_history)`: Summary stats
- `filter_summaries(summary_history, search_term, turn_range)`: Filtering logic

### Summary History Structure
```python
summary_history = [
    {
        "summary_text": "The discussion began with...",
        "turn_number": 5,
        "timestamp": "12:34:15",
        "message_count": 10,
        "turn_range": (1, 5)  # First turn to last turn covered
    },
    {
        "summary_text": "The conversation progressed to...",
        "turn_number": 10,
        "timestamp": "12:45:30",
        "message_count": 10,
        "turn_range": (6, 10)
    },
    # ... more summaries
]
```

### Styling
- Use existing color scheme from `SPEAKER_INFO`
- Leverage `inject_custom_css()` for custom timeline styling
- Use Streamlit native components where possible
- Add custom CSS for timeline line/connectors if needed

### Performance
- Use `@st.cache_data` for filtered/processed summary lists
- Efficient filtering/search implementation

## Example Layout

```
┌─────────────────────────────────────────────────┐
│ 📅 Discussion Timeline                          │
│ Chronological view of conversation summaries    │
├─────────────────────────────────────────────────┤
│ [Search] [Turn Range: All ▼] [View: Compact ▼] │
├─────────────────────────────────────────────────┤
│ Stats: 3 summaries • Turns 1-15 • 12:34-13:45  │
├─────────────────────────────────────────────────┤
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ Turns 1-5 • 12:34:15                        │ │
│ │ ─────────────────────────────────────────── │ │
│ │ The discussion began with an exploration    │ │
│ │ of AI ethics, focusing on the implications  │ │
│ │ of autonomous decision-making. GPT-A         │ │
│ │ presented a framework for ethical AI...     │ │
│ │                                              │ │
│ │ 📊 10 messages • Turn 5                      │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ Turns 6-10 • 12:45:30                       │ │
│ │ ─────────────────────────────────────────── │ │
│ │ The conversation shifted to practical       │ │
│ │ applications, with GPT-B raising concerns   │ │
│ │ about bias in training data. Both speakers  │ │
│ │ explored potential mitigation strategies... │ │
│ │                                              │ │
│ │ 📊 10 messages • Turn 10                     │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ Turns 11-15 • 13:12:45                      │ │
│ │ ─────────────────────────────────────────── │ │
│ │ The discussion concluded with a consensus    │ │
│ │ on the need for transparent AI systems...   │ │
│ │                                              │ │
│ │ 📊 10 messages • Turn 15                     │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Future Enhancements (Post-MVP)
- **Summary Comparison**: Side-by-side view showing how discussion evolved
- **Topic Detection**: Group summaries by detected topics
- **Visual Progression**: Chart showing conversation flow/direction
- **Export Options**: PDF, Markdown, JSON export
- **Deep Dive**: Click summary to see underlying messages for that period
- **Real-time Updates**: Auto-refresh when new summaries are generated
- **Summary Regeneration**: Allow regenerating summaries with different intervals
