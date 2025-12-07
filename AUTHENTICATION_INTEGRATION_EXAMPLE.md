# Authentication Integration Example

## Quick Start

### 1. Install streamlit-authenticator

```bash
pip install streamlit-authenticator
```

Or add to `bootstrap.sh`:
```bash
pip install streamlit-authenticator
```

### 2. Create Authentication Config

The module will create a default config on first run, or you can create it manually:

**File: `.streamlit/auth_config.yaml`**
```yaml
credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Admin User
      password: $2b$12$...  # Hashed password (use hash_password() function)
    user1:
      email: user1@example.com
      name: User One
      password: $2b$12$...  # Hashed password

cookie:
  expiry_days: 30
  key: your_random_cookie_key_here  # Change this!
  name: triadic_auth_cookie

preauthorized:
  emails: []
```

### 3. Hash Passwords

```python
from utils.streamlit_auth import hash_password

# Hash a password
hashed = hash_password("your_plaintext_password")
print(hashed)  # Copy this to auth_config.yaml
```

### 4. Integrate into app.py

**Option A: Simple Integration (Login Required)**

```python
# At the top of app.py, before any other content
from utils.streamlit_auth import require_auth

# Require authentication
if not require_auth():
    st.stop()  # Stop execution if not authenticated

# Rest of your app...
```

**Option B: Conditional Authentication (Optional)**

```python
# At the top of app.py
from utils.streamlit_auth import require_auth, get_current_user

# Enable/disable auth via config or environment variable
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
st.session_state["auth_enabled"] = AUTH_ENABLED

if AUTH_ENABLED:
    if not require_auth():
        st.stop()
    
    # Get current user info
    user = get_current_user()
    if user:
        st.sidebar.write(f"Logged in as: {user['name']}")
```

**Option C: Full Integration with Logout**

```python
# At the top of app.py
from utils.streamlit_auth import (
    require_auth, 
    get_current_user, 
    get_authenticator,
    load_auth_config,
    render_logout_button
)

# Require authentication
if not require_auth():
    st.stop()

# Show user info and logout button in sidebar
user = get_current_user()
if user:
    with st.sidebar:
        st.write(f"**User:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        
        # Logout button
        config = load_auth_config()
        if config:
            authenticator = get_authenticator(config)
            if authenticator:
                render_logout_button(authenticator)

# Rest of your app...
```

### 5. Update Persistence for User-Specific Storage

**In `utils/streamlit_persistence.py`:**

```python
# Enable user-specific storage
USE_SESSION_SPECIFIC_STORAGE = True  # Change to True

def _get_state_file_path() -> Path:
    if USE_SESSION_SPECIFIC_STORAGE:
        # Get username from authentication
        username = st.session_state.get("username", "anonymous")
        return _STORAGE_DIR / f"session_state_{username}.json"
    else:
        return _STORAGE_DIR / "session_state.json"
```

## Complete Example

See `app_with_auth_example.py` for a complete working example.

## Security Notes

1. **Change the cookie key** in `auth_config.yaml` to a random string
2. **Use strong passwords** for user accounts
3. **Enable HTTPS** in production
4. **Keep `auth_config.yaml` secure** - don't commit it to git
5. **Add `.streamlit/auth_config.yaml` to `.gitignore`**

## Testing

1. Start the app
2. You'll see a login form
3. Enter username and password from `auth_config.yaml`
4. After login, you'll have access to the app
5. Your session state will be saved per-user

