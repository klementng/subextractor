import unittest
import glob
import re
import os

import extract


class TestSubtitleExtractor(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        self.output_files = []
        super().__init__(methodName)

    def test_text_extract(self):
        extractor = extract.SubtitleExtractor(
            formats=["ass", "srt", "vtt"], overwrite=True
        )

        files = extractor.extract("tests/samples/text.mkv")
        self.assertEqual(len(files), 3 * 8)

        for f in files:
            self.assertGreater(os.path.getsize(f), 0)

        self.output_files.extend(files)

    # def test_bitmap_extract(self):
    #     extractor = extract.SubtitleExtractor(formats=['ass','srt','vtt'], overwrite=True)

    #     files = extractor.extract("tests/samples/bitmap.mkv")
    #     self.assertEqual(len(files), 3)

    #     for f in files:
    #         self.assertGreater(os.path.getsize(f), 0)

    #     self.output_files.extend(files)

    def tearDown(self) -> None:
        for f in self.output_files:
            os.remove(f)
