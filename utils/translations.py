"""Generate translations from LANG named tuples."""

import argparse
import json
from pathlib import Path

import black
from black import Mode


def generate(args: argparse.Namespace) -> None:  # pylint: disable=unused-argument
    """Generate python dictionary from language files."""

    # Get all the JSON files in the translations directory
    translation_files = Path("hdate/translations").glob("*.json")
    translations = {}
    for translation_file in sorted(translation_files):
        translations[translation_file.stem] = json.loads(
            translation_file.read_text(encoding="utf-8")
        )

    # Generate the python file
    python_file = Path("hdate/translations.py")
    file_contents = f'''
"""
This file was generated by utils/translations.py
Do not edit this file manually.
"""

# pylint: disable=line-too-long
# flake8: noqa: E501

TRANSLATIONS = {json.dumps(translations, ensure_ascii=False, indent=4)}
'''
    python_file.write_text(
        black.format_file_contents(file_contents, fast=False, mode=Mode()),
        encoding="utf-8",
    )


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    python_generator = subparsers.add_parser("generate", help="generate translations")
    python_generator.set_defaults(func=generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
