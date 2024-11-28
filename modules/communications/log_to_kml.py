"""
Convert log file to KML file.
"""

import pathlib
import re

from modules.common.modules.kml.kml_conversion import positions_to_kml
from modules.common.modules.position_global_relative_altitude import PositionGlobalRelativeAltitude


def convert_log_to_kml(
    log_file: str, document_name_prefix: str, save_directory: str
) -> "tuple[bool, pathlib.Path | None]":
    """Given a log file with a specific format, return a corresponding KML file.

    Args:
        log_file (str): Path to the log file
        document_name_prefix (str): Prefix name for saved KML file.
        save_directory (str): Directory to save the KML file to.

    Returns:
        tuple[bool, pathlib.Path | None]: Returns (False, None) if function
            failed to execute, otherwise (True, path) where path a pathlib.Path
            object pointing to the KML file.
    """
    positions = []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                # find all the latitudes and longitudes within the line
                latitudes = re.findall(r"latitude: (-?\d+\.\d+)", line)
                longitudes = re.findall(r"longitude: (-?\d+\.\d+)", line)
                altitudes = re.findall(r"altitude: (-?\d+\.\d+)", line)

                # we must find equal number of latitude and longitude numbers,
                # otherwise that means the log file is improperly formatted or
                # the script failed to detect all locations
                if not len(latitudes) == len(longitudes) == len(altitudes):
                    print("Number of latitudes, longitudes and latitudes found are different.")
                    print("Number of latitudes:", len(latitudes))
                    print("Number of longitudes:", len(longitudes))
                    print("Number of altitudes:", len(altitudes))
                    return False, None

                latitudes = list(map(float, latitudes))
                longitudes = list(map(float, longitudes))
                altitudes = list(map(float, altitudes))

                for i, latitude in enumerate(latitudes):
                    success, location = PositionGlobalRelativeAltitude.create(
                        latitude, longitudes[i], altitudes[i]
                    )
                    if not success:
                        return False, None
                    positions.append(location)

            return positions_to_kml(positions, document_name_prefix, save_directory)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as e:
        print(e.with_traceback())
        return False, None
