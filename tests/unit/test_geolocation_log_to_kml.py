"""
Test converting geolocation logs to KML files.
The inputs come from input_logs/ and the expected outputs are in output_kmls/.
"""

import pathlib
import shutil
from typing import Generator

import pytest

from modules.common.modules import position_global
from modules.log_parser import geolocation_log_to_kml


input_dir = pathlib.Path(__file__).parent / "input_logs"
expected_output_dir = pathlib.Path(__file__).parent / "output_kmls"


@pytest.fixture
def output_dir() -> Generator[pathlib.Path, None, None]:
    """Output directory for generated KML files"""
    path = pathlib.Path(__file__).parent / "__temp__"
    path.mkdir(exist_ok=True)

    yield path

    if path.exists():
        shutil.rmtree(path)


# The parameter name must be the same as the pytest.fixture function name
# pylint: disable=redefined-outer-name
def test_convert_geolocation_log_to_kml(output_dir: pathlib.Path) -> None:
    """Test converting geolocation log to KML"""
    log_file = input_dir / "geolocation_worker_2010.log"
    result, home_position = position_global.PositionGlobal.create(0, 0, 0)
    document_name_prefix = log_file.stem

    assert result

    geolocation_log_to_kml.convert_geolocation_log_to_kml(
        log_file, home_position, document_name_prefix, output_dir
    )

    generated_kml_file = next(output_dir.glob(f"{document_name_prefix}*.kml"))
    expected_kml_file = expected_output_dir / f"{document_name_prefix}.kml"

    # Compare file contents of generated vs actual KML files
    with open(generated_kml_file, "r", encoding="utf-8") as f:
        with open(expected_kml_file, "r", encoding="utf-8") as g:
            assert f.read().strip() == g.read().strip()


def test_find_home_position() -> None:
    """Test extracting home position from log file"""
    log_file = input_dir / "communications_worker_2023.log"

    result, home_position = geolocation_log_to_kml.find_home_position(log_file)

    assert result
    assert abs(43.43374252319336 - home_position.latitude) < 1e-6
    assert abs(-80.57689666748047 - home_position.longitude) < 1e-6
    assert abs(369.3699951171875 - home_position.altitude) < 1e-6
