"""
Streamlit Authentication Module

Provides user authentication using streamlit-authenticator library.
Supports username/password authentication with secure session management.
"""

from typing import Optional, Dict, Any
import streamlit as st
import yaml
from pathlib import Path
from yaml.loader import SafeLoader
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Try to import streamlit-authenticator
try:
    import streamlit_authenticator as stauth
    AUTHENTICATOR_AVAILABLE = True
except ImportError:
    AUTHENTICATOR_AVAILABLE = False
    logger.warning("streamlit-authenticator not installed. Run: pip install streamlit-authenticator")


def load_auth_config(config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load authentication configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to .streamlit/auth_config.yaml
    
    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    if config_path is None:
        config_path = Path(".streamlit") / "auth_config.yaml"
    
    if not config_path.exists():
        logger.warning(f"Auth config file not found at {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except Exception as e:
        logger.error(f"Failed to load auth config: {e}", exc_info=True)
        return None


def create_default_auth_config(config_path: Optional[Path] = None) -> None:
    """
    Create a default authentication configuration file.
    
    Args:
        config_path: Path to config file. Defaults to .streamlit/auth_config.yaml
    """
    if config_path is None:
        config_path = Path(".streamlit") / "auth_config.yaml"
    
    # Create .streamlit directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'admin@example.com',
                    'name': 'Admin User',
                    'password': ''  # Will be hashed on first run
                }
            }
        },
        'cookie': {
            'expiry_days': 30,
            'key': 'triadic_auth_key',  # Change this to a random string
            'name': 'triadic_auth_cookie'
        }
        # Note: 'preauthorized' removed - no longer supported in newer versions of streamlit-authenticator
    }
    
    try:
        with open(config_path, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        logger.info(f"Created default auth config at {config_path}")
        logger.warning("⚠️  IMPORTANT: Update the default password and cookie key before using in production!")
    except Exception as e:
        logger.error(f"Failed to create auth config: {e}", exc_info=True)


def hash_password(password: str) -> str:
    """
    Hash a password using streamlit-authenticator's Hasher.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    if not AUTHENTICATOR_AVAILABLE:
        raise ImportError("streamlit-authenticator not installed")
    
    hashed = stauth.Hasher([password]).generate()
    return hashed[0]


def get_authenticator(config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """
    Get an Authenticator instance.
    
    Args:
        config: Authentication configuration. If None, loads from default location.
    
    Returns:
        Authenticator instance or None if not available
    """
    if not AUTHENTICATOR_AVAILABLE:
        return None
    
    if config is None:
        config = load_auth_config()
        if config is None:
            return None
    
    try:
        # Note: preauthorized parameter has been removed from Authenticate class
        # in newer versions of streamlit-authenticator
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        return authenticator
    except Exception as e:
        logger.error(f"Failed to create authenticator: {e}", exc_info=True)
        return None


def render_login_page() -> tuple[Optional[str], Optional[bool], Optional[str]]:
    """
    Render login page and handle authentication.
    
    Returns:
        Tuple of (name, authentication_status, username)
        - name: User's name if authenticated
        - authentication_status: True if authenticated, False if failed, None if not attempted
        - username: Username if authenticated
    """
    if not AUTHENTICATOR_AVAILABLE:
        st.error("Authentication is not available. Please install streamlit-authenticator.")
        st.code("pip install streamlit-authenticator", language="bash")
        return None, None, None
    
    config = load_auth_config()
    if config is None:
        st.warning("Authentication configuration not found.")
        if st.button("Create default config"):
            create_default_auth_config()
            st.rerun()
        return None, None, None
    
    authenticator = get_authenticator(config)
    if authenticator is None:
        st.error("Failed to initialize authenticator.")
        return None, None, None
    
    # Render login form
    # CRITICAL: Check for duplicate form error first - if form already exists, don't try to create it again
    # This happens on reruns when the form is already rendered
    try:
        # Standard call: location as first positional argument
        # Note: login() signature: login(location='main', key='Login', ...)
        name, authentication_status, username = authenticator.login('main')
    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a duplicate form error - if so, this is a rerun and form already exists
        if "multiple identical forms" in error_str or "duplicate" in error_str:
            # Form already exists from previous render - this is normal on reruns
            # Return None to indicate we're waiting for user input
            logger.debug("Login form already exists (rerun) - waiting for user input")
            return None, None, None
        
        # For other errors, try with location as keyword argument
        logger.debug(f"Login with positional location failed, trying keyword: {e}")
        try:
            name, authentication_status, username = authenticator.login(location='main')
        except Exception as e2:
            error_str2 = str(e2).lower()
            # Check again for duplicate form error
            if "multiple identical forms" in error_str2 or "duplicate" in error_str2:
                logger.debug("Login form already exists (rerun) - waiting for user input")
                return None, None, None
            logger.error(f"All login attempts failed: {e2}", exc_info=True)
            return None, None, None
    
    return name, authentication_status, username


def render_logout_button(authenticator: Any) -> None:
    """
    Render logout button.
    
    Args:
        authenticator: Authenticator instance
    """
    if authenticator is not None:
        authenticator.logout('Logout', 'sidebar')


def require_auth(allow_guest: bool = True) -> bool:
    """
    Check if user is authenticated. If not, show login page or guest option.
    
    Args:
        allow_guest: If True, allow users to continue as guest (no persistence)
    
    Returns:
        True if authenticated or guest, False otherwise
    """
    # Check if authentication is enabled
    auth_enabled = st.session_state.get("auth_enabled", False)
    if not auth_enabled:
        # Mark as guest if auth is disabled
        if "is_guest" not in st.session_state:
            st.session_state["is_guest"] = True
            st.session_state["username"] = "guest"
        return True  # Auth not required
    
    # Check if already authenticated
    if st.session_state.get("authentication_status", False):
        st.session_state["is_guest"] = False
        return True
    
    # Check if already in guest mode
    if st.session_state.get("is_guest", False):
        return True
    
    # Show login page with guest option
    if allow_guest:
        col1, col2 = st.columns([2, 1])
        with col1:
            name, authentication_status, username = render_login_page()
        with col2:
            st.markdown("---")
            st.markdown("### Continue as Guest")
            st.caption("Use the app without an account. Your session will not be saved.")
            if st.button("Continue as Guest", use_container_width=True, type="secondary"):
                st.session_state["is_guest"] = True
                st.session_state["username"] = "guest"
                st.session_state["authentication_status"] = None
                st.rerun()
    else:
        name, authentication_status, username = render_login_page()
    
    # Store authentication state
    if authentication_status is not None:
        st.session_state["authentication_status"] = authentication_status
        st.session_state["username"] = username
        st.session_state["name"] = name
        st.session_state["is_guest"] = False
    
    if authentication_status is False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status is None and not st.session_state.get("is_guest", False):
        if not allow_guest:
            st.warning('Please enter your username and password')
        return False
    elif authentication_status or st.session_state.get("is_guest", False):
        return True
    
    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user information.
    
    Returns:
        Dictionary with user info (username, name, email) or None if not authenticated
    """
    if not st.session_state.get("authentication_status", False):
        return None
    
    return {
        "username": st.session_state.get("username"),
        "name": st.session_state.get("name"),
        "email": st.session_state.get("email")
    }

