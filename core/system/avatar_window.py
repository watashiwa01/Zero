import os
import webview

_avatar_instance = None

class AvatarWindow:
    def __init__(self):
        global _avatar_instance
        _avatar_instance = self
        self.window = None

    def create(self):
        # Locate absolute path to the local avatar.html file
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar.html")
        
        # Dimensions for the desktop hologram widget
        width, height = 300, 300
        x, y = 100, 100
        
        try:
            screens = webview.screens
            if screens:
                primary = screens[0]
                # Default position: bottom-right corner of primary screen
                x = primary.width - width - 30
                y = primary.height - height - 80
        except Exception:
            pass

        self.window = webview.create_window(
            title="Zero Hologram",
            url=html_path,
            width=width,
            height=height,
            x=x,
            y=y,
            frameless=True,       # Frameless/no borders
            transparent=True,     # Click-through transparent backing
            on_top=True           # Floats on top of all windows
        )

    def set_state(self, state):
        if self.window:
            try:
                # Call the Three.js state function in JS
                self.window.evaluate_js(f"if (window.setAvatarState) {{ window.setAvatarState('{state}'); }}")
            except Exception:
                pass

def set_avatar_state(state):
    """
    Global thread-safe function to update the 3D hologram's animation state.
    Valid states: 'idle', 'listening', 'thinking', 'speaking'
    """
    global _avatar_instance
    if _avatar_instance:
        _avatar_instance.set_state(state)

def start_avatar_gui(setup_callback=None):
    """
    Starts the webview window loop. Blocks the main thread.
    Exits gracefully when the window is closed.
    """
    avatar = AvatarWindow()
    avatar.create()
    webview.start(setup_callback)
