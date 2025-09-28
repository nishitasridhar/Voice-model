import asyncio
from typing import Optional
import google.generativeai as genai
# from config import settings
from .config import settings

class GeminiClient:
    """
    Direct Gemini client using google-generativeai.
    Exposes an async .chat(system_prompt, user_text) that runs the blocking SDK in a thread.
    """

    def __init__(self, model: Optional[str] = None):
        self.model_name = model or settings.default_model
        # Configure once per process; safe to call multiple times.
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(self.model_name)

    def _sync_generate(self, system_prompt: str, user_text: str) -> str:
        """
        Blocking call to Gemini; wrapped by asyncio.to_thread in chat().
        We pass system_prompt via system_instruction when available.
        """
        try:
            # Preferred path: system_instruction param (supported in current SDKs)
            resp = self._model.generate_content(
                contents=user_text,
                system_instruction=system_prompt,
                safety_settings=None,  # use defaults; customize if needed
                generation_config={"temperature": 0.7},
            )
        except TypeError:
            # Fallback for older SDKs without system_instruction param:
            prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
            resp = self._model.generate_content(prompt)

        # .text contains the concatenated text across parts
        return (resp.text or "").strip()

    async def chat(self, system_prompt: str, user_text: str) -> str:
        return await asyncio.to_thread(self._sync_generate, system_prompt, user_text)
