"""Speech-to-text helpers for voice chatbot input."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
import shutil

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


def _get_transcription_config() -> tuple[str, str, str, str | None]:
    """Read transcription configuration from environment at runtime."""
    api_key = os.getenv("TRANSCRIPTION_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("TRANSCRIPTION_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")
    language = os.getenv("TRANSCRIPTION_LANGUAGE") or None
    return api_key, base_url, model, language


# Optional local Whisper support (runs locally, free but requires CPU/GPU and ffmpeg)
try:
    import whisper  # type: ignore
    _local_whisper_available = True
    _local_whisper_model = None
except Exception:
    whisper = None  # type: ignore
    _local_whisper_available = False
    _local_whisper_model = None


def _load_local_whisper(model_name: str = "small"):
    """Load local whisper model lazily."""
    global _local_whisper_model
    if not _local_whisper_available:
        raise RuntimeError("Local Whisper is not installed")
    if _local_whisper_model is None:
        _local_whisper_model = whisper.load_model(model_name)
    return _local_whisper_model


def is_transcription_configured() -> bool:
    """Return True when voice transcription has enough configuration to run."""
    api_key, _, _, _ = _get_transcription_config()
    return bool(api_key) or bool(_local_whisper_available)


def transcribe_audio_bytes(filename: str, audio_bytes: bytes) -> str:
    """Transcribe an uploaded audio file using an OpenAI-compatible API."""
    api_key, base_url, model, language = _get_transcription_config()

    if not is_transcription_configured():
        raise RuntimeError(
            "Voice transcription is not configured. Set TRANSCRIPTION_API_KEY or OPENAI_API_KEY."
        )

    suffix = Path(filename or "voice-input.webm").suffix or ".webm"
    # Log runtime transcription configuration (without secret) for debugging
    print(f"DEBUG: Transcription model={model}, base_url={base_url}, language={language}")
    client = OpenAI(api_key=api_key, base_url=base_url)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        # If local Whisper is available, try local transcription first (cost-free)
        if _local_whisper_available:
            try:
                # Ensure ffmpeg is available to the process; allow override via FFMPEG_PATH env var
                ffmpeg_path = shutil.which("ffmpeg")
                print(f"DEBUG: ffmpeg found at: {ffmpeg_path}")
                if not ffmpeg_path:
                    env_ffmpeg = os.getenv("FFMPEG_PATH")
                    if env_ffmpeg:
                        os.environ["PATH"] = env_ffmpeg + os.pathsep + os.environ.get("PATH", "")
                        ffmpeg_path = shutil.which("ffmpeg")
                        print(f"DEBUG: After prepending FFMPEG_PATH, ffmpeg found at: {ffmpeg_path}")

                local_model_name = os.getenv("WHISPER_LOCAL_MODEL", "small")
                local_model = _load_local_whisper(local_model_name)
                # Preprocess audio with ffmpeg to 16kHz mono WAV for better accuracy
                converted_path = temp_path + ".converted.wav"
                try:
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        temp_path,
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        converted_path,
                    ]
                    import subprocess

                    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    audio_for_transcription = converted_path
                except Exception as conv_exc:
                    print(f"WARNING: ffmpeg preprocessing failed: {repr(conv_exc)}; falling back to original file")
                    audio_for_transcription = temp_path

                if language:
                    result = local_model.transcribe(audio_for_transcription, language=language)
                else:
                    result = local_model.transcribe(audio_for_transcription)
                # remove converted file if created
                try:
                    if audio_for_transcription != temp_path and os.path.exists(audio_for_transcription):
                        os.remove(audio_for_transcription)
                except Exception:
                    pass

                text = (result.get("text") or "").strip()
                if text:
                    print("DEBUG: Transcribed locally with Whisper")
                    return text
                else:
                    print("WARNING: Local Whisper returned empty transcription")
                    # If there's no remote API key configured, fail fast with an actionable message
                    if not api_key or not str(api_key).strip():
                        raise RuntimeError(
                            "Local Whisper returned an empty transcription and no remote TRANSCRIPTION_API_KEY is configured. "
                            "Improve audio quality or set TRANSCRIPTION_API_KEY to enable remote transcription fallback."
                        )
                    print("Falling back to remote API because TRANSCRIPTION_API_KEY is configured")
            except Exception as loc_exc:
                print(f"ERROR: Local Whisper transcription failed: {repr(loc_exc)}")
                # If there's no remote API key configured, fail fast with actionable message
                if not api_key:
                    raise RuntimeError(
                        "Local Whisper transcription failed (ffmpeg may be missing)."
                        " Install ffmpeg and ensure it's on PATH, or set TRANSCRIPTION_API_KEY to enable remote transcription."
                    ) from loc_exc
                print("Falling back to remote API because TRANSCRIPTION_API_KEY is configured")

        # Fallback to remote OpenAI-compatible transcription
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language,
            )

        text = (getattr(transcription, "text", None) or "").strip()
        if not text:
            raise RuntimeError("Audio transcription returned an empty result.")

        return text
    except Exception as exc:
        # Provide more details for debugging while avoiding leaking secrets
        err_msg = f"Voice transcription failed: {repr(exc)}"
        print("ERROR in transcribe_audio_bytes:", err_msg)
        raise RuntimeError(err_msg) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)