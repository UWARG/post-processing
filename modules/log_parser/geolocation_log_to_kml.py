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
) -> "tuple[bool, pathlib.Path | None]":
    """
    Given a geolocation log file with a specific format, return a corresponding KML file.

    Args:
        log_file (str): Path to the geolocation log file
        document_name_prefix (str): Prefix name for saved KML file.
        save_directory (str): Directory to save the KML file to.

    Returns:
        tuple[bool, pathlib.Path | None]: Returns (False, None) if function
            failed to execute, otherwise (True, path) where path a pathlib.Path
            object pointing to the KML file.
    """
    locations = []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
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
                    return False, None

                result, global_position = (
                    local_global_conversion.position_global_from_location_local(
                        home_position, local_location
                    )
                )
                if not result:
                    print("Failed converting from LocationLocal to PositionGlobal")
                    return False, None

                result, global_location = location_global.LocationGlobal.create(
                    global_position.latitude, global_position.longitude
                )
                if not result:
                    print("Failed converting from PositionGlobal to LocationGlobal")
                    return False, None

                locations.append(global_location)

        return kml_conversion.locations_to_kml(locations, document_name_prefix, save_directory)


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

    log_file_path = pathlib.Path(args.log_path)
    _document_name_prefix = args.document_prefix_name
    output_dir = pathlib.Path(args.output_dir)

    # Create the output directory if it doesn't exist already
    output_dir.mkdir(exist_ok=True, parents=True)

    communication_file_path = next(log_file_path.glob("communications_worker*"))
    _result, _home_position = find_home_position(communication_file_path)

    if not _result:
        print("Cannot find home position")
    else:
        geolocation_file_path = next(log_file_path.glob("geolocation_worker*"))
        _result, _path = convert_geolocation_log_to_kml(
            geolocation_file_path, _home_position, _document_name_prefix, output_dir
        )

    if _result:
        print("Done!")
    else:
        print("Failed to convert to KML")
