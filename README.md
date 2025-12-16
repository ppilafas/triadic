## Triadic – GPT‑5.1 Self‑Dialogue Podcast (Streamlit App)

Triadic is a GPT‑5.1 “self‑dialogue podcast” application where a **Host** moderates a conversation between two AI guests (**GPT‑A** and **GPT‑B**) in a talk‑show format.  
The app is built on **Streamlit 1.51+** with a **framework‑agnostic AI backend** that you can reuse in other projects.

---

## Features

- **Three‑speaker podcast format**: Host, GPT‑A, GPT‑B with alternating turns
- **Auto‑run mode**: Continuous turns with a configurable delay between messages
- **Manual control**: Trigger next turn, inject your own messages, pause/resume
- **Native Streamlit UI**: Uses `st.chat_message`, `st.chat_input`, and 1.51+ patterns (fragments, caching)
- **Vector‑store / RAG support**: Upload files, index them into OpenAI vector stores, and ask questions
- **Speech I/O**: Whisper‑based speech‑to‑text and text‑to‑speech helpers
- **Authentication & persistence**: Optional login, user‑scoped sessions, and session autosave
- **Reusable backend**: Conversation state, prompt building, and OpenAI API wrapper are UI‑agnostic

---

## Project Layout (Current)

```text
triadic/
├── app.py                    # Main Streamlit app (primary entrypoint)
├── app_chainlit.py           # Optional / legacy Chainlit interface (if enabled)
├── ai_api.py                 # OpenAI client wrapper + RAG and streaming helpers
├── config.py                 # Central configuration (models, audio, UI, speakers, etc.)
├── exceptions.py             # Custom exception hierarchy
├── stt.py                    # Speech‑to‑text utilities
├── tts.py                    # Text‑to‑speech utilities
├── system.txt                # System prompt used by the conversation engine
│
├── core/                     # Framework‑agnostic conversation logic
│   ├── conversation.py       # ConversationState, speaker alternation, history formats
│   └── message_builder.py    # Prompt assembly from history + system prompt
│
├── services/                 # Higher‑level business services
│   └── topic_generator.py    # AI‑generated topic suggestions
│
├── utils/                    # Streamlit + shared utilities
│   ├── logging_config.py     # Structured logging setup
│   ├── validators.py         # Input / config validation helpers
│   ├── streamlit_ui.py       # (If present) composite UI helpers
│   ├── streamlit_* .py       # Sidebar, chat input, messages, telemetry, styles, etc.
│   └── vector_store_manager.py  # Helpers for OpenAI vector‑store operations
│
├── kickstart_streamlit_project.py  # Script to scaffold a new app using this backend
├── AI_BACKEND_REUSE_GUIDE.md      # How to reuse the backend in other projects
├── STREAMLIT_CLOUD_SETUP.md       # Streamlit Cloud specific deployment notes
├── DEPLOYMENT_BEST_PRACTICES.md   # General deployment guidance
├── AUTHENTICATION_GUIDE.md        # Auth patterns used in this app
├── SESSION_PERSISTENCE_GUIDE.md   # Session persistence and autosave strategy
├── .git_workflow.md               # Git and branching conventions
└── chainlit.md                    # Notes / usage for the optional Chainlit interface
```

---

## Getting Started (Local Dev)

### 1. Install dependencies

From the project root:

```bash
pip install -r requirements.txt
```

Make sure you are using **Python 3.10+**.

### 2. Configure OpenAI

Set your API key using one of:

- Environment variable:

```bash
export OPENAI_API_KEY="sk‑..."
```

- Or Streamlit Cloud secrets:
  - Add `OPENAI_API_KEY` in your Streamlit app settings

`config.py` contains helper logic to resolve the model and API key from env, secrets, or (when applicable) a UI settings page.

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

Key runtime controls live in the **sidebar** and top controls:

- **On‑air / Auto‑run toggle** – enables continuous turns
- **Trigger next turn** – manually advances the conversation
- **Knowledge base / RAG controls** – upload files and index them
- **Settings** – model selection, delays, and other tuning knobs

If `AUTH_ENABLED=true` is set in the environment, the app will show the login flow described in `AUTHENTICATION_GUIDE.md`.

---

## Reusing the Backend

The AI backend is intentionally decoupled from Streamlit and can be dropped into other projects.

- Core files:
  - `ai_api.py`
  - `config.py`
  - `exceptions.py`
  - `core/conversation.py`
  - `core/message_builder.py`
  - `services/topic_generator.py`
  - `stt.py`, `tts.py` (if you need audio)
- See **`AI_BACKEND_REUSE_GUIDE.md`** for:
  - Minimal usage examples (`call_model`, streaming, RAG)
  - How to integrate with Flask/FastAPI/other frameworks
  - Recommended project shapes when embedding Triadic logic elsewhere

---

## Kickstarting a New Streamlit Project with This Backend

You can scaffold a fresh Streamlit app that reuses the Triadic backend with a single command:

```bash
# From the Triadic project root
python kickstart_streamlit_project.py my_chatbot ~/projects/
```

This will create a new folder (e.g. `~/projects/my_chatbot`) with:

- `app.py` – simple chat UI wired to the backend
- `backend/` – copied `ai_api.py`, `config.py`, `core/`, `services/`, etc.
- `utils/` – logging + validation helpers
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`

The generated project is intentionally minimal so you can iterate quickly and commit it to its **own** git repo.

---

## Deployment

- For **Streamlit Cloud** specifics, see `STREAMLIT_CLOUD_SETUP.md`
- For more general container/VM deployment patterns, see `DEPLOYMENT_BEST_PRACTICES.md`

At a minimum, you will need to:

- Provide `OPENAI_API_KEY` as an environment variable or secret
- Persist any optional storage used by telemetry or session persistence (if enabled)

---

## Contributing & Workflow

- Git and branching conventions are documented in `.git_workflow.md`
- The codebase is structured so that:
  - **`core/` and `services/`** stay UI‑agnostic
  - **`utils/streamlit_*.py`** own all Streamlit specifics
  - **`app.py`** is a thin, declarative composition layer

When adding new features:

- Prefer putting shared / business logic into `core/` or `services/`
- Keep Streamlit‑only details in `utils/streamlit_*.py`
- Update this `README.md` and `AI_BACKEND_REUSE_GUIDE.md` when you introduce new backend capabilities or change the high‑level architecture

This structure is designed to support **future revisions and clean git history** as the app evolves.


