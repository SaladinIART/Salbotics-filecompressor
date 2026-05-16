from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from salbotics_filecompressor.gui import format_batch_summary, format_result_summary, format_size


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
            "scan.pdf: success | 2.0 KB -> 1.0 KB | preserve-text:120dpi:q65",
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


if __name__ == "__main__":
    unittest.main()
