"""Tkinter GUI shell for Salbotics File Compressor."""

from __future__ import annotations

import queue
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .compressor import (
    DEFAULT_TARGET_KB,
    IMAGE_OUTPUT_PDF,
    IMAGE_OUTPUT_SAME_FORMAT,
    QUALITY_AGGRESSIVE,
    QUALITY_SAFE,
    QUALITY_SMART,
    SUPPORTED_IMAGE_SUFFIXES,
    CompressionOptions,
    compress_batch,
    compress_file,
)
from .engine_registry import EngineInfo, detect_engines
from .errors import FileCompressorError


READY_MESSAGE = "Ready"
APP_ICON = Path(__file__).resolve().parents[2] / "assets" / "salbotics-filecompressor.ico"


class SalboticsFileCompressorApp(tk.Tk):
    """Tkinter shell for Salbotics File Compressor."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Salbotics File Compressor")
        self.minsize(760, 440)
        if APP_ICON.exists():
            self.iconbitmap(APP_ICON)

        self.mode = tk.StringVar(value="file")
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.target_kb = tk.StringVar(value=str(DEFAULT_TARGET_KB))
        self.grayscale = tk.BooleanVar(value=False)
        self.image_output = tk.StringVar(value=IMAGE_OUTPUT_SAME_FORMAT)
        self.force_optimize = tk.BooleanVar(value=False)
        self.quality_mode = tk.StringVar(value=QUALITY_SMART)
        self.status = tk.StringVar(value=READY_MESSAGE)
        self.engine_status = tk.StringVar(value=format_engine_summary(detect_engines()))
        self._last_output_dir: Path | None = None
        self._result_queue: queue.Queue[tuple[str, list[object] | str]] = queue.Queue()

        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="Mode").grid(row=0, column=0, sticky="w", pady=(0, 10))
        mode_frame = ttk.Frame(root)
        mode_frame.grid(row=0, column=1, sticky="w", pady=(0, 10))
        ttk.Radiobutton(mode_frame, text="Single file", value="file", variable=self.mode).grid(
            row=0, column=0, padx=(0, 16)
        )
        ttk.Radiobutton(mode_frame, text="Folder", value="folder", variable=self.mode).grid(
            row=0, column=1
        )

        ttk.Label(root, text="Input").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.input_path).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(root, text="Browse", command=self._browse_input).grid(
            row=1, column=2, padx=(8, 0), pady=6
        )

        ttk.Label(root, text="Output folder").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.output_dir).grid(row=2, column=1, sticky="ew", pady=6)
        ttk.Button(root, text="Browse", command=self._browse_output_dir).grid(
            row=2, column=2, padx=(8, 0), pady=6
        )

        ttk.Label(root, text="Target KB").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(root, width=12, textvariable=self.target_kb).grid(
            row=3, column=1, sticky="w", pady=6
        )

        ttk.Checkbutton(root, text="Allow grayscale", variable=self.grayscale).grid(
            row=4, column=1, sticky="w", pady=6
        )

        ttk.Checkbutton(root, text="Force optimize", variable=self.force_optimize).grid(
            row=5, column=1, sticky="w", pady=6
        )

        ttk.Label(root, text="Quality mode").grid(row=6, column=0, sticky="w", pady=6)
        ttk.Combobox(
            root,
            textvariable=self.quality_mode,
            values=(QUALITY_SAFE, QUALITY_SMART, QUALITY_AGGRESSIVE),
            state="readonly",
            width=14,
        ).grid(row=6, column=1, sticky="w", pady=6)

        ttk.Label(root, text="Image output").grid(row=7, column=0, sticky="w", pady=6)
        image_output_frame = ttk.Frame(root)
        image_output_frame.grid(row=7, column=1, sticky="w", pady=6)
        ttk.Radiobutton(
            image_output_frame,
            text="Same format",
            value=IMAGE_OUTPUT_SAME_FORMAT,
            variable=self.image_output,
        ).grid(row=0, column=0, padx=(0, 16))
        ttk.Radiobutton(
            image_output_frame,
            text="PDF",
            value=IMAGE_OUTPUT_PDF,
            variable=self.image_output,
        ).grid(row=0, column=1)

        ttk.Label(root, textvariable=self.engine_status).grid(
            row=8,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(4, 0),
        )

        actions_frame = ttk.Frame(root)
        actions_frame.grid(row=9, column=1, sticky="w", pady=(18, 8))
        self.compress_button = ttk.Button(root, text="Compress", command=self._compress)
        self.compress_button.grid(row=0, column=0, sticky="w")
        self.open_output_button = ttk.Button(
            actions_frame,
            text="Open output folder",
            command=self._open_output_folder,
            state="disabled",
        )
        self.open_output_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.grid(row=10, column=0, columnspan=3, sticky="ew", pady=(10, 8))

        ttk.Label(root, textvariable=self.status).grid(row=11, column=0, columnspan=3, sticky="w")

        columns = ("file", "status", "original", "final", "mode", "note")
        self.results_table = ttk.Treeview(root, columns=columns, show="headings", height=8)
        headings = {
            "file": "File",
            "status": "Status",
            "original": "Original",
            "final": "Final",
            "mode": "Mode",
            "note": "Note",
        }
        widths = {
            "file": 180,
            "status": 120,
            "original": 90,
            "final": 90,
            "mode": 150,
            "note": 240,
        }
        for column in columns:
            self.results_table.heading(column, text=headings[column])
            self.results_table.column(column, width=widths[column], anchor="w")
        self.results_table.grid(row=12, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        root.rowconfigure(12, weight=1)

    def _browse_input(self) -> None:
        if self.mode.get() == "folder":
            selected = filedialog.askdirectory(title="Choose file folder")
        else:
            selected = filedialog.askopenfilename(
                title="Choose file",
                filetypes=[
                    (
                        "Supported files",
                        _filetype_pattern((".pdf", *SUPPORTED_IMAGE_SUFFIXES)),
                    ),
                    ("PDF files", "*.pdf"),
                    ("Image files", _filetype_pattern(SUPPORTED_IMAGE_SUFFIXES)),
                    ("All files", "*.*"),
                ],
            )
        if selected:
            self.input_path.set(str(Path(selected)))

    def _browse_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="Choose output folder")
        if selected:
            self.output_dir.set(str(Path(selected)))

    def _compress(self) -> None:
        request = self._build_request()
        if request is None:
            return

        self._clear_results()
        self._last_output_dir = None
        self.status.set("Compressing...")
        self.compress_button.configure(state="disabled")
        self.open_output_button.configure(state="disabled")
        self.progress.start(12)

        thread = threading.Thread(target=self._compress_in_background, args=request, daemon=True)
        thread.start()
        self.after(100, self._poll_result_queue)

    def _build_request(self) -> tuple[Path, Path, CompressionOptions, str] | None:
        if not self.input_path.get():
            messagebox.showerror("Missing input", "Choose a file or folder.")
            return None
        if not self.output_dir.get():
            messagebox.showerror("Missing output", "Choose an output folder.")
            return None

        try:
            target_kb = int(self.target_kb.get())
        except ValueError:
            messagebox.showerror("Invalid target", "Target KB must be a whole number.")
            return None

        if target_kb <= 0:
            messagebox.showerror("Invalid target", "Target KB must be greater than 0.")
            return None

        options = CompressionOptions(
            target_kb=target_kb,
            grayscale=self.grayscale.get(),
            image_output=self.image_output.get(),
            force_optimize=self.force_optimize.get(),
            quality_mode=self.quality_mode.get(),
        )
        return Path(self.input_path.get()), Path(self.output_dir.get()), options, self.mode.get()

    def _compress_in_background(
        self,
        input_path: Path,
        output_dir: Path,
        options: CompressionOptions,
        mode: str,
    ) -> None:
        try:
            if mode == "folder":
                payload: list[object] | str = compress_batch(
                    sorted(path for path in input_path.iterdir() if path.is_file()),
                    output_dir,
                    options,
                )
            else:
                output_path = _single_output_path(input_path, output_dir, options)
                payload = [compress_file(input_path, output_path, options)]
        except FileCompressorError as exc:
            self._result_queue.put(("error", str(exc)))
            return

        self._result_queue.put(("success", payload))

    def _poll_result_queue(self) -> None:
        try:
            status, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_result_queue)
            return

        self.progress.stop()
        self.compress_button.configure(state="normal")

        if status == "success":
            results = list(payload) if isinstance(payload, list) else []
            summary = format_batch_summary(results)
            self.status.set(summary)
            self._last_output_dir = Path(self.output_dir.get())
            if self._last_output_dir.exists():
                self.open_output_button.configure(state="normal")
            self._set_result_rows(results)
            messagebox.showinfo("Salbotics File Compressor", summary)
            return

        message = str(payload)
        self.status.set("Error")
        self._last_output_dir = None
        self.open_output_button.configure(state="disabled")
        self._clear_results()
        messagebox.showerror("Salbotics File Compressor", message)

    def _clear_results(self) -> None:
        for item in self.results_table.get_children():
            self.results_table.delete(item)

    def _set_result_rows(self, results: list[object]) -> None:
        self._clear_results()
        for result in results:
            self.results_table.insert(
                "",
                "end",
                values=(
                    getattr(result, "input_path").name,
                    getattr(result, "status"),
                    format_size(getattr(result, "original_size_bytes")),
                    format_size(getattr(result, "final_size_bytes")),
                    getattr(result, "mode"),
                    format_result_note(result),
                ),
            )

    def _open_output_folder(self) -> None:
        if self._last_output_dir is None:
            messagebox.showerror("Missing output", "No output folder is available yet.")
            return
        try:
            open_folder(self._last_output_dir)
        except OSError as exc:
            messagebox.showerror("Salbotics File Compressor", str(exc))


def format_result_summary(result: object) -> str:
    """Format one GUI result line."""
    note = format_result_note(result)
    summary = (
        f"{getattr(result, 'input_path').name}: {getattr(result, 'status')} | "
        f"{format_size(getattr(result, 'original_size_bytes'))} -> "
        f"{format_size(getattr(result, 'final_size_bytes'))} | {getattr(result, 'mode')}"
    )
    if note:
        summary += f" | {note}"
    return summary


def format_result_note(result: object) -> str:
    """Return a user-facing note for the result table."""
    warning = getattr(result, "warning") or ""
    status = getattr(result, "status")
    mode = getattr(result, "mode")
    if warning:
        if "kept original" in warning:
            return "Kept original; compression was not smaller."
        return warning
    if status == "already-under-target":
        return "Already under target; copied original."
    if status == "success":
        return "Target reached."
    if status == "optimized":
        return "Optimized from an already under-target file."
    if status == "skipped":
        return "Unsupported file type."
    if status == "failed":
        return "Failed."
    if mode == "copy":
        return "Copied original."
    return ""


def format_batch_summary(results: list[object]) -> str:
    """Format a compact multi-file GUI summary."""
    if not results:
        return "No files found."

    failed = sum(1 for result in results if getattr(result, "status") == "failed")
    skipped = sum(1 for result in results if getattr(result, "status") == "skipped")
    warnings = sum(1 for result in results if getattr(result, "warning"))
    return (
        f"Processed {len(results)} file(s). "
        f"Failed: {failed}. Skipped: {skipped}. Warnings: {warnings}."
    )


def format_size(size_bytes: int) -> str:
    """Format bytes as KB for GUI display."""
    return f"{size_bytes / 1024:.1f} KB"


def format_engine_summary(engines: list[EngineInfo]) -> str:
    """Format compact GUI engine readiness text."""
    by_name = {engine.name: engine for engine in engines}
    ghostscript = by_name.get("ghostscript")
    magick = by_name.get("imagemagick")
    pdf_status = "PDF ready" if ghostscript and ghostscript.available else "PDF needs Ghostscript"
    image_status = "Extended images ready" if magick and magick.available else "Extended images need ImageMagick"
    return f"{pdf_status}. {image_status}."


def _filetype_pattern(suffixes: tuple[str, ...] | frozenset[str]) -> str:
    return " ".join(f"*{suffix}" for suffix in sorted(suffixes))


def open_folder(path: Path) -> None:
    """Open a folder in Windows Explorer."""
    if not path.exists():
        raise OSError(f"output folder does not exist: {path}")
    os.startfile(path)  # type: ignore[attr-defined]


def _single_output_path(
    input_path: Path,
    output_dir: Path,
    options: CompressionOptions,
) -> Path:
    suffix = input_path.suffix.lower()
    if suffix == ".pdf" or options.image_output == IMAGE_OUTPUT_PDF:
        suffix = ".pdf"
    return output_dir / f"{input_path.stem}_compressed{suffix}"


def main() -> None:
    """Launch the GUI."""
    app = SalboticsFileCompressorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
