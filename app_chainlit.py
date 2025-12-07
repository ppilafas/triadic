import chainlit as cl
import asyncio
import time
from typing import List, Dict, Optional, Any
import numpy as np

# Core modules
from stt import transcribe_audio, create_wav_buffer
from ai_api import stream_model_generator, index_uploaded_files, ModelGenerationError
from tts import tts_stream_to_bytes

# Import our improved modules
from config import (
    speaker_config, 
    model_config, 
    timing_config
)
from exceptions import TranscriptionError, FileIndexingError
from utils.logging_config import get_logger
from core.conversation import (
    get_next_speaker_key,
    get_next_speaker_display_name,
    calculate_turn_count,
)
from core.message_builder import build_prompt
from utils.chainlit_ui import (
    create_styled_message_html,
    create_on_air_badge,
    get_settings
)

# Initialize logging
from utils.logging_config import setup_logging
setup_logging()

# Initialize logger
logger = get_logger(__name__)

# --- Configuration ---
SPEAKER_PROFILES = speaker_config.PROFILES
VOICE_MAP = speaker_config.VOICE_MAP

# --- UI Helpers ---

async def update_ui_controls():
    """Update both commands and controls in one call."""
    await setup_commands()
    await refresh_controls()

# --- UI State Management ---

async def setup_commands():
    """Set up native Chainlit Commands for persistent live controls."""
    settings = get_settings()
    is_running = settings["auto_run"]
    has_started = cl.user_session.get("has_started", False)
    
    commands = []
    
    # Start/Pause Broadcast command
    if is_running:
        commands.append({
            "id": "pause_broadcast",
            "icon": "pause",
            "description": "Pause the broadcast",
            "button": True,
            "persistent": True
        })
    else:
        command_id = "resume_broadcast" if has_started else "start_broadcast"
        command_label = "Resume Broadcast" if has_started else "Start Broadcast"
        commands.append({
            "id": command_id,
            "icon": "play",
            "description": command_label,
            "button": True,
            "persistent": True
        })
    
    # Audio Toggle command
    sound_icon = "volume-2" if settings.get("tts_enabled", False) else "volume-x"
    sound_label = "Mute Audio" if settings.get("tts_enabled", False) else "Enable Audio"
    commands.append({
        "id": "toggle_audio",
        "icon": sound_icon,
        "description": sound_label,
        "button": True,
        "persistent": True
    })
    
    # Manual Next Turn (only when paused)
    if not is_running and has_started:
        commands.append({
            "id": "manual_turn",
            "icon": "skip-forward",
            "description": "Trigger next turn manually",
            "button": True,
            "persistent": True
        })
    
    try:
        await cl.context.emitter.set_commands(commands)
        logger.debug(f"Set {len(commands)} commands")
    except Exception as e:
        logger.warning(f"Failed to set commands: {e}")

