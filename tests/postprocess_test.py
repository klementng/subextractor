import os
import tempfile
import unittest
from pathlib import Path

import pysubs2
import yaml

from postprocessing import SubtitleFormatter


class TestSubtitlePostprocessing(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        self.output_files = []
        self.temp_dir = tempfile.mkdtemp()
        super().__init__(methodName)

    def setUp(self) -> None:

        # Create test config
        config_data = {
            "ass": {
                "tasks": [
                    {
                        "selectors": [
                            {"uses": "info_select_current_info", "id": "old_info"}
                        ],
                        "actions": [
                            {
                                "uses": "info_action_update",
                                "with": {
                                    "PlayResX": 1920,
                                    "PlayResY": 1080,
                                    "Title": "Processed by PostProcessor",
                                },
                            }
                        ],
                    }
                ]
            },
            "srt": {
                "tasks": [
                    {
                        "selectors": [{"uses": "events_select_all"}],
                        "actions": [
                            {
                                "uses": "events_action_update_properties",
                                "with": {"style": "Default"},
                            }
                        ],
                    }
                ]
            },
        }

        # Save config file
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)

    def test_ass_processing(self):
        # Create test ASS file
        test_file = Path(self.temp_dir) / "test.ass"
        ssafile = pysubs2.SSAFile()

        # Set original properties
        ssafile.info["PlayResX"] = "1280"
        ssafile.info["PlayResY"] = "720"
        ssafile.info["Title"] = "Original Title"

        # Add test events
        event1 = pysubs2.SSAEvent(start=1000, end=3000, text="Hello World")
        event2 = pysubs2.SSAEvent(start=4000, end=6000, text="Test subtitle")
        ssafile.events.extend([event1, event2])

        # Save test file
        ssafile.save(str(test_file))
        self.output_files.append(str(test_file))

        # Process with formatter
        formatter = SubtitleFormatter(str(self.config_path))
        result = pysubs2.load(formatter.format(str(test_file))[0])

        # Verify processing
        self.assertIsNotNone(result)
        self.assertEqual(result.info["PlayResX"], "1920")
        self.assertEqual(result.info["PlayResY"], "1080")
        self.assertEqual(result.info["Title"], "Processed by PostProcessor")
        self.assertGreater(os.path.getsize(test_file), 0)

    def test_srt_processing(self):
        # Create test SRT file
        test_file = Path(self.temp_dir) / "test.srt"
        ssafile = pysubs2.SSAFile()

        # Add test events
        event1 = pysubs2.SSAEvent(start=1000, end=3000, text="First subtitle")
        event2 = pysubs2.SSAEvent(start=4000, end=6000, text="Second subtitle")
        ssafile.events.extend([event1, event2])

        # Save as SRT
        ssafile.save(str(test_file))
        self.output_files.append(str(test_file))

        # Process with formatter
        formatter = SubtitleFormatter(str(self.config_path))
        result = pysubs2.load(formatter.format(str(test_file))[0])

        # Verify processing
        self.assertIsNotNone(result)
        self.assertEqual(len(result.events), 2)
        self.assertGreater(os.path.getsize(test_file), 0)

    def test_unsupported_format(self):
        # Create test file with unsupported extension
        test_file = Path(self.temp_dir) / "test.vtt"
        test_file.write_text("WEBVTT\n\n00:01.000 --> 00:03.000\nTest subtitle")
        self.output_files.append(str(test_file))

        # Process with formatter - should raise error
        formatter = SubtitleFormatter(str(self.config_path))

        with self.assertRaises(RuntimeError):
            formatter.format(str(test_file))

    def test_scaling_workflow(self):
        # Create comprehensive scaling config with separate tasks for different operations
        scaling_config = {
            "ass": {
                "tasks": [
                    # Task 1: Update info
                    {
                        "selectors": [
                            {"uses": "info_select_current_info", "id": "old_info"}
                        ],
                        "actions": [
                            {
                                "uses": "info_action_update",
                                "with": {
                                    "PlayResX": "{{int(outputs['old_info'][0]['PlayResX']) * 2}}",
                                    "PlayResY": "{{int(outputs['old_info'][0]['PlayResY']) * 2}}",
                                },
                            }
                        ],
                    },
                    # Task 2: Scale styles
                    {
                        "selectors": [{"uses": "styles_select_all"}],
                        "actions": [
                            {
                                "uses": "styles_action_scale",
                                "with": {
                                    "x_old": "{{int(outputs['old_info'][0]['PlayResX'])}}",
                                    "y_old": "{{int(outputs['old_info'][0]['PlayResY'])}}",
                                    "x_new": "{{int(outputs['old_info'][0]['PlayResX']) * 2}}",
                                    "y_new": "{{int(outputs['old_info'][0]['PlayResY']) * 2}}",
                                },
                            }
                        ],
                    },
                ]
            }
        }

        # Save scaling config
        scaling_config_path = Path(self.temp_dir) / "scaling_config.yaml"
        with open(scaling_config_path, "w") as f:
            yaml.dump(scaling_config, f)

        # Create test file with styles
        test_file = Path(self.temp_dir) / "scaling_test.ass"
        ssafile = pysubs2.SSAFile()

        ssafile.info["PlayResX"] = "1280"
        ssafile.info["PlayResY"] = "720"

        # Add style
        style = pysubs2.SSAStyle()
        style.fontsize = 20
        style.marginl = 10
        style.marginr = 10
        style.marginv = 10
        ssafile.styles["Default"] = style

        ssafile.save(str(test_file))
        self.output_files.append(str(test_file))

        # Process scaling
        formatter = SubtitleFormatter(str(scaling_config_path))
        result = pysubs2.load(formatter.format(str(test_file))[0])

        # Verify scaling
        self.assertEqual(result.info["PlayResX"], "2560")  # 1280 * 2
        self.assertEqual(result.info["PlayResY"], "1440")  # 720 * 2
        self.assertEqual(result.styles["Default"].fontsize, 40)  # 20 * 2

    def test_simple_info_update(self):
        # Simple test for info updates only
        test_file = Path(self.temp_dir) / "info_test.ass"
        ssafile = pysubs2.SSAFile()

        ssafile.info["PlayResX"] = "1280"
        ssafile.info["PlayResY"] = "720"
        ssafile.info["Title"] = "Original"

        ssafile.save(str(test_file))
        self.output_files.append(str(test_file))

        # Process with basic config
        formatter = SubtitleFormatter(str(self.config_path))
        result = pysubs2.load(formatter.format(str(test_file))[0])

        # Verify
        self.assertEqual(result.info["Title"], "Processed by PostProcessor")
        self.assertEqual(result.info["PlayResX"], "1920")
        self.assertEqual(result.info["PlayResY"], "1080")

    def test_template_variables(self):
        # Test template variable resolution
        template_config = {
            "ass": {
                "tasks": [
                    {
                        "selectors": [
                            {"uses": "info_select_current_info", "id": "current_info"}
                        ],
                        "actions": [
                            {
                                "uses": "info_action_update",
                                "with": {
                                    "Title": "{{outputs['current_info'][0]['Title'] + ' - Modified'}}",
                                    "PlayResX": "{{int(outputs['current_info'][0]['PlayResX']) + 640}}",
                                },
                            }
                        ],
                    }
                ]
            }
        }

        template_config_path = Path(self.temp_dir) / "template_config.yaml"
        with open(template_config_path, "w") as f:
            yaml.dump(template_config, f)

        # Create test file
        test_file = Path(self.temp_dir) / "template_test.ass"
        ssafile = pysubs2.SSAFile()
        ssafile.info["PlayResX"] = "1280"
        ssafile.info["Title"] = "Original Title"

        ssafile.save(str(test_file))
        self.output_files.append(str(test_file))

        # Process
        formatter = SubtitleFormatter(str(template_config_path))
        result = pysubs2.load(formatter.format(str(test_file))[0])

        # Verify template resolution
        self.assertEqual(result.info["Title"], "Original Title - Modified")
        self.assertEqual(result.info["PlayResX"], "1920")  # 1280 + 640

    def tearDown(self) -> None:
        # Clean up output files
        for f in self.output_files:
            if os.path.exists(f):
                os.remove(f)

        # Clean up temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()
