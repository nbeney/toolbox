#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pillow>=11.0.0",
#   "qrcode[pil]>=8.0",
#   "rich>=14.0.0",
#   "typer>=0.26.7",
# ]
# ///

"""
QR Code Air-Gap Transfer Tool

Transfer files across an air-gap using a sequence of QR codes.

Actions:
  send     - Read a file and display a sequence of QR codes.
  receive  - Scan QR codes (via webcam or screenshots) to recreate the file.
"""

from __future__ import annotations

import base64
import json
import math
import os
import subprocess
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import qrcode
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

app = typer.Typer(help="Transfer files across an air-gap using QR codes.")
console = Console()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CHUNK_SIZE = 800  # raw bytes per chunk before base64 encoding
IMAGE_BORDER = 4  # modules of white quiet zone

SCREENSHOT_POLL_INTERVAL = 0.5  # seconds between scrot + zbarimg polls
WEBCAM_POLL_INTERVAL = 0.1  # seconds between webcam frame grabs

# Extra pause after opening the viewer so it has time to render before
# the receive side starts scanning.
VIEWER_OPEN_DELAY = 0.5


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReceiveMode(str, Enum):
    screenshot = "screenshot"
    webcam = "webcam"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_chunk_payload(
    index: int,
    total: int,
    filename: str,
    raw_chunk: bytes,
) -> str:
    """Return the JSON string to encode into a single QR code."""
    return json.dumps(
        {
            "i": index,
            "n": total,
            "name": filename,
            "data": base64.b64encode(raw_chunk).decode(),
        },
        separators=(",", ":"),
    )


def _parse_chunk_payload(raw: str) -> dict | None:
    """Parse and validate a QR payload. Returns None if invalid."""
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not all(k in obj for k in ("i", "n", "name", "data")):
        return None
    return obj


