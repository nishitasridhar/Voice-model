import asyncio
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from .sound import play_wav
from .config import settings
from .llm import GeminiClient
from .tts import CloudTTS   # ← important: imports tts.py on the main thread


LOG_PATH = Path(settings.output_dir) / "gui.log"


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


SYSTEM_PROMPT = "You are a concise, friendly assistant. Keep responses under 80 words unless asked."


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gemini (direct) → Cartesia TTS")
        self.geometry("780x560")

        # --------- UI ---------
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Gemini model:").pack(side="left")
        self.model_var = tk.StringVar(value=settings.default_model)
        ttk.Entry(top, textvariable=self.model_var, width=28).pack(side="left", padx=8)

        ttk.Label(top, text="Cartesia voice ID:").pack(side="left")
        self.voice_var = tk.StringVar(value=settings.default_cartesia_voice)
        ttk.Entry(top, textvariable=self.voice_var, width=40).pack(side="left", padx=8)

        mid = ttk.Frame(self, padding=12)
        mid.pack(fill="both", expand=True)

        ttk.Label(mid, text="Input text (what should Gemini answer?):").pack(anchor="w")
        self.txt = tk.Text(mid, height=12, wrap="word")
        self.txt.pack(fill="both", expand=True, pady=6)

        btns = ttk.Frame(self, padding=12)
        btns.pack(fill="x")
        ttk.Button(btns, text="Generate + Speak", command=self._start_generate).pack(side="left")
        ttk.Button(btns, text="Save only (no playback)", command=self._start_save_only).pack(side="left", padx=8)
        ttk.Button(btns, text="Clear", command=lambda: self.txt.delete("1.0", "end")).pack(side="left", padx=8)

        # status line
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(side="bottom", fill="x")

        # little toast area
        self.toast = tk.StringVar(value="")
        toast_lbl = ttk.Label(self, textvariable=self.toast, anchor="center", padding=6)
        toast_lbl.place(relx=0.5, rely=0.05, anchor="n")

        # show we actually created the window
        self.after(0, lambda: _log("Tk window initialized"))
        self.after(0, lambda: self.status.set("Ready."))

        # surface TK callback exceptions
        def _tk_ex_handler(exc, val, tb):
            try:
                messagebox.showerror("Unhandled error", f"{val}")
            finally:
                sys.__excepthook__(exc, val, tb)
        self.report_callback_exception = _tk_ex_handler  # type: ignore

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- UI helpers (always called on main thread) ---
    def _ui_set_status(self, text: str = "") -> None:
        self.after(0, self.status.set, text)
        self.after(0, lambda: _log(f"STATUS: {text}"))

    def _ui_error(self, title: str, msg: str) -> None:
        def _show():
            _log(f"ERROR: {title}: {msg}")
            messagebox.showerror(title, msg)
        self.after(0, _show)

    def _ui_offer_save_as(self, path: str) -> None:
        def _save_dialog():
            answer = messagebox.askyesno("Save As", "Do you want to choose a new filename?")
            if answer:
                new_path = filedialog.asksaveasfilename(
                    defaultextension=".wav",
                    filetypes=[("WAV audio", "*.wav"), ("All files", "*.*")]
                )
                if new_path:
                    from pathlib import Path
                    Path(new_path).write_bytes(Path(path).read_bytes())
        self.after(0, _save_dialog)

    def _show_toast(self, text: str, ms: int = 4000) -> None:
        def _set():
            self.toast.set(text)
            self.after(ms, lambda: self.toast.set(""))
        self.after(0, _set)
    # -------------------------------------------------

    def _start_generate(self):
        text = self.txt.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", "Type something first.")
            return
        self._spawn_worker(user_text=text, play=True)

    def _start_save_only(self):
        text = self.txt.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", "Type something first.")
            return
        self._spawn_worker(user_text=text, play=False)

    def _spawn_worker(self, user_text: str, play: bool):
        self._ui_set_status("Running Gemini → Cartesia TTS" + (" → play..." if play else " (save only)..."))
        _log("Spawning worker thread...")
        t = threading.Thread(target=self._run_job_sync, args=(user_text, play), name="tts-job", daemon=True)
        t.start()

    def _run_job_sync(self, user_text: str, play: bool):
        """
        Run the async pipeline in an isolated event loop via asyncio.run().
        Lazy-import heavy libs here to avoid any top-level side effects.
        """
        try:
            _log("Worker: starting asyncio.run")
            asyncio.run(self._run_pipeline(user_text, play))
            _log("Worker: asyncio.run finished")
        except Exception as e:
            self._ui_set_status("Error")
            self._ui_error("Error", str(e))

    async def _run_pipeline(self, user_text: str, play: bool):
        _log("Pipeline: start")
        # Lazy imports (inside worker) for safety
        from .llm import GeminiClient
        from .tts import CloudTTS
        from .sound import play_wav

        # 1) Gemini
        llm = GeminiClient(model=self.model_var.get())
        reply = await llm.chat(SYSTEM_PROMPT, user_text)
        _log(f"Pipeline: LLM reply length={len(reply)}")
        if not reply:
            raise RuntimeError("Empty response from Gemini.")

        # 2) TTS
        tts = CloudTTS(voice_id=self.voice_var.get())
        wav_path = await tts.synth_to_wav(reply)
        _log(f"Pipeline: TTS wav_path={wav_path}")

        # 3) Playback (in worker thread, not main)
        if play:
            _log("Pipeline: start playback")
            await asyncio.to_thread(play_wav, wav_path)
            _log("Pipeline: playback done")

        # 4) UI updates
        self._ui_offer_save_as(str(wav_path))
        self._ui_set_status(f"Done. File: {wav_path}")
        self._show_toast("✅ Finished — audio played & saved", 5000)
        _log("Pipeline: end")

    def _on_close(self):
        _log("WM_DELETE_WINDOW received — closing")
        self.destroy()
