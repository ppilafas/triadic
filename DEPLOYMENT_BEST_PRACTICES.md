# Deployment Best Practices - API Key Security

## ✅ Common Practices for Secure API Key Management

### 1. **Never Commit Keys to Git**
- ❌ **NEVER** put API keys in code files
- ❌ **NEVER** commit `.env` files with real keys
- ❌ **NEVER** hardcode keys in Python files
- ✅ **ALWAYS** use `.gitignore` to exclude sensitive files

### 2. **Use Environment Variables / Secrets**

**Local Development:**
```bash
# .env file (gitignored)
OPENAI_API_KEY=sk-your-key-here
```

**Cloud Deployment (Streamlit Cloud):**
- Use platform's secrets/environment variables feature
- Keys are encrypted and never exposed in code

### 3. **Template Files for Documentation**

Create example/template files that show the structure but not real keys:

**Example: `.env.example`**
```bash
OPENAI_API_KEY=sk-your-key-here
```

This file CAN be committed - it's just documentation.

### 4. **Documentation in README**

Document how to set up keys without revealing them:

```markdown
## Setup

1. Copy `.env.example` to `.env`
2. Add your `OPENAI_API_KEY` to `.env`
3. Never commit `.env` to git
```

### 5. **Platform-Specific Secrets Management**

**Streamlit Cloud:**
- Use "Environment variables" or "Secrets" in dashboard
- Keys are encrypted server-side
- Never visible in code or logs

**Other Platforms:**
- **Heroku:** Config vars in dashboard
- **AWS:** Secrets Manager or Parameter Store
- **Google Cloud:** Secret Manager
- **Azure:** Key Vault

## ✅ Your Current Setup (Already Secure!)

Your project already follows best practices:

1. ✅ `.gitignore` excludes `.env` and `.streamlit/secrets.toml`
2. ✅ Code reads from environment variables, not hardcoded values
3. ✅ No API keys in committed files
4. ✅ Template/documentation files can be committed safely

## 🔒 Security Checklist

- [x] `.env` in `.gitignore`
- [x] `.streamlit/secrets.toml` in `.gitignore`
- [x] No hardcoded keys in code
- [x] Code reads from `os.getenv()` or `st.secrets`
- [x] Documentation explains setup process
- [ ] Add `.env.example` template (optional but recommended)

## 📝 Recommended Addition

Create a `.env.example` file that shows the structure:

```bash
# Copy this file to .env and add your actual keys
# Never commit .env to git!

OPENAI_API_KEY=sk-your-key-here
```

This helps other developers (or future you) understand what keys are needed.

