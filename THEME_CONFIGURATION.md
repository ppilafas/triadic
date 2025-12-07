# Professional Theme Configuration

## Overview

This document describes the professional dark theme configuration for Triadic Studio, implemented using Streamlit's native theming system.

## Theme Design Philosophy

The theme is designed to:
- **Professional**: Clean, modern aesthetic suitable for a production application
- **Consistent**: Colors align with speaker color coding (Host=Green, GPT-A=Blue, GPT-B=Red)
- **Readable**: High contrast text on dark backgrounds for reduced eye strain
- **Cohesive**: Unified color palette across all UI elements

## Color Scheme

### Primary Colors
- **Primary Accent**: `#4da6ff` (Blue) - Matches GPT-A speaker color
- **Background**: `#0f172a` (Slate-900) - Deep, professional dark
- **Secondary Background**: `#1e293b` (Slate-800) - Sidebar and widgets
- **Text**: `#f1f5f9` (Slate-100) - High contrast, readable
- **Secondary Text**: `#cbd5e1` (Slate-300) - Subtle secondary information

### Speaker Color Mapping
- **Host**: `#10b981` (Emerald-500) - Green
- **GPT-A**: `#4da6ff` (Blue) - Primary accent
- **GPT-B**: `#ff6b6b` (Red) - Secondary accent

### Chart Colors
The chart color palette matches the speaker colors for consistency:
- Primary: Blue (GPT-A)
- Secondary: Red (GPT-B)
- Tertiary: Green (Host)
- Quaternary: Amber (accent)
- Quinary: Purple (accent)

## Configuration File

The theme is configured in `.streamlit/config.toml` using Streamlit 1.51+ native theming syntax.

### Key Features

1. **Base Theme**: Inherits from Streamlit's dark theme
2. **Separate Sidebar Styling**: Sidebar has its own color configuration
3. **Chart Colors**: Custom palette matching speaker colors
4. **Font Configuration**: Sans-serif with proper sizing for headings and code
5. **Border Styling**: Subtle borders with modern border radius

## Benefits of Native Theming

1. **Performance**: Native theme rendering is faster than CSS overrides
2. **Consistency**: All Streamlit components automatically use the theme
3. **Maintainability**: Centralized configuration in one file
4. **Accessibility**: Native themes follow accessibility best practices
5. **Future-Proof**: Compatible with Streamlit updates

## Custom CSS Integration

The native theme works alongside custom CSS in `utils/streamlit_ui.py`:
- **Native Theme**: Handles base colors, fonts, and component styling
- **Custom CSS**: Handles advanced styling like gradients, animations, and specific component enhancements

This hybrid approach provides:
- Consistent base styling (native theme)
- Advanced visual effects (custom CSS)
- Best of both worlds

## Theme Customization

To customize the theme:

1. **Edit `.streamlit/config.toml`**
   - Modify color values in the `[theme]` section
   - Adjust font settings in `[theme.font]`
   - Update chart colors in `[theme.chart]`

2. **Restart Streamlit**
   - Most theme changes require a restart
   - Some changes (like font faces) may require a full server restart

3. **Use Streamlit's Theme Editor** (Optional)
   - Run the app
   - Click menu (☰) → Settings → Edit active theme
   - Make changes and copy to `config.toml`

## Color Reference

### Slate Palette (Backgrounds)
- `#0f172a` - Slate-900 (Main background)
- `#1e293b` - Slate-800 (Sidebar, widgets)
- `#334155` - Slate-700 (Optional for hover states)

### Text Colors
- `#f1f5f9` - Slate-100 (Primary text)
- `#cbd5e1` - Slate-300 (Secondary text)
- `#94a3b8` - Slate-400 (Tertiary text)

### Accent Colors
- `#4da6ff` - Blue (Primary, GPT-A)
- `#ff6b6b` - Red (Secondary, GPT-B)
- `#10b981` - Green (Tertiary, Host)
- `#f59e0b` - Amber (Quaternary)
- `#8b5cf6` - Purple (Quinary)

## References

- [Streamlit Theming Documentation](https://docs.streamlit.io/develop/concepts/configuration/theming)
- [Streamlit Theme Configuration Options](https://docs.streamlit.io/develop/concepts/configuration/theming-customize-colors-and-borders)
- [Streamlit Font Customization](https://docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts)

