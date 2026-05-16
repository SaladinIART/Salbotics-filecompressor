from __future__ import annotations

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from salbotics_filecompressor.engine_registry import (
    EngineInfo,
    detect_engines,
    format_engine_table,
    format_supported_formats,
    supported_input_extensions,
)


class EngineRegistryTests(unittest.TestCase):
    def test_detect_engines_includes_builtin_pillow(self) -> None:
        with patch(
            "salbotics_filecompressor.engine_registry.find_ghostscript",
            side_effect=RuntimeError("missing"),
        ), patch(
            "salbotics_filecompressor.engine_registry._read_version",
            return_value="tool 1.0",
        ):
            engines = detect_engines(which=lambda name: None)

        pillow = next(engine for engine in engines if engine.name == "pillow")

        self.assertTrue(pillow.available)
        self.assertIn(".jpg", pillow.input_extensions)
        self.assertIn("image_compress", pillow.capabilities)

    def test_detect_engines_marks_path_tools_available(self) -> None:
        tools = {
            "qpdf": r"C:\Tools\qpdf.exe",
            "mutool": r"C:\Tools\mutool.exe",
            "magick": r"C:\Tools\magick.exe",
            "vips": r"C:\Tools\vips.exe",
            "soffice": r"C:\Tools\soffice.exe",
        }

        def fake_which(name: str) -> str | None:
            return tools.get(name)

        with patch(
            "salbotics_filecompressor.engine_registry.find_ghostscript",
            return_value=Path(r"C:\Tools\gswin64c.exe"),
        ), patch(
            "salbotics_filecompressor.engine_registry._read_version",
            return_value="tool 1.0",
        ):
            engines = detect_engines(which=fake_which)

        available = {engine.name for engine in engines if engine.available}

        self.assertGreaterEqual(
            available,
            {"ghostscript", "imagemagick", "libreoffice", "libvips", "mutool", "qpdf"},
        )

    def test_detect_engines_uses_configured_pdf_cleanup_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            qpdf = root / "qpdf.exe"
            mutool = root / "mutool.exe"
            qpdf.write_text("fake")
            mutool.write_text("fake")

            with patch.dict(
                "os.environ",
                {
                    "SALBOTICS_FILECOMPRESSOR_QPDF": str(qpdf),
                    "SALBOTICS_FILECOMPRESSOR_MUTOOL": str(mutool),
                },
                clear=True,
            ), patch(
                "salbotics_filecompressor.engine_registry.find_ghostscript",
                side_effect=RuntimeError("missing"),
            ), patch(
                "salbotics_filecompressor.engine_registry._read_version",
                return_value="tool 1.0",
            ):
                engines = detect_engines()

        paths = {engine.name: engine.path for engine in engines}

        self.assertEqual(paths["qpdf"], qpdf)
        self.assertEqual(paths["mutool"], mutool)

    def test_supported_input_extensions_uses_available_engines(self) -> None:
        engines = [
            EngineInfo(
                name="pillow",
                display_name="Pillow",
                available=True,
                capabilities=("image_compress",),
                input_extensions=(".jpg", ".png"),
                output_extensions=(".jpg", ".png"),
            ),
            EngineInfo(
                name="libreoffice",
                display_name="LibreOffice",
                available=False,
                capabilities=("office_to_pdf",),
                input_extensions=(".docx",),
                output_extensions=(".pdf",),
            ),
        ]

        self.assertEqual(supported_input_extensions(engines), (".jpg", ".png"))

    def test_format_engine_table_shows_missing_note(self) -> None:
        engines = [
            EngineInfo(
                name="qpdf",
                display_name="qpdf",
                available=False,
                capabilities=("pdf_cleanup",),
                input_extensions=(".pdf",),
                output_extensions=(".pdf",),
                note="Install qpdf",
            )
        ]

        output = format_engine_table(engines)

        self.assertIn("qpdf", output)
        self.assertIn("missing", output)
        self.assertIn("Install qpdf", output)

    def test_format_supported_formats_lists_engine_names(self) -> None:
        engines = [
            EngineInfo(
                name="pillow",
                display_name="Pillow",
                available=True,
                capabilities=("image_compress",),
                input_extensions=(".jpg",),
                output_extensions=(".jpg",),
            )
        ]

        output = format_supported_formats(engines)

        self.assertIn(".jpg", output)
        self.assertIn("pillow", output)


if __name__ == "__main__":
    unittest.main()
