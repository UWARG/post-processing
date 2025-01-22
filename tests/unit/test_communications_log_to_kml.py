"""
Test converting geolocation logs to KML files.
The inputs come from input_logs/ and the expected outputs are in output_kmls/.
"""

import pathlib
import shutil
from typing import Generator

import pytest

from modules.log_parser import communications_log_to_kml

input_dir = pathlib.Path(__file__).parent / "input_logs"
expected_output_dir = pathlib.Path(__file__).parent / "output_kmls"


@pytest.fixture
def output_dir() -> Generator[pathlib.Path, None, None]:
    """Output directory for generated KML files"""
    path = pathlib.Path(__file__).parent / "__temp__"
    path.mkdir()

    yield path

    if path.exists():
        shutil.rmtree(path)


# The parameter name must be the same as the pytest.fixture function name
# pylint: disable=redefined-outer-name
def test_convert_communication_log_to_kml(output_dir: pathlib.Path) -> None:
    """Test converting communication log to KML"""
    log_file = input_dir / "communications_worker_2023.log"
    document_name_prefix = log_file.stem

    result = communications_log_to_kml.convert_communication_log_to_kml(
        log_file, document_name_prefix, output_dir
    )
    assert result

    generated_kml_file = next(output_dir.glob(f"{document_name_prefix}_[0-9]*.kml"))
    expected_kml_file = expected_output_dir / f"{document_name_prefix}.kml"

    # Compare file contents of generated vs actual KML files
    with open(generated_kml_file, "r", encoding="utf-8") as f:
        with open(expected_kml_file, "r", encoding="utf-8") as g:
            assert f.read().strip() == g.read().strip()

    generated_kml_file = next(output_dir.glob(f"{document_name_prefix}_last_line_[0-9]*.kml"))
    expected_kml_file = expected_output_dir / f"{document_name_prefix}_last_line.kml"

    with open(generated_kml_file, "r", encoding="utf-8") as f:
        with open(expected_kml_file, "r", encoding="utf-8") as g:
            assert f.read().strip() == g.read().strip()