async def refresh_controls(force_update: bool = False):
    """
    Updates the Studio Deck status display (controls are now handled by native commands).
    
    Args:
        force_update: If True, always create a new message. If False, only update if state changed.
    """
    settings = get_settings()
    history = cl.user_session.get("history", [])
    
    # Calculate statistics
    turn_count = calculate_turn_count(history)
    is_running = settings["auto_run"]
    has_started = cl.user_session.get("has_started", False)
    
    # Check if state has changed (only create new message if state changed or forced)
    last_state = cl.user_session.get("last_control_state", {})
    current_state = {
        "auto_run": is_running,
        "tts_enabled": settings.get("tts_enabled", False),
        "turn_count": turn_count
    }
    
    state_changed = last_state != current_state
    
    # Track all control message IDs to manage duplicates
    control_msg_ids = cl.user_session.get("control_msg_ids", [])
    old_msg_id = cl.user_session.get("control_msg_id")
    
    # Only create new Studio Deck if state changed or forced, or if we don't have one yet
    if not force_update and not state_changed and old_msg_id:
        # State hasn't changed, skip creating a new message
        return
    
    # Update last known state
    cl.user_session.set("last_control_state", current_state)
    
    # Determine next speaker display name
    if history:
        last_speaker_key = history[-1].get("author_key", "host")
        next_speaker = get_next_speaker_display_name(last_speaker_key)
    else:
        next_speaker = "GPT-A"
    
    # Build status HTML
    status_html_parts = []
    
    if is_running:
        status_html_parts.append('<span class="on-air-badge">🔴 ON AIR</span>')
        status_html_parts.append(f'<span style="color: #94a3b8; font-size: 0.85em; margin-left: 12px;">Next: {next_speaker} • Delay: {settings.get("auto_delay", 4)}s</span>')
    else:
        status_html_parts.append('<span style="color: #64748b; font-size: 0.85em; padding: 4px 12px; background: #1e293b; border-radius: 8px;">⏸️ Standby</span>')
    
    # Generate unique ID for this Studio Deck instance
    deck_id = int(time.time() * 1000)  # milliseconds timestamp
    
    # Build Studio Deck using improved native Chainlit structure
    studio_deck_html = f'''
    <div class="studio-deck" data-deck-id="{deck_id}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; gap: 20px;">
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
                    <strong style="font-size: 1.2em; color: #e2e8f0;">🎛️ Studio Deck</strong>
                    {"".join(status_html_parts)}
                </div>
                <div style="margin-top: 8px; color: #94a3b8; font-size: 0.85em; display: flex; align-items: center; gap: 8px;">
                    <span>💡</span>
                    <span>Use the command buttons above to control the broadcast</span>
                </div>
            </div>
            <div style="text-align: right; color: #94a3b8; font-size: 0.9em; min-width: 140px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px;">
                    <span>📊</span>
                    <span><strong style="color: #ff6b6b; font-size: 1.1em;">{turn_count}</strong> turns</span>
                </div>
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px;">
                    <span>🎯</span>
                    <span>Model: <strong style="color: #60a5fa;">{settings.get("model_name", "gpt-5-mini").replace("gpt-", "").upper()}</strong></span>
                </div>
            </div>
        </div>
    </div>
    '''

    # Use native Chainlit Message with System author for better styling
    msg = await cl.Message(
        content=studio_deck_html,
        author="System"
    ).send()
    
    # Track this message ID for duplicate prevention
    if old_msg_id and old_msg_id not in control_msg_ids:
        control_msg_ids.append(old_msg_id)
    control_msg_ids.append(msg.id)
    # Keep only the last 3 message IDs to avoid memory issues
    control_msg_ids = control_msg_ids[-3:]
    
    cl.user_session.set("control_msg_id", msg.id)
    cl.user_session.set("control_msg_ids", control_msg_ids)

# --- Task Management ---

def cancel_scheduled_turn():
    task = cl.user_session.get("schedule_task")
    if task and not task.done(): task.cancel()
    cl.user_session.set("schedule_task", None)

async def schedule_next_turn() -> None:
    """Schedule the next turn after a delay."""
    settings = get_settings()
    delay = float(settings.get("auto_delay", timing_config.DEFAULT_AUTO_DELAY))
    try:
        await asyncio.sleep(delay)
        if get_settings()["auto_run"]:
            await execute_turn()
    except asyncio.CancelledError:
        logger.debug("Scheduled turn cancelled")
        pass

# --- Core Execution ---

