import argparse
import json
from io import TextIOWrapper
from pathlib import Path
from typing import List


class LogEntryReader:
    _line = ""
    _timestamp = None

    def __init__(self, source: TextIOWrapper) -> None:
        self._source = source

    def readline(self):
        self._line = self._source.readline()
        # Recalculate timestamp if possible
        if self._line:
            self._timestamp = json.loads(self._line)["timestamp"]
        else:
            self._timestamp = None
        return self._line

    @property
    def line(self):
        return self._line

    @property
    def timestamp(self):
        return self._timestamp


def parse_args():
    parser = argparse.ArgumentParser(description="Log merge tool")

    parser.add_argument(
        "logs", metavar="<INPUT>", type=str, nargs=2, help="log files to merge"
    )
    parser.add_argument(
        "-o",
        metavar="<OUTPUT>",
        dest="output",
        required=True,
        help="path to the output log",
    )

    return parser.parse_args()


def verify_files(inputs: List[Path], output: Path) -> None:
    # Inputs should exist and be files
    for input in inputs:
        if not input.exists() or not input.is_file():
            raise FileNotFoundError(f"Log file at {input} not found")
    # Output should not exist
    if output.exists():
        raise FileExistsError("Log file {output} already exists")


def make_subdirectories(output: Path):
    subdir = output.parent
    subdir.mkdir(parents=True)


def merge_logs(inputs: List[Path], output: Path) -> None:
    # Get the file handlers
    out_file = open(output, "w")
    # Left and right are just aliases for convenience
    left_file = open(inputs[0], "r")
    right_file = open(inputs[1], "r")

    # Set up readers
    left_reader = LogEntryReader(left_file)
    right_reader = LogEntryReader(right_file)
    # Init
    left_reader.readline()
    right_reader.readline()
    # Loop while we have content in both
    while all((left_reader.line, right_reader.line)):
        # Select necessary reader
        if left_reader.timestamp < right_reader.timestamp:
            reader = left_reader
        else:
            reader = right_reader
        # Write and move to next line
        out_file.write(reader.line)
        reader.readline()

    # Finish by writing the leftovers
    for reader in (left_reader, right_reader):
        while reader.line:
            out_file.write(reader.line)
            reader.readline()

    # Close files
    out_file.close()
    left_file.close()
    right_file.close()


def main():
    args = parse_args()
    inputs = [Path(x) for x in args.logs]
    output = Path(args.output)

    verify_files(inputs, output)
    make_subdirectories(output)
    merge_logs(inputs, output)


if __name__ == "__main__":
    main()
