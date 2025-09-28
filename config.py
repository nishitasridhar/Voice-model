import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # load .env if present

@dataclass
class Settings:
    # LLM (Gemini) via LiveKit Google plugin
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # Cartesia TTS
    cartesia_api_key: str = os.getenv("CARTESIA_API_KEY", "")
    default_cartesia_model: str = os.getenv("DEFAULT_CARTESIA_MODEL", "sonic-2")
    default_cartesia_voice: str = os.getenv("DEFAULT_CARTESIA_VOICE", "")

    # Misc
    output_dir: str = os.getenv("OUTPUT_DIR", "./out")
    default_model: str = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.0-flash-001")

    def validate(self):
        errors = []
        if not self.google_api_key:
            errors.append("Missing GOOGLE_API_KEY (Gemini).")
        if not self.cartesia_api_key:
            errors.append("Missing CARTESIA_API_KEY (Cartesia TTS).")
        out = Path(self.output_dir)
        try:
            out.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create OUTPUT_DIR ({self.output_dir}): {e}")
        if errors:
            raise RuntimeError(" | ".join(errors))

settings = Settings()