async def execute_turn() -> None:
    """
    Execute one turn of the conversation.
    Generates a response from the next speaker and updates history.
    """
    settings = get_settings()
    history = cl.user_session.get("history", [])
    
    # Input validation
    if not history:
        logger.warning("No conversation history found")
        error_html = create_styled_message_html("⚠️ **No conversation history found.**", "system")
        await cl.Message(content=error_html, author="System").send()
        return
    
    try:
        # build_prompt is now synchronous, no await needed
        prompt, next_speaker_key = build_prompt(history)
        speaker_info = SPEAKER_PROFILES[next_speaker_key]
        
        effort = settings.get('reasoning_effort', model_config.DEFAULT_REASONING_EFFORT).title()
        step_label = f"{speaker_info['name']} • {effort} Effort"
        
        logger.info(f"Executing turn for {speaker_info['name']} with {effort} effort")
        
        # Add ON AIR badge if podcast is running
        on_air_html = ""
        if settings["auto_run"]:
            on_air_html = create_on_air_badge(speaker_info['name'], effort)
        
        # Use native Chainlit Step with better metadata
        async with cl.Step(
            name=step_label,
            type="llm"
        ) as step:
            step.input = f"Processing with {settings.get('model_name', 'gpt-5-mini')}..."
            
            # Create message for streaming
            msg = cl.Message(
                author=speaker_info["name"],
                content=""
            )
            full_response = ""
            
            try:
            token_gen = stream_model_generator(prompt, config=settings)
                # Stream tokens in real-time (plain text for streaming)
            for token in token_gen:
                await msg.stream_token(token)
                full_response += token
            
            except ModelGenerationError as e:
                logger.error(f"Model generation failed: {e}", exc_info=True)
                error_html = create_styled_message_html(
                    f"⚠️ **AI Generation Error:** {str(e)}\n\nPlease try again or adjust your settings.",
                    "system"
                )
                await cl.Message(
                    content=error_html,
                    author="System"
                ).send()
                raise
            
            step.output = full_response

            # After streaming completes, update message with styled content
            styled_content = create_styled_message_html(full_response, next_speaker_key)
            final_content = on_air_html + styled_content if on_air_html else styled_content
            msg.content = final_content
        
        # Send message first so text is visible immediately
        await msg.send()
        
        # Generate TTS in parallel (if enabled) and add audio when ready
        # Note: Chainlit's Audio element requires complete bytes, so we can't stream chunks
        # but we generate TTS in parallel to minimize delay
        if settings["tts_enabled"]:
            voice = VOICE_MAP.get(next_speaker_key, "alloy")
            # Generate TTS asynchronously - runs in background after message is sent
            async def generate_and_add_tts():
                try:
                    logger.debug(f"Starting TTS generation for {speaker_info['name']} (voice: {voice})")
                    # Use make_async to run the blocking TTS streaming call in a thread pool
                    # The TTS API streams chunks internally, but we collect them all before sending
                    # (Chainlit's Audio element requires complete bytes for playback)
                    audio_bytes = await cl.make_async(tts_stream_to_bytes)(full_response, voice=voice)
            if audio_bytes:
                        # Create audio element without autoplay - will be hidden via CSS, triggered by speaker icon
                        audio_element = cl.Audio(
                            name=f"voice_{speaker_info['name']}.mp3",
                            content=audio_bytes,
                            display="inline",  # Must be valid Chainlit value, we'll hide with CSS
                            auto_play=False
                        )
                        
                        # Add audio element to message (hidden)
                        msg.elements = [audio_element]
                        
                        # Add speaker icon to message content for on-demand playback
                        # Use a simple emoji icon that will be made clickable via JavaScript
                        speaker_icon_html = f'<span class="speaker-icon" data-audio-name="voice_{speaker_info["name"]}.mp3" style="cursor: pointer; margin-left: 8px; font-size: 1.2em; vertical-align: middle; user-select: none;" title="Click to play audio">🔊</span>'
                        
                        # Update message content to include speaker icon at the end
                        current_content = msg.content
                        msg.content = current_content + speaker_icon_html
            await msg.update()
                        
                        logger.info(f"TTS audio added for {speaker_info['name']}: {len(audio_bytes)} bytes (on-demand playback)")
                    else:
                        logger.warning(f"TTS generation returned empty bytes for {speaker_info['name']}")
                except Exception as e:
                    logger.warning(f"TTS generation failed for {speaker_info['name']}: {e}", exc_info=True)
                    # Continue without audio - don't fail the whole turn
            
            # Start TTS generation in background (non-blocking)
            # Audio will appear when ready via msg.update()
            asyncio.create_task(generate_and_add_tts())

        history.append({"author": speaker_info["name"], "author_key": next_speaker_key, "content": full_response})
        cl.user_session.set("history", history)
        
        logger.info(f"Turn completed: {speaker_info['name']} responded with {len(full_response)} characters")
        
        if settings["auto_run"]:
            task = asyncio.create_task(schedule_next_turn())
            cl.user_session.set("schedule_task", task)
            # Update controls after turn completes
            await refresh_controls(force_update=False)
            await setup_commands()  # Keep separate here to avoid unnecessary refresh
            
    except ModelGenerationError:
        # Already handled above
        settings["auto_run"] = False
        cl.user_session.set("settings", settings)
        await update_ui_controls()
    except Exception as e:
        logger.error("Unexpected error in execute_turn", exc_info=True)
        error_html = create_styled_message_html(
            "⚠️ **System Error:** An unexpected error occurred. Please check the logs.",
            "system"
        )
        await cl.Message(content=error_html, author="System").send()
        settings["auto_run"] = False
        cl.user_session.set("settings", settings)
        await update_ui_controls()

