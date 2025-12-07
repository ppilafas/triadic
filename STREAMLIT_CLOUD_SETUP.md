# Streamlit Cloud Setup Guide

## Adding Your OpenAI API Key

### ✅ Method 1: Environment Variables (Most Common)

1. **Go to your Streamlit Cloud dashboard:**
   - Visit https://share.streamlit.io
   - Log in with your GitHub account
   - Find your app (triadic)

2. **Open the app settings:**
   - Click on your app
   - Click the "⋮" (three dots) menu in the top right
   - Select "Settings"

3. **Add environment variable:**
   - Look for "Environment variables" section (may be under "Advanced settings")
   - Click "Add environment variable"
   - **Key:** `OPENAI_API_KEY`
   - **Value:** `sk-your-actual-api-key-here`
   - Click "Save"

4. **Redeploy:**
   - Streamlit Cloud will automatically redeploy
   - Or click "Reboot app" in the app menu

### ✅ Method 2: Secrets Tab (If Available)

If you see a "Secrets" tab in Settings:

1. Go to Settings > Secrets tab
2. Add in TOML format:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```
3. Click "Save"

### ✅ Method 3: Manage App Button

1. Click the "Manage app" button (bottom right of your app)
2. Look for "Secrets" or "Environment variables" section
3. Add your key there

### ✅ Method 4: Using secrets.toml File (Alternative)

If the above methods don't work, you can create a `.streamlit/secrets.toml` file locally (this file is gitignored):

1. Create `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key-here"
   ```

2. **IMPORTANT:** This file is already in `.gitignore`, so it won't be committed
3. For Streamlit Cloud, you'll still need to add it via the dashboard

## Local Development

For local development, create a `.env` file (already in `.gitignore`):

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Or export it in your shell:
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

## Security Notes

- ✅ **DO**: Use Streamlit Cloud environment variables/secrets for production
- ✅ **DO**: Use `.env` file for local development (already gitignored)
- ❌ **DON'T**: Commit API keys to git
- ❌ **DON'T**: Hardcode keys in your Python files
- ❌ **DON'T**: Share your API key publicly

## Verification

After adding the key, your app should:
1. Load without the "OPENAI_API_KEY is missing" error
2. Be able to make API calls to OpenAI
3. Function normally

If you still see the error:
- Make sure the variable name is exactly `OPENAI_API_KEY` (case-sensitive)
- Check that you saved the changes
- Try rebooting the app manually
- Check the app logs in "Manage app" > "Logs"

## Troubleshooting

**Can't find Secrets/Environment Variables?**
- Look in "Settings" > "Advanced settings"
- Check the "Manage app" menu
- Some accounts may need to verify email first
- Try refreshing the page