def _decode_qr_from_screen(screenshot_path: Path) -> str | None:
    """Take a screenshot with scrot and decode QR codes with zbarimg.

    Returns the decoded QR string, or None if no QR found.
    """
    # Remove any previous screenshot to avoid stale data.
    screenshot_path.unlink(missing_ok=True)

    # Capture the screen to a file.
    result = subprocess.run(
        ["scrot", str(screenshot_path)],
        capture_output=True,
    )
    if result.returncode != 0:
        return None

    # Verify the file was actually written.
    if not screenshot_path.exists():
        return None

    # Decode any QR codes in the screenshot.
    result = subprocess.run(
        [
            "zbarimg",
            "--raw",
            "--quiet",
            "-Sdisable",
            "-Sqrcode.enable",
            str(screenshot_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None

    # zbarimg may return multiple codes separated by newlines; take the first.
    return result.stdout.strip().split("\n")[0]


def _decode_qr_from_webcam_frame(frame) -> str | None:
    """Decode a QR code from an OpenCV frame (numpy array).

    Falls back to writing to a temp file + zbarimg if cv2 detector fails.
    """

    import cv2

    # Try OpenCV detector first (faster than writing to disk).
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(frame)
    if data:
        return data

    # Fallback: write frame to PNG and use zbarimg.
    tmp = Path(tempfile.gettempdir()) / "qrtransfer_webcam_frame.png"
    cv2.imwrite(str(tmp), frame)
    result = subprocess.run(
        ["zbarimg", "--raw", "--quiet", "-Sdisable", "-Sqrcode.enable", str(tmp)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip().split("\n")[0]


# ---------------------------------------------------------------------------
# Send helpers
# ---------------------------------------------------------------------------


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


# Target QR window size in pixels. The QR is rendered natively at this size
# (by choosing box_size accordingly) so there is NO resize step — fractional
# pixel boundaries would corrupt the module grid and break decoding.
QR_WINDOW_SIZE = 600


class _QRWindow:
    """A small tkinter window that displays QR code images in-process.

    Runs the Tk event loop in a background thread so the main thread can
    drive navigation without blocking. Call show(path) to swap the image,
    close() to destroy the window.
    """

    def __init__(self) -> None:
        import queue
        import threading
        import tkinter as tk
        from PIL import Image, ImageTk  # noqa: F401 — imported for type use below

        self._queue: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        self._tk_ref = None  # keep PhotoImage alive

        def _run() -> None:
            root = tk.Tk()
            root.title("QR Transfer")
            root.resizable(False, False)
            # Remove window decorations that might interfere with scanning.
            root.configure(bg="white")

            label = tk.Label(root, bg="white", bd=0)
            label.pack()

            self._root = root
            self._label = label
            self._ready.set()

            def _poll() -> None:
                try:
                    while True:
                        item = self._queue.get_nowait()
                        if item is None:
                            root.destroy()
                            return
                        # item is a PIL Image
                        photo = ImageTk.PhotoImage(item)
                        self._tk_ref = photo  # prevent GC
                        label.configure(image=photo)
                        root.geometry(f"{item.width}x{item.height}")
                except Exception:
                    pass
                root.after(30, _poll)

            root.after(30, _poll)
            root.mainloop()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        self._ready.wait(timeout=5)

    def show(self, path: Path) -> None:
        """Display the image at *path* in the window at its native resolution."""
        from PIL import Image

        img = Image.open(path)
        # No resize — the image was rendered at exactly QR_WINDOW_SIZE px.
        self._queue.put(img)

    def close(self) -> None:
        """Destroy the window."""
        self._queue.put(None)


def _render_qr_image(data: str, dest: Path) -> None:
    """Render a QR code PNG whose size is close to QR_WINDOW_SIZE.

    We compute box_size so that (modules + 2*border) * box_size ≈ QR_WINDOW_SIZE.
    This avoids any resize step — the image is pixel-perfect from the start.
    """
    # First pass: determine the number of modules for this payload.
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=IMAGE_BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)
    modules = qr.modules_count  # modules per side (excluding border)
    total_units = modules + 2 * IMAGE_BORDER
    box_size = max(4, QR_WINDOW_SIZE // total_units)  # at least 4px per module

    # Second pass: render at the computed box_size.
    qr2 = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=IMAGE_BORDER,
    )
    qr2.add_data(data)
    qr2.make(fit=True)
    img = qr2.make_image(fill_color="black", back_color="white")
    img.save(str(dest))


def _render_qr_terminal(data: str) -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    lines: list[str] = []
    for row_idx in range(0, len(matrix), 2):
        top = matrix[row_idx]
        bottom = (
            matrix[row_idx + 1] if row_idx + 1 < len(matrix) else [False] * len(top)
        )
        line = ""
        for t, b in zip(top, bottom):
            if t and b:
                line += "█"
            elif t and not b:
                line += "▀"
            elif not t and b:
                line += "▄"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)


def _show_terminal_chunk(
    index: int,
    total: int,
    payload: str,
    filename: str,
    auto_delay: Optional[float],
) -> None:
    console.clear()
    text = Text(_render_qr_terminal(payload), style="black on white")
    progress = f"[bold]{index + 1}[/bold] / {total}"
    title = f"[cyan]{filename}[/cyan]  —  chunk {progress}"
    subtitle = (
        f"[dim]auto-advance in {auto_delay:.1f}s[/dim]"
        if auto_delay
        else "[dim]ENTER = next   B = back   Q = quit[/dim]"
    )
    console.print(
        Panel(text, title=title, subtitle=subtitle, expand=False, padding=(0, 1))
    )


# ---------------------------------------------------------------------------
# Send command
# ---------------------------------------------------------------------------


@app.command("send")
def send(
    file: Annotated[Path, typer.Argument(help="File to send.")],
    chunk_size: Annotated[
        int,
        typer.Option("--chunk-size", "-s", help="Raw bytes per QR chunk."),
    ] = DEFAULT_CHUNK_SIZE,
    auto: Annotated[
        Optional[float],
        typer.Option(
            "--auto", "-a", help="Auto-advance every N seconds instead of key input."
        ),
    ] = None,
    start: Annotated[
        int,
        typer.Option("--start", "-S", help="Start from chunk index (0-based)."),
    ] = 0,
    terminal: Annotated[
        bool,
        typer.Option(
            "--terminal", "-t", help="Force terminal block-character rendering."
        ),
    ] = False,
) -> None:
    """Read a file and display a sequence of QR codes for air-gap transfer."""
    if not file.exists():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(code=1)
    if not file.is_file():
        console.print(f"[red]Not a file:[/red] {file}")
        raise typer.Exit(code=1)

    raw = file.read_bytes()
    total_chunks = max(1, math.ceil(len(raw) / chunk_size))

    if start < 0 or start >= total_chunks:
        console.print(f"[red]--start must be between 0 and {total_chunks - 1}[/red]")
        raise typer.Exit(code=1)

    use_image = _has_display() and not terminal
    renderer = "image viewer" if use_image else "terminal"

    console.print(
        f"[bold green]Sending[/bold green] [cyan]{file.name}[/cyan]  "
        f"({len(raw):,} bytes  →  {total_chunks} chunk{'s' if total_chunks != 1 else ''}  "
        f"via {renderer})"
    )

    payloads: list[str] = []
    for i in range(total_chunks):
        chunk = raw[i * chunk_size : (i + 1) * chunk_size]
        payloads.append(_make_chunk_payload(i, total_chunks, file.name, chunk))

    if use_image:
        _send_image_mode(payloads, total_chunks, file.name, auto, start)
    else:
        _send_terminal_mode(payloads, total_chunks, file.name, auto, start)


def _send_status_panel(
    index: int,
    total: int,
    filename: str,
    auto_delay: Optional[float],
) -> Panel:
    """Build a Rich panel showing send progress."""
    bar = "".join("█" if i <= index else "░" for i in range(total))
    body_lines = [
        f"[bold]{index + 1}[/bold] / {total} chunks  —  [cyan]{filename}[/cyan]",
        f"[green]{bar}[/green]",
    ]
    if auto_delay:
        body_lines.append(f"[dim]auto-advancing every {auto_delay:.1f}s[/dim]")
    else:
        body_lines.append("[dim]ENTER = next   B = back   Q = quit[/dim]")
    body = Text.from_markup("\n".join(body_lines))
    return Panel(body, title="[bold]Send[/bold]", expand=False)


def _send_image_mode(
    payloads: list[str],
    total: int,
    filename: str,
    auto_delay: Optional[float],
    start: int,
) -> None:
    with tempfile.TemporaryDirectory(prefix="qrtransfer_") as tmpdir:
        tmp = Path(tmpdir)

        # Pre-render all chunks so navigation is instant.
        console.print("Rendering QR codes…")
        png_paths: list[Path] = []
        for i, payload in enumerate(payloads):
            p = tmp / f"chunk_{i:04d}.png"
            _render_qr_image(payload, p)
            png_paths.append(p)

        window = _QRWindow()
        index = start

        try:
            with Live(
                _send_status_panel(index, total, filename, auto_delay),
                console=console,
                refresh_per_second=4,
            ) as live:
                while True:
                    window.show(png_paths[index])
                    live.update(_send_status_panel(index, total, filename, auto_delay))
                    time.sleep(VIEWER_OPEN_DELAY)

                    if auto_delay is not None:
                        time.sleep(auto_delay)
                        if index >= total - 1:
                            live.update(
                                _send_status_panel(index, total, filename, auto_delay)
                            )
                            break
                        index += 1
                    else:
                        # Live context doesn't play well with Prompt — stop
                        # the live display temporarily to read input.
                        live.stop()
                        try:
                            answer = Prompt.ask(
                                "",
                                choices=[],
                                default="",
                                show_choices=False,
                                show_default=False,
                                console=console,
                            )
                        except (EOFError, KeyboardInterrupt):
                            break
                        live.start()

                        key = answer.strip().lower()
                        if key in ("q", "quit", "exit"):
                            break
                        elif key in ("b", "back", "p", "prev"):
                            index = max(0, index - 1)
                        else:
                            if index >= total - 1:
                                live.update(
                                    _send_status_panel(
                                        index, total, filename, auto_delay
                                    )
                                )
                                break
                            index += 1
        finally:
            window.close()

    console.print(
        f"[bold green]All {total} chunk{'s' if total != 1 else ''} displayed.[/bold green]"
    )


def _send_terminal_mode(
    payloads: list[str],
    total: int,
    filename: str,
    auto_delay: Optional[float],
    start: int,
) -> None:
    index = start
    while True:
        _show_terminal_chunk(index, total, payloads[index], filename, auto_delay)
        console.print(_send_status_panel(index, total, filename, auto_delay))

        if auto_delay is not None:
            time.sleep(auto_delay)
            if index >= total - 1:
                break
            index += 1
        else:
            try:
                answer = Prompt.ask(
                    "",
                    choices=[],
                    default="",
                    show_choices=False,
                    show_default=False,
                    console=console,
                )
            except (EOFError, KeyboardInterrupt):
                break

            key = answer.strip().lower()
            if key in ("q", "quit", "exit"):
                break
            elif key in ("b", "back", "p", "prev"):
                index = max(0, index - 1)
            else:
                if index >= total - 1:
                    break
                index += 1

    console.print(
        f"[bold green]All {total} chunk{'s' if total != 1 else ''} displayed.[/bold green]"
    )


# ---------------------------------------------------------------------------
# Receive helpers
# ---------------------------------------------------------------------------


def _chunks_status_panel(
    total: int | None,
    received: set[int],
    filename: str | None,
    poll_count: int = 0,
    decode_count: int = 0,
) -> Panel:
    """Build a Rich panel showing which chunks have been received."""
    if total is None:
        body = Text.from_markup(
            "Waiting for first QR code…\n"
            f"[dim]polls: {poll_count}  decoded: {decode_count}[/dim]"
        )
    else:
        missing = sorted(set(range(total)) - received)
        done = len(received)
        bar = "".join("█" if i in received else "░" for i in range(total))
        body_lines = [
            f"[bold]{done}[/bold] / {total} chunks  —  [cyan]{filename or '?'}[/cyan]",
            f"[green]{bar}[/green]",
        ]
        if missing:
            body_lines.append(f"[yellow]Missing:[/yellow] {missing}")
        else:
            body_lines.append("[bold green]✓ All chunks received![/bold green]")
        body_lines.append(f"[dim]polls: {poll_count}  decoded: {decode_count}[/dim]")
        body = Text.from_markup("\n".join(body_lines))

    return Panel(body, title="[bold]Receive[/bold]", expand=False)


def _assemble_file(chunks: dict[int, bytes], total: int, dest: Path) -> None:
    dest.write_bytes(b"".join(chunks[i] for i in range(total)))


# ---------------------------------------------------------------------------
# Receive — screenshot mode
# ---------------------------------------------------------------------------


def _receive_screenshot(output: Path | None) -> None:
    """Poll the screen with scrot + zbarimg until all chunks are received."""
    chunks: dict[int, bytes] = {}
    total: int | None = None
    filename: str | None = None

    console.print(
        "[bold green]Receive (screenshot)[/bold green]  "
        "Scanning the screen with scrot + zbarimg.\n"
        "Press [bold]Ctrl-C[/bold] to abort.\n"
    )

    poll_count = 0
    decode_count = 0

    screenshot_path = Path(tempfile.gettempdir()) / "qrtransfer_screen.png"

    try:
        with Live(
            _chunks_status_panel(None, set(), None),
            console=console,
            refresh_per_second=4,
        ) as live:
            while True:
                poll_count += 1
                decoded = _decode_qr_from_screen(screenshot_path)

                if decoded:
                    decode_count += 1
                    chunk = _parse_chunk_payload(decoded)
                    if chunk is not None:
                        idx: int = chunk["i"]
                        n: int = chunk["n"]
                        name: str = chunk["name"]
                        data: bytes = base64.b64decode(chunk["data"])

                        if total is None:
                            total = n
                            filename = name

                        if idx not in chunks:
                            chunks[idx] = data

                        if len(chunks) == total:
                            live.update(
                                _chunks_status_panel(
                                    total,
                                    set(chunks),
                                    filename,
                                    poll_count,
                                    decode_count,
                                )
                            )
                            break

                live.update(
                    _chunks_status_panel(
                        total,
                        set(chunks),
                        filename,
                        poll_count,
                        decode_count,
                    )
                )

                time.sleep(SCREENSHOT_POLL_INTERVAL)

    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=1)
    finally:
        screenshot_path.unlink(missing_ok=True)

    _finish_receive(chunks, total, filename, output)


# ---------------------------------------------------------------------------
# Receive — webcam mode
# ---------------------------------------------------------------------------


def _receive_webcam(output: Path | None, camera: int) -> None:
    """Capture frames from a webcam and decode QR codes until transfer complete."""
    import cv2

    chunks: dict[int, bytes] = {}
    total: int | None = None
    filename: str | None = None

    console.print(
        f"[bold green]Receive (webcam {camera})[/bold green]  "
        "Hold each QR code in front of the camera.\n"
        "Press [bold]Ctrl-C[/bold] to abort.\n"
    )

    poll_count = 0
    decode_count = 0

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        console.print(f"[red]Cannot open camera {camera}.[/red]")
        raise typer.Exit(code=1)

    try:
        with Live(
            _chunks_status_panel(None, set(), None),
            console=console,
            refresh_per_second=4,
        ) as live:
            while True:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(WEBCAM_POLL_INTERVAL)
                    continue

                poll_count += 1
                decoded = _decode_qr_from_webcam_frame(frame)

                if decoded:
                    decode_count += 1
                    chunk = _parse_chunk_payload(decoded)
                    if chunk is not None:
                        idx: int = chunk["i"]
                        n: int = chunk["n"]
                        name: str = chunk["name"]
                        data: bytes = base64.b64decode(chunk["data"])

                        if total is None:
                            total = n
                            filename = name

                        if idx not in chunks:
                            chunks[idx] = data

                        if len(chunks) == total:
                            live.update(
                                _chunks_status_panel(
                                    total,
                                    set(chunks),
                                    filename,
                                    poll_count,
                                    decode_count,
                                )
                            )
                            break

                live.update(
                    _chunks_status_panel(
                        total,
                        set(chunks),
                        filename,
                        poll_count,
                        decode_count,
                    )
                )

                time.sleep(WEBCAM_POLL_INTERVAL)

    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/yellow]")
        cap.release()
        raise typer.Exit(code=1)
    finally:
        cap.release()

    _finish_receive(chunks, total, filename, output)


# ---------------------------------------------------------------------------
# Shared receive finish
# ---------------------------------------------------------------------------


def _finish_receive(
    chunks: dict[int, bytes],
    total: int | None,
    filename: str | None,
    output: Path | None,
) -> None:
    if total is None or not chunks:
        console.print("[red]No chunks received — nothing to write.[/red]")
        raise typer.Exit(code=1)

    missing = set(range(total)) - set(chunks)
    if missing:
        console.print(
            f"[red]Incomplete transfer:[/red] missing chunks {sorted(missing)}.\n"
            "Re-run receive to collect the remaining chunks."
        )
        raise typer.Exit(code=1)

    dest = output or Path(filename or "received_file")
    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        counter = 1
        while dest.exists():
            dest = dest.with_name(f"{stem}_{counter}{suffix}")
            counter += 1
        console.print(f"[yellow]Output file already exists — saving as {dest}[/yellow]")

    _assemble_file(chunks, total, dest)
    size = dest.stat().st_size
    console.print(
        f"\n[bold green]✓ Saved[/bold green] [cyan]{dest}[/cyan]  ({size:,} bytes)"
    )


# ---------------------------------------------------------------------------
# Receive command
# ---------------------------------------------------------------------------


@app.command("receive")
def receive(
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output file path. Defaults to the filename embedded in the QR codes.",
        ),
    ] = None,
    mode: Annotated[
        ReceiveMode,
        typer.Option(
            "--mode",
            "-m",
            help="Scan source: screenshot (polls the screen) or webcam.",
        ),
    ] = ReceiveMode.screenshot,
    camera: Annotated[
        int,
        typer.Option(
            "--camera",
            "-c",
            help="Webcam device index (used with --mode webcam).",
        ),
    ] = 0,
) -> None:
    """Scan QR codes to reassemble a file transferred with the send command."""
    if mode == ReceiveMode.screenshot:
        _receive_screenshot(output)
    else:
        _receive_webcam(output, camera)


if __name__ == "__main__":
    app()