# --- Lifecycle Hooks ---

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Start Podcast", message="Let's start the show!", icon="/public/play.svg"),
        cl.Starter(label="Debug Mode", message="Run a diagnostic check.", icon="/public/bug.svg")
    ]

@cl.on_chat_start
async def start() -> None:
    """Initialize chat session with settings and welcome message."""
    logger.info("New chat session started")
    
    # Inject JavaScript to make speaker icons clickable for on-demand audio playback
    audio_click_handler = '''
    <script>
    (function() {
        if (window.speakerIconHandlerInitialized) return;
        window.speakerIconHandlerInitialized = true;
        
        function setupSpeakerIcon(icon) {
            if (icon.dataset.setup) return;
            icon.dataset.setup = 'true';
            
            icon.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const audioName = this.dataset.audioName;
                if (!audioName) return;
                
                // Find the audio element with matching name
                const audioElements = document.querySelectorAll('audio');
                const targetAudio = Array.from(audioElements).find(a => {
                    const source = a.querySelector('source');
                    return source && source.src.includes(audioName);
                });
                
                if (targetAudio) {
                    // Stop all other playing audio
                    audioElements.forEach(a => {
                        if (a !== targetAudio && !a.paused) {
                            a.pause();
                            a.currentTime = 0;
                        }
                    });
                    
                    // Toggle play/pause for this audio
                    if (targetAudio.paused) {
                        targetAudio.play();
                        this.textContent = '⏸️'; // Change to pause icon
                    } else {
                        targetAudio.pause();
                        this.textContent = '🔊'; // Change back to play icon
                    }
                    
                    // Update icon when audio ends
                    targetAudio.onended = () => {
                        this.textContent = '🔊';
                    };
                }
            });
        }
        
        // Set up existing speaker icons
        document.querySelectorAll('.speaker-icon').forEach(setupSpeakerIcon);
        
        // Observe for new speaker icons
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        if (node.classList && node.classList.contains('speaker-icon')) {
                            setupSpeakerIcon(node);
                        } else if (node.querySelectorAll) {
                            node.querySelectorAll('.speaker-icon').forEach(setupSpeakerIcon);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    '''
    
    # Send the click handler script as a hidden system message
    await cl.Message(content=audio_click_handler, author="System").send()
    
    # Set up native Chainlit Commands for persistent controls
    await setup_commands()
    
    # Settings Panel
    settings = await cl.ChatSettings([
        cl.input_widget.Select(
            id="model_name", 
            label="Model", 
            values=model_config.ALLOWED_MODELS, 
            initial_index=0 if model_config.DEFAULT_MODEL in model_config.ALLOWED_MODELS else 0
        ),
        cl.input_widget.Select(
            id="reasoning_effort", 
            label="Reasoning", 
            values=model_config.ALLOWED_EFFORT_LEVELS, 
            initial_index=model_config.ALLOWED_EFFORT_LEVELS.index(model_config.DEFAULT_REASONING_EFFORT) if model_config.DEFAULT_REASONING_EFFORT in model_config.ALLOWED_EFFORT_LEVELS else 1
        ),
        cl.input_widget.Switch(id="auto_run", label="Auto-Run Podcast", initial=False),
        cl.input_widget.Slider(
            id="auto_delay", 
            label="Delay (sec)", 
            min=int(timing_config.MIN_AUTO_DELAY), 
            max=int(timing_config.MAX_AUTO_DELAY), 
            initial=int(timing_config.DEFAULT_AUTO_DELAY)
        ),
        cl.input_widget.Switch(id="tts_enabled", label="Enable TTS", initial=False),
    ]).send()
    
    # Session Initialization
    cl.user_session.set("settings", settings)
    cl.user_session.set("history", [{"author": "System", "author_key": "host", "content": "Triadic System Online."}])
    cl.user_session.set("uploaded_file_index", {})
    cl.user_session.set("vector_store_id", None)
    cl.user_session.set("has_started", False)
    
    # [SHOWCASE UI] Rich Welcome Message using native Chainlit markdown
    welcome_content = """# 🎙️ Triadic Studio

    **GPT-5.1 Self-Dialogue Monolith**
    
    Welcome to the showcase. This system allows two AI personas to discuss any topic, grounded in your documents.
    
## 🚀 How to use:

    1. **Upload a PDF:** Drag & drop a book or report to index it.
2. **Start the Show:** Click ▶️ Start Podcast using the command buttons above.
    3. **Interject:** Type or use the Microphone to interrupt them live.

---
*Use the Studio Deck below to monitor the conversation and control the broadcast.*
"""
    
    # Use native Chainlit Message with markdown for better rendering
    await cl.Message(
        content=welcome_content,
        author="System"
    ).send()
    
    await refresh_controls()

