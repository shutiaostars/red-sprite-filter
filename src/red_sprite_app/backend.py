from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .models import (
    CandidateReview,
    default_output_dir,
    export_confirmed_csv,
    load_candidates_csv,
    write_review_state,
)


APP_ROOT = Path(__file__).resolve().parent
WORK_ROOT = APP_ROOT.parent
DETECTOR = WORK_ROOT / "red_sprite_filter.py"
STATIC_ROOT = APP_ROOT / "static"
SUPPORTED_STATES = {"confirmed", "suspected", "false_positive", "unreviewed"}
CHOOSE_PATH_KINDS = {"video", "source-folder", "output-folder"}


def _default_tool_dirs() -> list[str]:
    """Tool/search directories, cross-platform, including bundled binaries.

    When packaged with PyInstaller the ffmpeg/ffprobe binaries land in
    ``sys._MEIPASS``; when run from source we look for a local ``bin/`` folder
    next to the executable. On Windows we also accept a conventional install
    location, and on macOS/Linux the usual Homebrew/system paths.
    """
    dirs: list[str] = []
    if getattr(sys, "_MEIPASS", None):
        dirs.append(sys._MEIPASS)
    exe_dir = Path(sys.executable).parent
    dirs.append(str(exe_dir / "bin"))
    dirs.append(str(exe_dir))
    if sys.platform == "win32":
        dirs.append(r"C:\ffmpeg\bin")
    else:
        dirs.extend(["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"])
    return dirs


def build_runtime_path(existing_path: str | None = None) -> str:
    parts: list[str] = []
    for path in _default_tool_dirs() + (existing_path or "").split(os.pathsep):
        if path and path not in parts:
            parts.append(path)
    return os.pathsep.join(parts)


os.environ["PATH"] = build_runtime_path(os.environ.get("PATH"))


class AppState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.process: subprocess.Popen[str] | None = None
        self.logs: list[str] = []
        self.last_output: Path | None = None
        self.last_returncode: int | None = None
        self.running = False

    def append_log(self, line: str) -> None:
        with self.lock:
            self.logs.append(line.rstrip())
            self.logs = self.logs[-500:]

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            return {
                "running": self.running,
                "logs": list(self.logs),
                "last_output": str(self.last_output) if self.last_output else "",
                "last_returncode": self.last_returncode,
            }


STATE = AppState()


def check_dependencies() -> dict[str, object]:
    deps = [
        {"name": "python", "ok": True, "detail": sys.executable},
        {"name": "ffmpeg", "ok": shutil.which("ffmpeg") is not None, "detail": shutil.which("ffmpeg") or "not found"},
        {"name": "ffprobe", "ok": shutil.which("ffprobe") is not None, "detail": shutil.which("ffprobe") or "not found"},
    ]
    for module_name, label in [("numpy", "numpy"), ("PIL", "Pillow")]:
        try:
            __import__(module_name)
            deps.append({"name": label, "ok": True, "detail": "available"})
        except Exception as exc:
            deps.append({"name": label, "ok": False, "detail": str(exc)})
    return {"ok": all(item["ok"] for item in deps), "dependencies": deps}


def build_scan_command(
    source: Path,
    output: Path,
    mode: str,
    max_candidates: int,
    min_score: float,
    min_red_pixels: int,
    pre_seconds: float,
    post_seconds: float,
) -> list[str]:
    return [
        sys.executable,
        str(DETECTOR),
        str(source),
        "--out",
        str(output),
        "--score-mode",
        mode,
        "--max-candidates",
        str(max_candidates),
        "--min-score",
        str(min_score),
        "--min-red-pixels",
        str(min_red_pixels),
        "--pre-seconds",
        str(pre_seconds),
        "--post-seconds",
        str(post_seconds),
    ]


def build_choose_path_script(kind: str) -> str:
    if kind == "video":
        return 'POSIX path of (choose file with prompt "选择视频文件")'
    if kind == "source-folder":
        return 'POSIX path of (choose folder with prompt "选择素材文件夹")'
    if kind == "output-folder":
        return 'POSIX path of (choose folder with prompt "选择输出目录")'
    raise ValueError(f"Unsupported chooser kind: {kind}")


