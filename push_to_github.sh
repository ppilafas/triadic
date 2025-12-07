#!/bin/bash
# Auto-push script for Triadic project
# Usage: ./push_to_github.sh [commit message]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get commit message from argument or use default
COMMIT_MSG="${1:-Update codebase}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Triadic - Auto Push to GitHub${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Check if there are any changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit.${NC}"
    exit 0
fi

# Show status
echo -e "${GREEN}Current status:${NC}"
git status --short
echo ""

# Stage all changes
echo -e "${GREEN}Staging all changes...${NC}"
git add .
echo ""

# Commit with message
echo -e "${GREEN}Committing changes...${NC}"
echo -e "Commit message: ${YELLOW}${COMMIT_MSG}${NC}"
git commit -m "$COMMIT_MSG"
echo ""

# Check if remote has changes and pull if needed
echo -e "${GREEN}Checking for remote changes...${NC}"
git fetch origin main
if [ "$(git rev-list HEAD...origin/main --count)" != "0" ]; then
    echo -e "${YELLOW}Remote has changes. Pulling with rebase...${NC}"
    if ! git pull --rebase origin main; then
        echo -e "${RED}❌ Failed to pull remote changes. Please resolve conflicts manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Successfully rebased local changes on top of remote.${NC}"
    echo ""
fi

# Push to GitHub
echo -e "${GREEN}Pushing to GitHub...${NC}"
if git push origin main; then
    echo ""
    echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
    echo ""
    echo "Repository: https://github.com/ppilafas/triadic"
    echo "Streamlit Cloud will automatically redeploy."
else
    echo ""
    echo -e "${RED}❌ Push failed. Check the error above.${NC}"
    exit 1
fi

