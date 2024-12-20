"""
Convert log file to KML file.
"""

import pathlib
import re

from modules.common.modules.kml.kml_conversion import named_positions_to_kml
from modules.common.modules.mavlink.local_global_conversion import (
    position_global_from_position_local,
)
from modules.common.modules.position_global import PositionGlobal
from modules.common.modules.position_global_relative_altitude import (
    NamedPositionGlobalRelativeAltitude,
)
from modules.common.modules.position_local import PositionLocal


def convert_log_to_kml(
    log_file: str, document_name_prefix: str, save_directory: str
) -> "tuple[bool, pathlib.Path | None]":
    """Given a log file with a specific format, generate a corresponding KML file.

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
    float_regex = r"-?\d+\.\d+"

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # the first line is discarded
            f.readline()
            # the second line includes the home location
            line = f.readline()

            origin_latitude = float(re.search(rf"latitude: ({float_regex})", line).group(1))
            origin_longitude = float(re.search(rf"longitude: ({float_regex})", line).group(1))
            origin_altitude = float(re.search(rf"altitude: ({float_regex})", line).group(1))

            # relative altitude with respect to itself is zero
            success, home_position = PositionGlobal.create(
                origin_latitude, origin_longitude, origin_altitude
            )
            if not success:
                return False, None

            success, home_position_relative_altitude = NamedPositionGlobalRelativeAltitude.create(
                "Home location", origin_latitude, origin_longitude, 0
            )
            if not success:
                return False, None
            positions.append(home_position_relative_altitude)

            # read the lines, two at a time
            while True:
                line1 = f.readline()
                if not line1:  # no more lines to read
                    break
                line2 = f.readline()

                # in meters
                north = float(re.search(rf"north: ({float_regex})", line2).group(1))
                east = float(re.search(rf"east: ({float_regex})", line2).group(1))
                down = float(re.search(rf"down: ({float_regex})", line2).group(1))

                print(north, east, down)

                timestamp = re.search(rf"time: ({float_regex})", line1).group(1)
                yaw, pitch, roll = re.search(
                    rf"YPR radians: ({float_regex}), ({float_regex}), ({float_regex})", line2
                ).group(1, 2, 3)

                success, local_position = PositionLocal.create(north, east, down)
                if not success:
                    return False, None

                success, converted_position = position_global_from_position_local(
                    home_position, local_position
                )
                if not success:
                    return False, None

                success, converted_position_relative_altitude = (
                    NamedPositionGlobalRelativeAltitude.create(
                        f"Time: {timestamp}, YPR radians: {yaw}, {pitch}, {roll}",
                        converted_position.latitude,
                        converted_position.longitude,
                        converted_position.altitude - origin_altitude,
                    )
                )
                if not success:
                    return False, None
                positions.append(converted_position_relative_altitude)
            return named_positions_to_kml(positions, document_name_prefix, save_directory)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as e:
        print(e)
        return False, None
