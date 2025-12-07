#!/usr/bin/env bash
set -e

# Resolve script directory (your triadic root)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[triadic] Using root: $ROOT_DIR"

# 0. Load .env if present
if [ -f ".env" ]; then
  echo "[triadic] Loading environment from .env"
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

# 1. Create virtual env if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "[triadic] Creating virtualenv in .venv"
  python3 -m venv .venv
fi

# 2. Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Upgrade pip + install ALL dependencies (Streamlit + Chainlit)
echo "[triadic] Installing Python dependencies..."
pip install --upgrade pip

# Core AI deps
pip install openai

# Streamlit Showcase deps (Telemetry uses pandas/altair, Auth for user management)
pip install streamlit streamlit-autorefresh pandas altair streamlit-authenticator

# Chainlit deps
pip install chainlit

echo "[triadic] Dependencies installed."

# 4. Check for OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
  echo "[triadic] WARNING: OPENAI_API_KEY is not set."
  echo "          Export it before running this script, e.g.:"
  echo '          export OPENAI_API_KEY="sk-..."'
fi

# 5. Interface Selection Menu
echo ""
echo "========================================="
echo "   TRIADIC • GPT-5.1 System Launcher     "
echo "========================================="
echo "1) Streamlit Showcase (Visual Dashboard)"
echo "2) Chainlit Interface (Agentic Chat)"
echo "3) Streamlit with Authentication"
echo "========================================="
read -r -p "Select interface [1/2/3] (default: 1): " choice

# Default to 1 if empty
choice=${choice:-1}

if [[ "$choice" == "1" ]]; then
    echo "[triadic] Launching Streamlit..."
    streamlit run app.py
elif [[ "$choice" == "2" ]]; then
    echo "[triadic] Launching Chainlit..."
    # -w flag enables auto-reload (watch mode)
    chainlit run app_chainlit.py -w
elif [[ "$choice" == "3" ]]; then
    echo "[triadic] Launching Streamlit with Authentication enabled..."
    export AUTH_ENABLED=true
    streamlit run app.py
else
    echo "[triadic] Invalid selection. Exiting."
    exit 1
fi