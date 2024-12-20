"""
Test a sample log file.
"""

import filecmp
import pathlib

from modules.communications.log_to_kml import convert_log_to_kml


INPUT_FILE = pathlib.Path("tests", "unit", "communication_logs", "input.log")
OUTPUT_FILE = pathlib.Path("tests", "unit", "communication_logs", "output")
EXPECTED_OUTPUT_FILE = pathlib.Path("tests", "unit", "communication_logs", "expected_output.kml")


def test_convert_log_to_kml() -> None:
    """
    Compare the output file of convert_log_to_kml to the expected KML file.
    """
    success, output_path = convert_log_to_kml(INPUT_FILE, OUTPUT_FILE.name, OUTPUT_FILE.parent)
    try:
        assert success, "convert_log_to_kml failed."

        assert filecmp.cmp(
            str(output_path), str(EXPECTED_OUTPUT_FILE), shallow=False
        ), "Generated KML doesn't match expected output"
    finally:
        if success:
            output_path.unlink()
