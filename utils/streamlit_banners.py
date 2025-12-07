"""
Streamlit Banner Module

Handles banner rendering for Streamlit UI:
- App banner (Triadic Show logo)
- Broadcast banner (ON AIR indicator)
"""

import base64
from pathlib import Path
from typing import Optional, Callable
import streamlit as st
from utils.streamlit_ui import SPEAKER_INFO
from utils.logging_config import get_logger

logger = get_logger(__name__)


@st.cache_resource
def _load_banner_image() -> Optional[bytes]:
    """
    Load banner image file as bytes (cached with @st.cache_resource).
    
    Args:
        None (banner path is fixed)
    
    Returns:
        Banner image bytes if found, None otherwise
    """
    banner_path = Path("public/banners/triadic-banner.png")
    if banner_path.exists():
        try:
            with open(banner_path, "rb") as img_file:
                return img_file.read()
        except Exception as e:
            logger.warning(f"Failed to load banner {banner_path}: {e}")
    return None


@st.cache_data
def _encode_banner_data_uri(img_data: bytes) -> str:
    """
    Encode banner image bytes as base64 data URI (cached with @st.cache_data).
    
    Args:
        img_data: Banner image bytes
    
    Returns:
        Base64 data URI string
    """
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def render_app_banner(clickable: bool = False, on_click: Optional[Callable] = None) -> bool:
    """
    Render the Triadic Show banner at the top of the main content area.
    
    Loads the banner image from public/banners/ and displays it as a header.
    Uses @st.cache_resource and @st.cache_data for efficient loading (Phase 3 optimization).
    
    Args:
        clickable: If True, makes the banner clickable
        on_click: Optional callback function to call when banner is clicked
    
    Returns:
        True if banner was clicked (when clickable=True), False otherwise
    """
    # Load banner image (cached)
    img_data = _load_banner_image()
    
    if img_data:
        try:
            # Encode as data URI (cached)
            banner_data_uri = _encode_banner_data_uri(img_data)
            
            if clickable:
                
                # Use HTML img tag to better control transparency
                st.markdown(f"""
                    <div class="app-banner-container clickable-banner-wrapper" style="position: relative;">
                        <img src="{banner_data_uri}" alt="Triadic Show" class="app-banner" style="background: transparent; image-rendering: -webkit-optimize-contrast;" />
                """, unsafe_allow_html=True)
                
                # Add hover overlay HTML
                st.markdown("""
                    <div class="banner-hover-overlay">
                        <div class="banner-cta-text">
                            <span>Click to Enter →</span>
                        </div>
                    </div>
                    <style>
                        .app-banner-container {
                            position: relative;
                            border-radius: var(--radius-lg);
                            overflow: hidden;
                            box-shadow: var(--shadow-md);
                            cursor: pointer;
                            transition: all var(--duration-normal) var(--ease-out);
                        }
                        .app-banner-container:hover {
                            transform: scale(1.015) translateY(-2px);
                            box-shadow: var(--shadow-xl), 0 0 30px rgba(77, 166, 255, 0.2);
                        }
                        .banner-hover-overlay {
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background: rgba(0, 0, 0, 0.4);
                            backdrop-filter: blur(8px);
                            opacity: 0;
                            transition: opacity var(--duration-normal) var(--ease-out);
                            border-radius: var(--radius-lg);
                            pointer-events: none;
                            z-index: 5;
                        }
                        .clickable-banner-wrapper:hover .banner-hover-overlay {
                            opacity: 1;
                        }
                        .banner-cta-text {
                            background: rgba(0, 0, 0, 0.7);
                            backdrop-filter: blur(12px);
                            padding: 14px 28px;
                            border-radius: 12px;
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        }
                        .banner-cta-text span {
                            color: white;
                            font-weight: 600;
                            font-size: 0.95rem;
                            letter-spacing: 0.5px;
                        }
                    </style>
                    </div>
                """, unsafe_allow_html=True)
                
                # Create clickable button overlay using columns
                click_col1, click_col2, click_col3 = st.columns([1, 8, 1])
                with click_col2:
                    clicked = st.button("", key="banner_click_button", use_container_width=True, help="Click to enter the app")
                    if clicked:
                        if on_click:
                            on_click()
                        return True
                return False
            else:
                # Render banner with proper styling (non-clickable)
                # Use HTML img tag to better control transparency
                banner_html = f"""
                <div class="app-banner-container">
                    <img src="{banner_data_uri}" alt="Triadic Show" class="app-banner" style="background: transparent; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" />
                </div>
                """
                st.markdown(banner_html, unsafe_allow_html=True)
                return False
        except Exception as e:
            logger.warning(f"Failed to process banner: {e}")
            return False
    else:
        logger.warning("Banner not found at public/banners/triadic-banner.png")
        return False


def render_broadcast_banner(speaker_key: str) -> None:
    """
    Render ON AIR banner for current speaker.
    
    Args:
        speaker_key: Speaker key (gpt_a or gpt_b)
    """
    meta = SPEAKER_INFO.get(speaker_key, SPEAKER_INFO["gpt_a"])
    color = meta["color"]
    label = meta["full_label"].upper()
    
    st.markdown(
        f"""
        <div style="
            background-color: {color}15; 
            border: 1px solid {color}; 
            border-radius: 8px; 
            padding: 8px; 
            text-align: center; 
            margin-bottom: 20px;
            animation: pulse 2s infinite;">
            <span style="color: {color}; font-weight: bold; letter-spacing: 1px; font-size: 0.9em;">
                <span style="color: #ef4444;">●</span> ON AIR: {label}
            </span>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 {color}30; }}
                70% {{ box-shadow: 0 0 0 8px {color}00; }}
                100% {{ box-shadow: 0 0 0 0 {color}00; }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

