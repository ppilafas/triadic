# Streamlit Authentication Guide

## Overview

This guide covers different authentication options for Streamlit applications and how to implement them.

## Authentication Options

### 1. **Streamlit Native OIDC (OpenID Connect)** ⭐ Recommended for Production

**Best for:** Production apps, enterprise deployments, OAuth/SSO integration

**Pros:**
- Native Streamlit support (built-in)
- Supports Google, Microsoft, Okta, and other OIDC providers
- Secure, industry-standard protocol
- No additional dependencies

**Cons:**
- Requires OIDC provider setup
- More complex initial configuration

**Implementation:**
```python
import streamlit as st

# Check if user is logged in
if not st.user.is_logged_in:
    if st.button("Log in"):
        st.login("google")  # or "microsoft", "okta", etc.
else:
    if st.button("Log out"):
        st.logout()
    st.write(f"Hello, {st.user.name}!")
```

**Setup:**
1. Configure `.streamlit/secrets.toml`:
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "your_cookie_secret"

[auth.google]
client_id = "your_client_id"
client_secret = "your_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### 2. **streamlit-authenticator** ⭐ Recommended for Simple Apps

**Best for:** Simple apps, username/password authentication, quick setup

**Pros:**
- Easy to set up
- Username/password based
- Cookie-based session management
- Password hashing included

**Cons:**
- Requires manual user management
- No OAuth/SSO support
- Additional dependency

**Installation:**
```bash
pip install streamlit-authenticator
```

**Implementation:**
See `utils/streamlit_auth.py` for full implementation.

### 3. **Custom Authentication**

**Best for:** Full control, custom requirements, database integration

**Pros:**
- Complete control
- Can integrate with any database
- Custom user management

**Cons:**
- More development effort
- Security considerations
- Session management complexity

## Recommended Implementation

For this application, we'll implement **streamlit-authenticator** as it provides:
- Simple setup
- Good security practices
- Easy integration with existing code
- User-specific session persistence

## Integration with Session Persistence

Once authentication is implemented, we can update the persistence system to use user-specific storage:

```python
# In utils/streamlit_persistence.py
def _get_state_file_path() -> Path:
    if USE_SESSION_SPECIFIC_STORAGE:
        # Get username from authentication
        username = st.session_state.get("username", "anonymous")
        return _STORAGE_DIR / f"session_state_{username}.json"
    else:
        return _STORAGE_DIR / "session_state.json"
```

## Security Best Practices

1. **Use HTTPS** in production
2. **Hash passwords** (streamlit-authenticator does this automatically)
3. **Secure cookies** for session management
4. **Validate user input** to prevent injection attacks
5. **Rate limiting** for login attempts
6. **Session expiration** after inactivity

## Next Steps

1. Choose authentication method
2. Install dependencies (if using streamlit-authenticator)
3. Configure user credentials
4. Integrate with app
5. Update persistence to be user-specific

