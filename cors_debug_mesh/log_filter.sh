#!/bin/bash
# This script reads from stdin, line by line, and filters out consecutively repeated lines.

last_line=""
count=0

# Set a threshold for how many times a line can be repeated before being suppressed.
THRESHOLD=10

while IFS= read -r line; do
  if [[ "$line" == "$last_line" ]]; then
    # Line is the same as the previous one, increment counter.
    ((count++))
    # Print the line only if it's not yet over the threshold.
    if ((count <= THRESHOLD)); then
      echo "$line"
    fi
  else
    # A new, different line has appeared.
    # First, check if the *previous* line was suppressed and needs a summary message.
    if ((count > THRESHOLD)); then
      echo "    [Previous line repeated $((count - THRESHOLD)) more times]"
    fi
    # Now, print the new line and reset the state.
    echo "$line"
    last_line="$line"
    count=1
  fi
done

# After the loop, check one last time for any suppressed trailing lines.
if ((count > THRESHOLD)); then
  echo "    [Previous line repeated $((count - THRESHOLD)) more times]"
fi
