"""
Convert log file to KML file.
"""

import argparse
import pathlib
import re

from .common.modules.kml import kml_conversion
from .common.modules import location_global


def _convert_communication_log_to_kml(
    log_file: str, document_name_prefix: str, save_directory: pathlib.Path
) -> bool:
    """
    Given a communications log file, write it to a KML file.

    Args:
        log_file (str): Path to the communications log file
        document_name_prefix (str): Prefix name for saved KML file.
        save_directory (pathlib.Path): Directory to save the KML file to.

    Returns:
        bool: True on success, False otherwise.
    """
    locations = []

    for line in log_file.split("\n"):
        # Use the timestamp (hh:mm:ss) as the name of the marker in the KML file
        time = line[:8]
        # find all the latitudes and longitudes within the line
        latitudes = re.findall(r"latitude: (-?\d+\.\d+)", line)
        longitudes = re.findall(r"longitude: (-?\d+\.\d+)", line)

        # we must find equal number of latitude and longitude numbers,
        # otherwise that means the log file is improperly formatted or
        # the script failed to detect all locations
        if len(latitudes) != len(longitudes):
            print("Number of latitudes and longitudes found are different.")
            print(f"# of altitudes: {len(latitudes)}, # of longitudes: {len(longitudes)}")
            return False, None

        # Convert list of strings to list of floats
        latitudes = list(map(float, latitudes))
        longitudes = list(map(float, longitudes))

        # Cannot use for each loop here, iterating through both lists at the same time
        # pylint: disable-next=consider-using-enumerate
        for i in range(len(latitudes)):
            result, location = location_global.NamedLocationGlobal.create(
                f"{time} {i}", latitudes[i], longitudes[i]
            )
            if not result:
                print(f"Failed to create location for time {time} and index {i}.")
                return False, None

            locations.append(location)

    result, path = kml_conversion.named_locations_to_kml(
        locations, document_name_prefix, save_directory
    )
    return result


def convert_communication_log_to_kml(
    log_file_path: pathlib.Path, document_name_prefix: str, save_directory: pathlib.Path
) -> bool:
    """
    Given a communications log file, create a KML of the entire file and a KML
    for the last line.

    Args:
        log_file_path (pathlib.Path): Path to the communications log file
        document_name_prefix (str): Prefix name for saved KML files.
        save_directory (str): Directory to save the KML files to.

    Returns:
        bool: True on success, False otherwise.
    """
    with open(log_file_path, "r", encoding="utf-8") as log_file:
        content = log_file.read().strip()

        # Convert the entire log file to KML file
        result = _convert_communication_log_to_kml(content, document_name_prefix, save_directory)
        if not result:
            print(f"Failed to convert {log_file_path} to KML.")
            return False

        # Convert only the last line to KML file
        result = _convert_communication_log_to_kml(
            content.split("\n")[-1], document_name_prefix + "_last_line", save_directory
        )
        if not result:
            print(f"Failed to convert {log_file_path} to KML.")
            return False
    return True


# similar main to other logs to kml scripts
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-path", type=str, required=True, help="path to logs folder")

    args = parser.parse_args()

    conversion_result = convert_communication_log_to_kml(
        args.log_path, "output", pathlib.Path.cwd()
    )
    if conversion_result:
        print("Done!")
    else:
        print("Failed to convert to KML")
