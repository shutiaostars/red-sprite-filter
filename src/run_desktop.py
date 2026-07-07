"""Top-level entry point for the desktop app (used by PyInstaller).

Importing through the package keeps ``red_sprite_app.desktop``'s relative
imports working inside the frozen executable.
"""

from red_sprite_app.desktop import main

if __name__ == "__main__":
    main()
