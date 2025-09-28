# app/sound.py
from pathlib import Path

def play_wav(path: str | Path):
    """
    Play a WAV file. Tries simpleaudio; falls back to winsound on Windows.
    """
    p = str(path)
    try:
        import simpleaudio as sa
        wave_obj = sa.WaveObject.from_wave_file(p)
        play_obj = wave_obj.play()
        play_obj.wait_done()
        return
    except Exception:
        pass

    # Fallback for Windows if simpleaudio isn't available
    try:
        import winsound
        winsound.PlaySound(p, winsound.SND_FILENAME)
    except Exception as e:
        raise RuntimeError(f"Failed to play audio: {e}") from e
