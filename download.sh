#!/usr/bin/env bash

set -euo pipefail

# Save the original working directory
ORIGINAL_DIR="$(pwd)"

# Always return to the original directory when the script exits
trap 'cd "$ORIGINAL_DIR"' EXIT

# Go to the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

URL="https://zenodo.org/records/22707065/files/zenodo.zip?download=1"
ZIP_FILE="zenodo.zip"
EXTRACT_DIR="zenodo"
TARGET_DIR="datasets"

# ------------------------------------------------------------------
# Download
# ------------------------------------------------------------------

echo "Downloading datasets..."
wget -O "$ZIP_FILE" "$URL"

# ------------------------------------------------------------------
# Extract
# ------------------------------------------------------------------

echo "Extracting datasets..."
mkdir -p "$EXTRACT_DIR"
unzip -q "$ZIP_FILE" -d "$EXTRACT_DIR"

# ------------------------------------------------------------------
# Move contents
# ------------------------------------------------------------------

echo "Moving dataset files..."
mv "$EXTRACT_DIR"/zenodo/biokg/* "$TARGET_DIR"/biokg/
mv "$EXTRACT_DIR"/zenodo/codex/* "$TARGET_DIR"/codex/

# ------------------------------------------------------------------
# Clean up
# ------------------------------------------------------------------

echo "Cleaning up..."
rm -rf "$EXTRACT_DIR"
rm -f "$ZIP_FILE"

# ------------------------------------------------------------------
# Return to original directory
# ------------------------------------------------------------------

cd "$ORIGINAL_DIR"

echo "Done."