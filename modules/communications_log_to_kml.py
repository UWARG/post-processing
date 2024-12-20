"""
Convert log file to KML file.
"""

import argparse
import pathlib
import re

from .common.modules.kml import kml_conversion
from .common.modules import location_global


DEFAULT_RESULTS_PATH = pathlib.Path("results")


def convert_communication_log_to_kml(
    log_file_path: pathlib.Path, document_name_prefix: str, save_directory: pathlib.Path
) -> "tuple[bool, pathlib.Path | None]":
    """
    Given a communications log file with a specific format, return a corresponding KML file.

    Args:
        log_file (str): Path to the communications log file
        document_name_prefix (str): Prefix name for saved KML file.
        save_directory (str): Directory to save the KML file to.

    Returns:
        tuple[bool, pathlib.Path | None]: Returns (False, None) if function
            failed to execute, otherwise (True, path) where path a pathlib.Path
            object pointing to the KML file.
    """
    locations = []

    with open(log_file_path, "r", encoding="utf-8") as log_file:
        for line in log_file:
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
                    time + " " + i, latitudes[i], longitudes[i]
                )
                if not result:
                    return False, None
                locations.append(location)

    return kml_conversion.named_locations_to_kml(locations, document_name_prefix, save_directory)


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

    pathlib.Path(args.output_dir).mkdir(exist_ok=True, parents=True)
    result, path = convert_communication_log_to_kml(
        args.log_path, args.document_prefix_name, args.output_dir
    )
    if result:
        print("Done!")
    else:
        print("Failed to convert to KML")
