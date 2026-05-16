from __future__ import annotations

import unittest
from unittest.mock import patch

from salbotics_filecompressor.cli import build_parser, main


class CliParserTests(unittest.TestCase):
    def test_image_output_defaults_to_same_format(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.jpg", "-o", "output.jpg"])

        self.assertEqual(args.image_output, "same-format")

    def test_image_output_accepts_pdf(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.png", "-o", "output.pdf", "--image-output", "pdf"])

        self.assertEqual(args.image_output, "pdf")

    def test_list_engines_exits_without_input_file(self) -> None:
        with patch(
            "salbotics_filecompressor.cli.format_engine_table",
            return_value="Engine table",
        ), patch("builtins.print") as mocked_print:
            exit_code = main(["--list-engines"])

        self.assertEqual(exit_code, 0)
        mocked_print.assert_called_once_with("Engine table")

    def test_list_formats_exits_without_input_file(self) -> None:
        with patch(
            "salbotics_filecompressor.cli.format_supported_formats",
            return_value="Format table",
        ), patch("builtins.print") as mocked_print:
            exit_code = main(["--list-formats"])

        self.assertEqual(exit_code, 0)
        mocked_print.assert_called_once_with("Format table")


if __name__ == "__main__":
    unittest.main()
