from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from salbotics_filecompressor.compressor import (
    IMAGE_OUTPUT_PDF,
    IMAGE_OUTPUT_SAME_FORMAT,
    QUALITY_SAFE,
    QUALITY_SMART,
    CompressionOptions,
    compress_batch,
    compress_file,
    find_ghostscript,
    _image_candidates_for,
)
from salbotics_filecompressor.errors import CompressionFailedError, GhostscriptNotFoundError


def completed() -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")


def output_path_from(command: list[str]) -> Path:
    for part in command:
        if part.startswith("-sOutputFile="):
            return Path(part.removeprefix("-sOutputFile="))
    raise AssertionError("missing -sOutputFile")


def cleanup_output_path_from(command: list[str]) -> Path:
    return Path(command[-1])


def magick_output_path_from(command: list[str]) -> Path:
    return Path(command[-1])


class CompressionEngineTests(unittest.TestCase):
    def test_target_bytes_uses_binary_kilobytes(self) -> None:
        self.assertEqual(CompressionOptions().target_bytes, 499 * 1024)

    def test_invalid_quality_mode_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CompressionOptions(quality_mode="reckless")  # type: ignore[arg-type]

    def test_missing_ghostscript_has_actionable_message(self) -> None:
        with patch.dict("os.environ", {}, clear=True), patch(
            "shutil.which", return_value=None
        ), patch(
            "salbotics_filecompressor.compressor._standard_windows_ghostscript_paths",
            return_value=[],
        ):
            with self.assertRaises(GhostscriptNotFoundError) as raised:
                find_ghostscript()

        self.assertIn("Ghostscript not found", str(raised.exception))
        self.assertIn("SALBOTICS_FILECOMPRESSOR_GS", str(raised.exception))

    def test_find_ghostscript_checks_standard_windows_install_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exe = root / "gs" / "gs10.07.0" / "bin" / "gswin64c.exe"
            exe.parent.mkdir(parents=True)
            exe.write_text("fake")

            with patch.dict(
                "os.environ",
                {"ProgramFiles": str(root), "ProgramFiles(x86)": str(root / "x86")},
                clear=True,
            ), patch("shutil.which", return_value=None):
                self.assertEqual(find_ghostscript(), exe)

    def test_already_small_pdf_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "small.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"%PDF tiny")

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=499),
                gs_path="fake-gs",
                run_command=lambda command: completed(),
            )

            self.assertEqual(result.status, "already-under-target")
            self.assertEqual(result.mode, "copy")
            self.assertEqual(output.read_bytes(), source.read_bytes())

    def test_force_optimize_does_not_copy_small_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "small.jpg"
            output = root / "out.jpg"
            image = Image.effect_noise((300, 300), 80).convert("RGB")
            image.save(source, "JPEG", quality=95)
            image.close()

            result = compress_file(
                source,
                output,
                CompressionOptions(
                    target_kb=499,
                    force_optimize=True,
                    image_output=IMAGE_OUTPUT_SAME_FORMAT,
                ),
            )

            self.assertNotEqual(output.read_bytes(), source.read_bytes())
            self.assertIn(result.status, {"optimized", "warning"})
            self.assertTrue(result.mode.startswith("image:"))

    def test_smart_near_target_image_candidates_start_gently(self) -> None:
        options = CompressionOptions(target_kb=100, quality_mode=QUALITY_SMART)

        candidates = _image_candidates_for(options, original_size=110 * 1024)

        self.assertEqual(candidates[0], (1.0, 88))
        self.assertIn((0.95, 82), candidates)

    def test_safe_pdf_mode_skips_raster_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                target = output_path_from(command)
                target.write_bytes(b"p" * 3000)
                return completed()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=1, quality_mode=QUALITY_SAFE),
                gs_path="fake-gs",
                run_command=fake_runner,
            )

            self.assertEqual(result.status, "warning")
            self.assertTrue(commands)
            self.assertTrue(all("-sDEVICE=pdfwrite" in command for command in commands))

    def test_qpdf_cleanup_can_succeed_without_ghostscript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                cleanup_output_path_from(command).write_bytes(b"q" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_qpdf",
                return_value=Path("fake-qpdf"),
            ), patch(
                "salbotics_filecompressor.compressor.find_mutool",
                return_value=None,
            ), patch(
                "salbotics_filecompressor.compressor.find_ghostscript",
                side_effect=AssertionError("Ghostscript should not be needed"),
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1),
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "qpdf-cleanup")
            self.assertEqual(output.stat().st_size, 900)
            self.assertEqual(len(commands), 1)

    def test_mutool_cleanup_runs_when_qpdf_misses_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                target = cleanup_output_path_from(command)
                if command[0] == "fake-qpdf":
                    target.write_bytes(b"q" * 3000)
                else:
                    target.write_bytes(b"m" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_qpdf",
                return_value=Path("fake-qpdf"),
            ), patch(
                "salbotics_filecompressor.compressor.find_mutool",
                return_value=Path("fake-mutool"),
            ), patch(
                "salbotics_filecompressor.compressor.find_ghostscript",
                side_effect=AssertionError("Ghostscript should not be needed"),
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1),
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "mutool-cleanup")
            self.assertEqual(output.stat().st_size, 900)
            self.assertEqual([command[0] for command in commands], ["fake-qpdf", "fake-mutool"])

    def test_pdf_cleanup_failure_falls_back_to_ghostscript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                if command[0] == "fake-qpdf":
                    return subprocess.CompletedProcess(
                        args=command,
                        returncode=1,
                        stdout="",
                        stderr="qpdf failed",
                    )

                output_path_from(command).write_bytes(b"p" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_qpdf",
                return_value=Path("fake-qpdf"),
            ), patch(
                "salbotics_filecompressor.compressor.find_mutool",
                return_value=None,
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1),
                    gs_path="fake-gs",
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "preserve-text:150dpi:q75")
            self.assertEqual(commands[0][0], "fake-qpdf")
            self.assertEqual(commands[1][0], "fake-gs")

    def test_grayscale_pdf_skips_qpdf_and_mutool_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                output_path_from(command).write_bytes(b"p" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_qpdf",
                return_value=Path("fake-qpdf"),
            ), patch(
                "salbotics_filecompressor.compressor.find_mutool",
                return_value=Path("fake-mutool"),
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1, grayscale=True),
                    gs_path="fake-gs",
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "preserve-text:150dpi:q75")
            self.assertTrue(commands)
            self.assertTrue(all(command[0] == "fake-gs" for command in commands))

    def test_selects_first_preserve_candidate_under_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 4000)
            sizes = [3000, 900, 500, 400]

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                target = output_path_from(command)
                target.write_bytes(b"p" * sizes.pop(0))
                return completed()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=1),
                gs_path="fake-gs",
                run_command=fake_runner,
            )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "preserve-text:120dpi:q65")
            self.assertEqual(output.stat().st_size, 900)

    def test_raster_fallback_can_meet_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                target = output_path_from(command)
                if "-sDEVICE=pdfwrite" in command:
                    target.write_bytes(b"p" * 3000)
                    return completed()

                target.parent.mkdir(exist_ok=True)
                image = Image.new("RGB", (16, 16), "white")
                image.save(target.parent / "page-0001.jpg", "JPEG", quality=35)
                return completed()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=2),
                gs_path="fake-gs",
                run_command=fake_runner,
            )

            self.assertEqual(result.status, "success")
            self.assertTrue(result.mode.startswith("raster:"))
            self.assertLessEqual(output.stat().st_size, 2 * 1024)

    def test_miss_target_saves_smallest_candidate_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "large.pdf"
            output = root / "out.pdf"
            source.write_bytes(b"x" * 5000)

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                target = output_path_from(command)
                if "-sDEVICE=pdfwrite" in command:
                    target.write_bytes(b"p" * 3000)
                    return completed()

                target.parent.mkdir(exist_ok=True)
                image = Image.new("RGB", (64, 64), "white")
                image.save(target.parent / "page-0001.jpg", "JPEG", quality=35)
                return completed()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=1),
                gs_path="fake-gs",
                run_command=fake_runner,
            )

            self.assertEqual(result.status, "warning")
            self.assertIn("target not reached", result.warning or "")
            self.assertGreater(output.stat().st_size, 0)

    def test_batch_continues_after_one_failed_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "out"
            good = root / "good.pdf"
            missing = root / "missing.pdf"
            good.write_bytes(b"%PDF tiny")

            results = compress_batch(
                [good, missing],
                output_dir,
                CompressionOptions(target_kb=499),
                gs_path="fake-gs",
                run_command=lambda command: completed(),
            )

            self.assertEqual([result.status for result in results], ["already-under-target", "failed"])
            self.assertTrue((output_dir / "good_compressed.pdf").exists())

    def test_jpeg_can_compress_to_same_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "photo.jpg"
            output = root / "photo_compressed.jpg"
            image = Image.effect_noise((900, 900), 80).convert("RGB")
            image.save(source, "JPEG", quality=95)
            image.close()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=60, image_output=IMAGE_OUTPUT_SAME_FORMAT),
            )

            self.assertTrue(output.exists())
            self.assertEqual(output.suffix, ".jpg")
            self.assertIn(result.status, {"success", "warning"})
            self.assertTrue(result.mode.startswith("image:"))
            self.assertGreater(result.original_size_bytes, result.final_size_bytes)

    def test_png_can_compress_to_same_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "diagram.png"
            output = root / "diagram_compressed.png"
            image = Image.effect_noise((600, 600), 80).convert("RGB")
            image.save(source, "PNG")
            image.close()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=120, image_output=IMAGE_OUTPUT_SAME_FORMAT),
            )

            self.assertTrue(output.exists())
            self.assertEqual(output.suffix, ".png")
            self.assertIn(result.status, {"success", "warning"})
            self.assertTrue(result.mode.startswith("image:"))
            self.assertGreater(result.final_size_bytes, 0)

    def test_image_can_output_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "photo.jpg"
            output = root / "photo_compressed.pdf"
            image = Image.new("RGB", (400, 400), "white")
            image.save(source, "JPEG", quality=90)
            image.close()

            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=499, image_output=IMAGE_OUTPUT_PDF),
            )

            self.assertTrue(output.exists())
            self.assertEqual(output.suffix, ".pdf")
            self.assertEqual(output.read_bytes()[:4], b"%PDF")
            self.assertTrue(result.mode.startswith("image-pdf:"))

    def test_webp_uses_imagemagick_for_same_format_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "graphic.webp"
            output = root / "graphic_compressed.webp"
            source.write_bytes(b"fake-webp" * 200)
            commands: list[list[str]] = []

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                commands.append(command)
                magick_output_path_from(command).write_bytes(b"w" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_magick",
                return_value=Path("fake-magick"),
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1, image_output=IMAGE_OUTPUT_SAME_FORMAT),
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "magick:100%:q85")
            self.assertEqual(output.suffix, ".webp")
            self.assertEqual(output.stat().st_size, 900)
            self.assertEqual(commands[0][0], "fake-magick")
            self.assertIn("-strip", commands[0])
            self.assertIn("-quality", commands[0])

    def test_tiff_uses_imagemagick_for_pdf_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "scan.tiff"
            output = root / "scan_compressed.pdf"
            source.write_bytes(b"fake-tiff" * 200)

            def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
                magick_output_path_from(command).write_bytes(b"%PDF" + b"p" * 900)
                return completed()

            with patch(
                "salbotics_filecompressor.compressor.find_magick",
                return_value=Path("fake-magick"),
            ):
                result = compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1, image_output=IMAGE_OUTPUT_PDF),
                    run_command=fake_runner,
                )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.mode, "magick-pdf:100%:q85")
            self.assertEqual(output.suffix, ".pdf")
            self.assertEqual(output.read_bytes()[:4], b"%PDF")

    def test_extended_image_fails_clearly_without_imagemagick(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "graphic.webp"
            output = root / "graphic_compressed.webp"
            source.write_bytes(b"fake-webp" * 400)

            with patch(
                "salbotics_filecompressor.compressor.find_magick",
                return_value=None,
            ), self.assertRaisesRegex(CompressionFailedError, "ImageMagick is required"):
                compress_file(
                    source,
                    output,
                    CompressionOptions(target_kb=1, image_output=IMAGE_OUTPUT_SAME_FORMAT),
                )

    def test_batch_processes_supported_files_and_skips_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "out"
            pdf = root / "doc.pdf"
            jpg = root / "photo.jpg"
            txt = root / "notes.txt"
            pdf.write_bytes(b"%PDF tiny")
            image = Image.new("RGB", (80, 80), "white")
            image.save(jpg, "JPEG", quality=90)
            image.close()
            txt.write_text("not supported")

            results = compress_batch(
                [pdf, jpg, txt],
                output_dir,
                CompressionOptions(target_kb=499, image_output=IMAGE_OUTPUT_PDF),
                gs_path="fake-gs",
                run_command=lambda command: completed(),
            )

            self.assertEqual(
                [results[0].status, results[2].status],
                ["already-under-target", "skipped"],
            )
            self.assertIn(results[1].status, {"success", "warning"})
            self.assertTrue((output_dir / "doc_compressed.pdf").exists())
            self.assertTrue((output_dir / "photo_compressed.pdf").exists())
            self.assertFalse((output_dir / "notes.txt").exists())


if __name__ == "__main__":
    unittest.main()
