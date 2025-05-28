import logging
import os
import unittest

import extract
import extract.config
import extract.prober

logging.basicConfig(level=logging.DEBUG)


class TestSubtitleExtractor(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        self.output_files = []
        super().__init__(methodName)

    def test_text_extract(self):

        config = extract.config.ExtractorConfig(True, ["vtt", "srt", "ass"])
        probe = extract.prober.MediaProber()
        extractor = extract.TextSubtitleExtractor(config, probe)

        files = extractor.extract("tests/samples/text.mkv")
        self.assertEqual(len(files), 3 * 8)

        for f in files:
            self.assertGreater(os.path.getsize(f), 0)

        self.output_files.extend(files)

    def test_bitmap_extract(self):

        config = extract.config.ExtractorConfig(
            True, ["vtt", "srt", "ass"], unknown_language_as="eng"
        )
        probe = extract.prober.MediaProber()
        extractor = extract.BitmapSubtitleExtractor(config, probe)

        files = extractor.extract("tests/samples/bitmap.mkv")
        self.assertEqual(len(files), 4)

        for f in files:
            self.assertGreater(os.path.getsize(f), 0)

        self.output_files.extend(files)

    def tearDown(self) -> None:
        for f in self.output_files:
            os.remove(f)
