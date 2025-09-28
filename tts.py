# tts.py
import time
from pathlib import Path
import contextlib
import aiohttp

from livekit.plugins import cartesia
from livekit.rtc import AudioFrame
from livekit.agents import utils as lk_utils

# from config import settings
from .config import settings


@contextlib.asynccontextmanager
async def _install_http_session():
    """
    Install our own aiohttp.ClientSession into LiveKit's http_context so that
    plugins (like Cartesia TTS) can call utils.http_context.http_session()
    even when we're not running inside an Agent worker.

    This handles multiple possible function names across agent versions:
      - use_http_session(session)   (context manager)
      - set_http_session(session)   (setter + clear_http_session())
      - set_current_http_session(session) (setter + clear_current_http_session())
    """
    session = aiohttp.ClientSession()

    http_ctx = lk_utils.http_context
    use_cm = getattr(http_ctx, "use_http_session", None)
    set_fn = getattr(http_ctx, "set_http_session", None) or getattr(http_ctx, "set_current_http_session", None)
    clear_fn = getattr(http_ctx, "clear_http_session", None) or getattr(http_ctx, "clear_current_http_session", None)

    try:
        if callable(use_cm):
            # Newer helpers: context manager provided by the SDK
            async with use_cm(session):
                yield
        elif callable(set_fn) and callable(clear_fn):
            # Older helpers: explicit set/clear
            set_fn(session)
            try:
                yield
            finally:
                try:
                    clear_fn()
                except Exception:
                    pass
        else:
            # Fall back: monkey-patch the context var accessor (last resort)
            # (We only do this if absolutely necessary.)
            orig = getattr(http_ctx, "http_session", None)
            if orig is None:
                await session.close()
                raise RuntimeError(
                    "LiveKit http_context API not recognized. Update livekit-agents to ~=1.2 "
                    "or provide a supported http_context helper."
                )

            def _return_ours():
                return session

            # Patch
            setattr(http_ctx, "http_session", _return_ours)
            try:
                yield
            finally:
                # Restore if possible
                try:
                    setattr(http_ctx, "http_session", orig)
                except Exception:
                    pass
    finally:
        await session.close()


class CloudTTS:
    """
    Cartesia TTS via LiveKit plugin.
    We are NOT running in an Agent worker, so we inject our own aiohttp session
    into http_context for the duration of the synth call.
    """

    def __init__(self, voice_id: str | None = None, model: str | None = None, language: str = "en"):
        self.voice_id = voice_id or settings.default_cartesia_voice
        self.model = model or settings.default_cartesia_model
        self.language = language

    async def synth_to_wav(self, text: str, out_dir: str | Path | None = None) -> Path:
        out_dir = Path(out_dir or settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"tts_{int(time.time())}.wav"
        out_path = out_dir / filename

        # Install our own client session into LiveKit's http_context for this call
        async with _install_http_session():
            tts = cartesia.TTS(
                model=self.model,
                voice=self.voice_id,
                language=self.language,
                # NOTE: no 'session=' kw here; the plugin will pull from http_context
            )

            stream = tts.synthesize(text)
            frame: AudioFrame = await stream.collect()
            out_path.write_bytes(frame.to_wav_bytes())

        return out_path