def open_path(path: Path) -> None:
    """Open a file or folder with the OS default handler (cross-platform)."""
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def choose_path(kind: str) -> dict[str, object]:
    """Cross-platform file/folder picker.

    On macOS we keep the native osascript dialog. On Windows/Linux we fall back
    to a tkinter dialog so the HTTP endpoint still works outside the pywebview
    shell. (When running inside pywebview, the frontend prefers the native
    webview dialog exposed via ``JsApi.choose_path`` instead.)
    """
    if sys.platform == "darwin":
        script = build_choose_path_script(kind)
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return {"ok": False, "cancelled": True, "path": "", "error": proc.stderr.strip()}
        return {"ok": True, "cancelled": False, "path": proc.stdout.strip()}

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if kind == "video":
            path = filedialog.askopenfilename(
                title="选择视频文件",
                filetypes=[("视频文件", "*.mp4 *.mov *.m4v *.mts *.m2ts *.mkv *.avi"), ("所有文件", "*.*")],
            )
        elif kind == "source-folder":
            path = filedialog.askdirectory(title="选择素材文件夹")
        elif kind == "output-folder":
            path = filedialog.askdirectory(title="选择输出目录")
        else:
            root.destroy()
            return {"ok": False, "error": f"unknown chooser kind: {kind}"}
        root.destroy()
    except Exception as exc:  # pragma: no cover - GUI fallback path
        return {"ok": False, "cancelled": False, "path": "", "error": str(exc)}
    if not path:
        return {"ok": False, "cancelled": True, "path": ""}
    return {"ok": True, "cancelled": False, "path": path}


def _json_response(handler: BaseHTTPRequestHandler, payload: dict[str, object], status: int = 200) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


class _ScanLogWriter(io.TextIOBase):
    """Tee stdout into both the on-disk run log and the in-memory state log."""

    def __init__(self, log_file: "io.TextIOBase") -> None:
        self._log = log_file

    def write(self, s: str) -> int:
        if s:
            for line in s.splitlines():
                line = line.rstrip("\n")
                self._log.write(line + "\n")
                self._log.flush()
                STATE.append_log(line)
        return len(s)


def _run_detector_in_process(argv: list[str], log_file: "io.TextIOBase") -> int:
    """Run the detector module in-process.

    Used when frozen by PyInstaller, because ``sys.executable`` is then the
    bundled application (not a Python interpreter), so we cannot spawn it with
    ``red_sprite_filter.py`` as an argument the way we do in source mode.
    """
    import red_sprite_filter as detector

    saved_stdout = sys.stdout
    sys.stdout = _ScanLogWriter(log_file)
    try:
        return int(detector.main(argv) or 0)
    except Exception as exc:  # pragma: no cover - defensive
        STATE.append_log(f"ERROR: {exc}")
        return 1
    finally:
        sys.stdout = saved_stdout


def _run_scan(command: list[str], output: Path, settings: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "settings.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log_path = output / "run_log.txt"
    STATE.append_log("开始扫描")
    frozen = getattr(sys, "_MEIPASS", None) is not None
    with STATE.lock:
        STATE.running = True
        STATE.last_output = output
        STATE.last_returncode = None

    if frozen:
        # sys.executable is the bundled app, so run the detector module in-process.
        # command == [sys.executable, DETECTOR, ...]; drop the first two entries.
        argv = command[2:]
        with log_path.open("w", encoding="utf-8") as log:
            returncode = _run_detector_in_process(argv, log)
        with STATE.lock:
            STATE.running = False
            STATE.last_returncode = returncode
        STATE.append_log(f"扫描结束，退出码 {returncode}")
        return

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(WORK_ROOT),
        )
        with STATE.lock:
            STATE.process = process
            STATE.running = True
            STATE.last_output = output
            STATE.last_returncode = None
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            log.flush()
            STATE.append_log(line)
        returncode = process.wait()
    with STATE.lock:
        STATE.running = False
        STATE.process = None
        STATE.last_returncode = returncode
    STATE.append_log(f"扫描结束，退出码 {returncode}")


class RedSpriteHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        STATE.append_log(format % args)

    def do_GET(self) -> None:
        path = unquote(self.path.split("?", 1)[0])
        if path == "/health":
            _json_response(self, {"app": "红色精灵筛选器", **check_dependencies(), **STATE.snapshot()})
            return
        if path == "/results":
            output = self._requested_output()
            if output is None:
                _json_response(self, {"candidates": [], **STATE.snapshot()})
                return
            candidates = [candidate.__dict__ for candidate in load_candidates_csv(output / "candidates.csv")]
            _json_response(self, {"candidates": candidates, "output": str(output), **STATE.snapshot()})
            return
        if path.startswith("/media/"):
            self._serve_file(Path(path.removeprefix("/media/")))
            return
        self._serve_static("index.html" if path == "/" else path.lstrip("/"))

    def do_POST(self) -> None:
        if self.path == "/choose-path":
            payload = _read_json(self)
            kind = str(payload.get("kind", ""))
            if kind not in CHOOSE_PATH_KINDS:
                _json_response(self, {"ok": False, "error": "unknown chooser kind"}, status=400)
                return
            _json_response(self, choose_path(kind))
            return
        if self.path == "/scan":
            payload = _read_json(self)
            source = Path(str(payload["source"])).expanduser().resolve()
            output = Path(str(payload.get("output") or default_output_dir(source))).expanduser().resolve()
            mode = str(payload.get("mode") or "precision")
            settings = {
                "source": str(source),
                "output": str(output),
                "mode": mode,
                "max_candidates": int(payload.get("max_candidates", 24)),
                "min_score": float(payload.get("min_score", 0.8 if mode == "precision" else 0.012)),
                "min_red_pixels": int(payload.get("min_red_pixels", 8)),
                "pre_seconds": float(payload.get("pre_seconds", 1.0)),
                "post_seconds": float(payload.get("post_seconds", 2.0)),
            }
            command = build_scan_command(
                source,
                output,
                mode,
                int(settings["max_candidates"]),
                float(settings["min_score"]),
                int(settings["min_red_pixels"]),
                float(settings["pre_seconds"]),
                float(settings["post_seconds"]),
            )
            thread = threading.Thread(target=_run_scan, args=(command, output, settings), daemon=True)
            thread.start()
            _json_response(self, {"ok": True, "output": str(output), "command": command})
            return
        if self.path == "/cancel":
            with STATE.lock:
                process = STATE.process
            if process and process.poll() is None:
                process.terminate()
                STATE.append_log("已请求取消扫描")
            _json_response(self, {"ok": True})
            return
        if self.path == "/review-state":
            payload = _read_json(self)
            output = Path(str(payload["output"])).expanduser().resolve()
            reviews = [
                CandidateReview(candidate_id=str(item["candidate_id"]), state=str(item["state"]))
                for item in payload.get("reviews", [])
                if str(item.get("state")) in SUPPORTED_STATES
            ]
            review_path = write_review_state(output, reviews)
            confirmed_path = export_confirmed_csv(output, reviews)
            _json_response(self, {"ok": True, "review_state": str(review_path), "confirmed_csv": str(confirmed_path)})
            return
        if self.path == "/open-path":
            payload = _read_json(self)
            path = Path(str(payload["path"])).expanduser().resolve()
            open_path(path)
            _json_response(self, {"ok": True})
            return
        _json_response(self, {"ok": False, "error": "unknown endpoint"}, status=404)

    def _requested_output(self) -> Path | None:
        header = self.headers.get("X-Output-Dir")
        if header:
            return Path(header).expanduser().resolve()
        snapshot = STATE.snapshot()
        if snapshot.get("last_output"):
            return Path(str(snapshot["last_output"]))
        return None

    def _serve_static(self, relpath: str) -> None:
        path = (STATIC_ROOT / relpath).resolve()
        if not str(path).startswith(str(STATIC_ROOT.resolve())) or not path.exists():
            _json_response(self, {"ok": False, "error": "not found"}, status=404)
            return
        self._send_file(path)

    def _serve_file(self, relpath: Path) -> None:
        output = STATE.last_output
        if output is None:
            _json_response(self, {"ok": False, "error": "no output loaded"}, status=404)
            return
        path = (output / relpath).resolve()
        if not str(path).startswith(str(output.resolve())) or not path.exists():
            _json_response(self, {"ok": False, "error": "media not found"}, status=404)
            return
        self._send_file(path)

    def _send_file(self, path: Path) -> None:
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(host: str, port: int, open_browser: bool) -> None:
    server = ThreadingHTTPServer((host, port), RedSpriteHandler)
    url = f"http://{host}:{server.server_address[1]}"
    print(url, flush=True)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    server.serve_forever()


def make_server(host: str, port: int):
    server = ThreadingHTTPServer((host, port), RedSpriteHandler)
    url = f"http://{host}:{server.server_address[1]}"
    return server, url


def start_background(host: str = "127.0.0.1", port: int = 0):
    """Start the HTTP server in a daemon thread. Returns ``(server, url)``."""
    server, url = make_server(host, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(url, flush=True)
    return server, url


def shutdown() -> None:
    """Terminate any running scan subprocess (best effort)."""
    with STATE.lock:
        proc = STATE.process
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)
    serve(args.host, args.port, args.open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