@cl.on_settings_update
async def update_settings(settings):
    cl.user_session.set("settings", settings)
    await update_ui_controls()
    
    if settings["auto_run"]:
        cl.user_session.set("has_started", True)
        await execute_turn()
    else:
        cancel_scheduled_turn()

# --- Audio Hooks (WAV Buffering) ---

@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_chunks", [])
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk):
    if chunk.data:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        chunks = cl.user_session.get("audio_chunks")
        if chunks is None:
            chunks = []
            cl.user_session.set("audio_chunks", chunks)
        chunks.append(audio_chunk)

@cl.on_audio_end
async def on_audio_end() -> None:
    """Handle audio recording end, transcribe and process."""
    chunks = cl.user_session.get("audio_chunks")
    if not chunks:
        logger.warning("Audio end event but no chunks found")
        return
    
    try:
    # Create valid WAV in memory
        from config import audio_config
        wav_buffer = await cl.make_async(create_wav_buffer)(chunks, sample_rate=audio_config.SAMPLE_RATE)
    
    if wav_buffer:
        # Transcribe
            try:
        text = await cl.make_async(transcribe_audio)(wav_buffer)
            except TranscriptionError as e:
                logger.error(f"Transcription failed: {e}", exc_info=True)
                error_html = create_styled_message_html(
                    "⚠️ **Audio Error:** Could not transcribe your voice input. Please try again.",
                    "system"
                )
                await cl.Message(content=error_html, author="System").send()
                return
        
        if text:
                logger.info(f"Transcribed audio: {len(text)} characters")
                # Use styled message for host input
                styled_text = create_styled_message_html(text, "host")
                msg = cl.Message(author="Host", content=styled_text, type="user_message")
            await msg.send()
            
            history = cl.user_session.get("history")
            history.append({"author": "Host", "author_key": "host", "content": text})
            cl.user_session.set("history", history)
            
            cancel_scheduled_turn()
            await execute_turn()
            else:
                logger.warning("Transcription returned empty text")
    except Exception as e:
        logger.error(f"Error processing audio end: {e}", exc_info=True)
        error_html = create_styled_message_html(
            "⚠️ **Audio Processing Error:** An error occurred processing your audio.",
            "system"
        )
        await cl.Message(content=error_html, author="System").send()

# --- Shared Command/Action Handlers ---

async def handle_start_broadcast():
    """Shared handler for starting/resuming broadcast."""
    settings = get_settings()
    settings["auto_run"] = True
    cl.user_session.set("has_started", True)
    cl.user_session.set("settings", settings)
    
    await update_ui_controls()
    
    # Enhanced broadcast started message
    delay = settings.get("auto_delay", 4)
    model = settings.get("model_name", "gpt-5-mini").replace("gpt-", "").upper()
    effort = settings.get("reasoning_effort", "low").title()
    
    broadcast_html = create_styled_message_html(
        f"🎙️ **Broadcast Started**\n\n"
        f"📡 Model: {model} • Effort: {effort}\n"
        f"⏱️ Turn Delay: {delay}s\n"
        f"🔊 TTS: {'Enabled' if settings.get('tts_enabled') else 'Disabled'}",
        "system"
    )
    await cl.Message(content=broadcast_html, author="System").send()
    
    # execute_turn will call refresh_controls at the end, so no need to call it here
    await execute_turn()

async def handle_pause_broadcast():
    """Shared handler for pausing broadcast."""
    settings = get_settings()
    settings["auto_run"] = False
    cl.user_session.set("settings", settings)
    cancel_scheduled_turn()
    
    await update_ui_controls()
    
    # Enhanced pause message with statistics
    history = cl.user_session.get("history", [])
    turn_count = calculate_turn_count(history)
    
    paused_html = create_styled_message_html(
        f"⏸️ **Broadcast Paused**\n\n"
        f"📊 Total Turns: {turn_count}",
        "system"
    )
    await cl.Message(content=paused_html, author="System").send()

