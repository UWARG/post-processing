"""
Convert log file to KML file.
"""

import argparse
import pathlib
import re

from ..common.modules import location_global
from ..common.modules import location_local
from ..common.modules import position_global
from ..common.modules.kml import kml_conversion
from ..common.modules.mavlink import local_global_conversion


DEFAULT_RESULTS_PATH = pathlib.Path("results")


def convert_geolocation_log_to_kml(
    log_file: pathlib.Path,
    home_position: position_global.PositionGlobal,
    document_name_prefix: str,
    save_directory: pathlib.Path,
) -> bool:
    """
    Given a geolocation log file, generate a KML file.

    Args:
        log_file (pathlib.Path): Path to the geolocation log file
        document_name_prefix (str): Prefix name for saved KML file.
        save_directory (pathlib.Path): Directory to save the KML file to.

    Returns:
        bool: True on success, False otherwise.
    """
    locations = []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            # Use the timestamp (hh:mm:ss) as the name of the marker in the KML file
            time = line[:8]

            # find all the points within the line (should be just 1)
            points = re.findall(
                r"centre: \[.*\]", line
            )  # format: [ 'centre:', '[', '123.123', '123.123]' ]

            if len(points) > 0:
                point = points[0].split()
                north = float(point[2])
                east = float(point[3][:-1])
                result, local_location = location_local.LocationLocal.create(north, east)
                if not result:
                    print("Failed creating LocationLocal")
                    return False

                result, global_position = (
                    local_global_conversion.position_global_from_location_local(
                        home_position, local_location
                    )
                )
                if not result:
                    print("Failed converting from LocationLocal to PositionGlobal")
                    return False

                # must make this named
                result, global_location = location_global.NamedLocationGlobal.create(
                    f"{time}", global_position.latitude, global_position.longitude
                )
                if not result:
                    print("Failed converting from PositionGlobal to LocationGlobal")
                    return False

                locations.append(global_location)

    result, path = kml_conversion.named_locations_to_kml(
        locations, document_name_prefix, save_directory
    )
    return result


def find_home_position(path: pathlib.Path) -> "tuple[bool, position_global.PositionGlobal | None]":
    """
    Parses a log file to find the home position coordinates.

    Args:
        path (pathlib.Path): The path to the log file.

    Returns:
        tuple: A tuple containing a boolean and a PositionGlobal object or None.
               The boolean is True if the home position was found, otherwise False.
               The PositionGlobal object contains the latitude, longitude, and altitude
               of the home position if found, otherwise None.
    """
    with open(path, "r", encoding="utf-8") as log_file:
        for line in log_file:
            home_position_line = re.findall(r"Home position received: .*", line)
            if len(home_position_line) > 0:
                home_position_parts = home_position_line[0].split()
                return position_global.PositionGlobal.create(
                    float(home_position_parts[6][:-1]),
                    float(home_position_parts[8][:-1]),
                    float(home_position_parts[10]),
                )
    return False, None


# similar main to other logs to kml scripts
# pylint: disable=duplicate-code
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", type=str, required=True, help="path to logs folder")
    parser.add_argument(
        "--document-prefix-name", type=str, default="", help="prefix name for saved KML file"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=str(DEFAULT_RESULTS_PATH),
        help="directory to save KML file to",
    )
    args = parser.parse_args()

    log_dir = pathlib.Path(args.log_path)
    _document_name_prefix = args.document_prefix_name
    output_dir = pathlib.Path(args.output_dir)

    # Create the output directory if it doesn't exist already
    output_dir.mkdir(exist_ok=True, parents=True)

    communication_file_path = next(log_dir.glob("communications_worker_[0-9]*.log"))
    _result, _home_position = find_home_position(communication_file_path)

    if not _result:
        print("Cannot find home position")
    else:
        geolocation_file_path = next(log_dir.glob("geolocation_worker_[0-9]*.log"))
        _result = convert_geolocation_log_to_kml(
            geolocation_file_path, _home_position, _document_name_prefix, output_dir
        )

    if _result:
        print("Done!")
    else:
        print("Failed to convert to KML")
