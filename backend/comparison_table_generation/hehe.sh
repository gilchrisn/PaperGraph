#!/bin/bash
# concat_copy.sh
# This script finds all .py files recursively, concatenates their contents,
# and copies the result to the Windows clipboard.

# Create a temporary file to hold the concatenated contents.
tempfile=$(mktemp)

# Loop through each Python file.
find . -type f -name "*.py" | while read file; do
    echo "---------- File: $file ----------" >> "$tempfile"
    cat "$file" >> "$tempfile"
    echo -e "\n" >> "$tempfile"
done

# Copy the concatenated output to the clipboard using clip.exe.
cat "$tempfile" | clip.exe

# Clean up temporary file.
rm "$tempfile"
