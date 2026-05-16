from __future__ import annotations

import unittest

from salbotics_filecompressor.cli import build_parser


class CliParserTests(unittest.TestCase):
    def test_image_output_defaults_to_same_format(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.jpg", "-o", "output.jpg"])

        self.assertEqual(args.image_output, "same-format")

    def test_image_output_accepts_pdf(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.png", "-o", "output.pdf", "--image-output", "pdf"])

        self.assertEqual(args.image_output, "pdf")


if __name__ == "__main__":
    unittest.main()