async def handle_toggle_audio():
    """Shared handler for toggling audio."""
    settings = get_settings()
    settings["tts_enabled"] = not settings.get("tts_enabled", False)
    cl.user_session.set("settings", settings)
    
    await update_ui_controls()
    
    label = "Sound ON" if settings["tts_enabled"] else "Sound OFF"
    icon = "🔊" if settings["tts_enabled"] else "🔇"
    sound_html = create_styled_message_html(f"{icon} **{label}**", "system")
    await cl.Message(content=sound_html, author="System").send()

async def handle_manual_turn():
    """Shared handler for manual turn trigger."""
    settings = get_settings()
    if settings["auto_run"]:
        return  # Shouldn't happen, but guard against it
    
    history = cl.user_session.get("history", [])
    if not history:
        error_html = create_styled_message_html(
            "⚠️ **No conversation history.** Start the broadcast first or send a message.",
            "system"
        )
        await cl.Message(content=error_html, author="System").send()
        await update_ui_controls()
        return
    
    await execute_turn()
    await refresh_controls()  # execute_turn already updates controls, but refresh for consistency

# --- Action Handlers (Legacy - for backward compatibility) ---

@cl.action_callback("toggle_auto")
async def on_auto_toggle(action):
    """Handle broadcast start/stop (legacy action callback)."""
    val = action.payload.get("value", "off")
    if val == "on":
        await handle_start_broadcast()
    else:
        await handle_pause_broadcast()

@cl.action_callback("manual_turn")
async def on_manual_turn(action):
    """Manually trigger the next turn (legacy action callback)."""
    await handle_manual_turn()

@cl.action_callback("toggle_audio")
async def on_audio_toggle(action):
    """Handle audio toggle (legacy action callback)."""
    await handle_toggle_audio()

# --- Message Handler ---

@cl.on_message
async def on_message(msg: cl.Message) -> None:
    """Handle incoming messages (text or file uploads)."""
    # Handle commands (native Chainlit Commands)
    if msg.command:
        if msg.command == "start_broadcast" or msg.command == "resume_broadcast":
            await handle_start_broadcast()
            return
        elif msg.command == "pause_broadcast":
            await handle_pause_broadcast()
            return
        elif msg.command == "toggle_audio":
            await handle_toggle_audio()
            return
        elif msg.command == "manual_turn":
            cancel_scheduled_turn()
            await handle_manual_turn()
            return
    
    cancel_scheduled_turn()
    
    # RAG Indexing
    if msg.elements:
        files = [el for el in msg.elements if "file" in el.mime or "pdf" in el.mime or "text" in el.mime]
        if files:
            # Use native Chainlit Step with better metadata
            async with cl.Step(
                name="📚 Knowledge Base",
                type="tool"
            ) as step:
                step.input = f"Processing {len(files)} document(s) for RAG indexing..."
                try:
                    # Wrap blocking I/O in async executor to avoid blocking event loop
                    await cl.make_async(index_uploaded_files)(files, session_store=cl.user_session)
                    step.output = f"✅ Successfully indexed {len(files)} file(s). Vector store updated."
                    logger.info(f"Successfully indexed {len(files)} files")
                    # Use native markdown for better formatting
                    await cl.Message(
                        content=f"✅ **Indexed {len(files)} file(s).**\n\nYour documents are now part of the knowledge base.",
                        author="System"
                    ).send()
                except FileIndexingError as e:
                    logger.error(f"File indexing failed: {e}", exc_info=True)
                    step.output = f"Error: {str(e)}"
                    error_html = create_styled_message_html(
                        f"⚠️ **Indexing Error:** Failed to index files. {str(e)}",
                        "system"
                    )
                    await cl.Message(content=error_html, author="System").send()

    # Text Logic
    if msg.content:
        logger.info(f"Received text message: {len(msg.content)} characters")
        # Store original content for history
        original_content = msg.content
        
        # Display with styled bubble
        styled_content = create_styled_message_html(original_content, "host")
        display_msg = cl.Message(author="Host", content=styled_content, type="user_message")
        await display_msg.send()
        
        history = cl.user_session.get("history")
        history.append({"author": "Host", "author_key": "host", "content": original_content})
        cl.user_session.set("history", history)
        
        await execute_turn()