from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from salbotics_filecompressor.engine_registry import EngineInfo
from salbotics_filecompressor.gui import (
    _filetype_pattern,
    format_batch_summary,
    format_engine_summary,
    format_result_note,
    format_result_summary,
    format_size,
)


class GuiFormattingTests(unittest.TestCase):
    def test_format_single_result_summary(self) -> None:
        result = SimpleNamespace(
            input_path=Path("scan.pdf"),
            original_size_bytes=2048,
            final_size_bytes=1024,
            mode="preserve-text:120dpi:q65",
            status="success",
            warning=None,
        )

        self.assertEqual(
            format_result_summary(result),
            "scan.pdf: success | 2.0 KB -> 1.0 KB | "
            "preserve-text:120dpi:q65 | Target reached.",
        )

    def test_format_result_note_explains_copy_and_warning_states(self) -> None:
        kept = SimpleNamespace(
            status="warning",
            mode="copy",
            warning="target not reached; kept original because image:100%:q85 was not smaller",
        )
        copied = SimpleNamespace(status="already-under-target", mode="copy", warning=None)
        optimized = SimpleNamespace(status="optimized", mode="image:100%:q85", warning=None)

        self.assertEqual(
            format_result_note(kept),
            "Kept original; compression was not smaller.",
        )
        self.assertEqual(
            format_result_note(copied),
            "Already under target; copied original.",
        )
        self.assertEqual(
            format_result_note(optimized),
            "Optimized from an already under-target file.",
        )

    def test_format_batch_summary_counts_failures_and_warnings(self) -> None:
        results = [
            SimpleNamespace(
                input_path=Path("a.pdf"),
                original_size_bytes=2048,
                final_size_bytes=1024,
                mode="copy",
                status="already-under-target",
                warning=None,
            ),
            SimpleNamespace(
                input_path=Path("b.pdf"),
                original_size_bytes=4096,
                final_size_bytes=0,
                mode="failed",
                status="failed",
                warning="input PDF does not exist",
            ),
        ]

        summary = format_batch_summary(results)

        self.assertEqual(
            summary,
            "Processed 2 file(s). Failed: 1. Skipped: 0. Warnings: 1.",
        )

    def test_format_empty_batch_summary(self) -> None:
        self.assertEqual(format_batch_summary([]), "No files found.")

    def test_format_size(self) -> None:
        self.assertEqual(format_size(1536), "1.5 KB")

    def test_format_engine_summary_reports_key_optional_engines(self) -> None:
        engines = [
            EngineInfo(
                name="ghostscript",
                display_name="Ghostscript",
                available=True,
                capabilities=("pdf_compress",),
                input_extensions=(".pdf",),
                output_extensions=(".pdf",),
            ),
            EngineInfo(
                name="imagemagick",
                display_name="ImageMagick",
                available=False,
                capabilities=("image_convert",),
                input_extensions=(".webp",),
                output_extensions=(".webp",),
            ),
        ]

        self.assertEqual(
            format_engine_summary(engines),
            "PDF ready. Extended images need ImageMagick.",
        )

    def test_filetype_pattern_sorts_supported_suffixes(self) -> None:
        self.assertEqual(_filetype_pattern(frozenset({".webp", ".jpg"})), "*.jpg *.webp")


if __name__ == "__main__":
    unittest.main()
