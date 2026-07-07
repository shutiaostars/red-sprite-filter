from __future__ import annotations

"""Cross-platform desktop launcher (Windows / macOS / Linux).

This replaces the macOS-only Swift shell (``native/RedSpriteFilterApp.swift``)
with a Python + pywebview window. pywebview uses the OS-native webview
(WebView2 / Edge on Windows, WebKit on macOS, GTK-WebKit on Linux), so the
same code drives a native window on every platform.

The Python backend (``backend``) is started in a background thread and served
over localhost; pywebview then loads that URL. File/folder picking is exposed
to the frontend through ``JsApi.choose_path`` so it uses a real native dialog
instead of the HTTP ``/choose-path`` fallback.
"""

import webview

from . import backend


class JsApi:
    """Methods exposed to the frontend via ``window.pywebview.api``."""

    def choose_path(self, kind: str) -> dict[str, object]:
        if not webview.windows:
            return {"ok": False, "error": "window not ready"}
        win = webview.windows[0]
        if kind == "video":
            result = win.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("视频文件 (*.mp4;*.mov;*.m4v;*.mts;*.m2ts;*.mkv;*.avi)",),
            )
        elif kind in ("source-folder", "output-folder"):
            result = win.create_file_dialog(webview.FOLDER_DIALOG)
        else:
            return {"ok": False, "error": f"unknown chooser kind: {kind}"}

        if not result:
            return {"ok": False, "cancelled": True, "path": ""}
        path = result[0] if isinstance(result, (list, tuple)) else result
        return {"ok": True, "cancelled": False, "path": str(path)}


def _on_closed() -> None:
    backend.shutdown()


def main() -> None:
    server, url = backend.start_background(host="127.0.0.1", port=0)
    api = JsApi()
    window = webview.create_window(
        "红色精灵筛选器",
        url,
        js_api=api,
        width=1320,
        height=860,
    )
    window.events.closed += _on_closed
    # create_window blocks until all windows are closed.
    backend.shutdown()


if __name__ == "__main__":
    main()
