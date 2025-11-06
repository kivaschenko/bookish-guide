#!/usr/bin/env python3
"""
Convert B-roll timing format from array to rushes object format
"""

import json
import sys
import os


def convert_timing_format(input_file, output_file):
    """Convert timing file from array format to rushes object format"""

    print(f"🔄 Converting {input_file} to {output_file}")

    # Read the array format
    with open(input_file, "r", encoding="utf-8") as f:
        timing_array = json.load(f)

    print(f"📊 Found {len(timing_array)} timing entries")

    # Convert to rushes format
    rushes_format = {"rushes": {}}

    # Group by rush (audio file)
    for entry in timing_array:
        rush = entry["rush"]
        if rush not in rushes_format["rushes"]:
            rushes_format["rushes"][rush] = []
        rushes_format["rushes"][rush].append(entry)

    # Save in the expected format
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rushes_format, f, indent=2, ensure_ascii=False)

    print(f"✅ Converted successfully!")
    print(f"📁 Output saved to: {output_file}")

    # Show structure
    for rush, entries in rushes_format["rushes"].items():
        print(f"  🎵 {rush}: {len(entries)} segments")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_timing_format.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = (
        sys.argv[2] if len(sys.argv) > 2 else "temp/broll_timing_converted.json"
    )

    if not os.path.exists(input_file):
        print(f"❌ Error: Input file {input_file} not found")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(
        os.path.dirname(output_file) if os.path.dirname(output_file) else ".",
        exist_ok=True,
    )

    convert_timing_format(input_file, output_file)
