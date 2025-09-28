from .config import settings
# ⬇️ add this line (keeps a reference unused; side-effect = plugin registers)
import livekit.plugins.cartesia as _cartesia  # noqa: F401
from .gui import App

def main():
    settings.validate()
    app = App()
    app.after(0, lambda: print("[main] Tk mainloop starting", flush=True))
    app.mainloop()
    print("[main] Tk mainloop ended", flush=True)

if __name__ == "__main__":
    main()
