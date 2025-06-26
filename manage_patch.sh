#!/bin/bash

# This script applies or reverts the canvas parenting fix for ui.js.
# It allows for controlled testing of the race condition theory.

PATCH_FILE="fix_canvas_parenting.patch"
TARGET_FILE="ui.js"
ACTION=$1

# --- Pre-flight Checks ---

# Check if a valid action was provided
if [[ "$ACTION" != "apply" && "$ACTION" != "revert" ]]; then
    echo "Usage: $0 [apply|revert]"
    echo "  apply  - Applies the patch to fix the DOM parenting issue in $TARGET_FILE."
    echo "  revert - Reverts the patch, restoring $TARGET_FILE to its original state."
    exit 1
fi

# Check if the target file and patch file exist
if [ ! -f "$TARGET_FILE" ]; then
    echo "Error: Target file '$TARGET_FILE' not found in the current directory."
    exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
    echo "Error: Patch file '$PATCH_FILE' not found in the current directory."
    exit 1
fi

# --- Main Logic ---

if [ "$ACTION" == "apply" ]; then
    echo "Attempting to apply patch '$PATCH_FILE' to '$TARGET_FILE'..."
    patch --forward --reject-file=- "$TARGET_FILE" < "$PATCH_FILE"
    if [ $? -eq 0 ]; then
        echo "Patch applied successfully. The canvas views should now render correctly."
        echo "A backup of the original file may have been created as '$TARGET_FILE.orig'."
    else
        echo "Error: Patch command failed. The file might already be patched or have conflicts."
        echo "Check for a '.rej' file for details on failed hunks."
        exit 1
    fi
elif [ "$ACTION" == "revert" ]; then
    echo "Attempting to revert patch on '$TARGET_FILE' using '$PATCH_FILE'..."
    patch --reverse --reject-file=- "$TARGET_FILE" < "$PATCH_FILE"
    if [ $? -eq 0 ]; then
        echo "Patch reverted successfully. The file is back to its original (buggy) state."
    else
        echo "Error: Revert command failed. The file might not be patched or have conflicts."
        echo "Check for a '.rej' file for details on failed hunks."
        exit 1
    fi
fi

exit 0