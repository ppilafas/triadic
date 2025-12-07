#!/bin/bash
# Setup GitHub repository for Triadic project

set -e

echo "========================================="
echo "  GitHub Repository Setup for Triadic"
echo "========================================="
echo ""

# Step 1: Authenticate (if not already done)
if ! gh auth status &>/dev/null; then
    echo "Step 1: Authenticate with GitHub"
    echo "-----------------------------------"
    echo "Run: gh auth login"
    echo "Follow the prompts to authenticate via browser"
    echo ""
    read -p "Press Enter after you've authenticated..."
fi

# Step 2: Create repository
echo ""
echo "Step 2: Create GitHub repository"
echo "-----------------------------------"
REPO_NAME="triadic"
echo "Creating repository: $REPO_NAME"

# Create the repository (public by default, add --private for private repo)
gh repo create "$REPO_NAME" --public --source=. --remote=origin --push

echo ""
echo "✅ Repository created and code pushed!"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com/$(gh api user --jq .login)/$REPO_NAME"
echo "2. Deploy on Streamlit Cloud: https://share.streamlit.io"
echo ""

