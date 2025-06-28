import sys
import re
from collections import defaultdict

def analyze_log(file_path, ngram_size=4, min_repeats=2):
    """
    Analyzes a log file to find frequently repeated, order-independent n-grams.

    Args:
        file_path (str): The path to the log file.
        ngram_size (int): The number of words to consider in an n-gram.
        min_repeats (int): The minimum number of times an n-gram must repeat to be shown.
    """
    ngram_counts = defaultdict(int)
    ngram_first_occurrence = {}

    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Normalize line: lowercase and remove non-alphanumeric chars except spaces
                words = re.sub(r'[^a-z0-9\s]', '', line.lower()).split()

                if not words:
                    continue

                for i in range(len(words) - ngram_size + 1):
                    ngram = tuple(words[i:i + ngram_size])
                    # Canonical form is the sorted tuple of words
                    canonical_ngram = tuple(sorted(ngram))

                    if canonical_ngram not in ngram_first_occurrence:
                        ngram_first_occurrence[canonical_ngram] = line_num
                    
                    ngram_counts[canonical_ngram] += 1

    except FileNotFoundError:
        print(f"Error: Log file not found at {file_path}")
        return

    # Filter out n-grams that don't meet the minimum repeat count
    filtered_ngrams = {k: v for k, v in ngram_counts.items() if v >= min_repeats}

    # Sort the filtered n-grams by their first occurrence
    sorted_ngrams = sorted(filtered_ngrams.keys(), key=lambda ng: ngram_first_occurrence[ng])

    print(f"--- Analysis of {file_path} (N-gram size: {ngram_size}, Min repeats: {min_repeats}) ---")
    if not sorted_ngrams:
        print("No highly repeated n-grams found.")
        return
        
    for ngram in sorted_ngrams:
        count = ngram_counts[ngram]
        # Rejoin for readability
        ngram_str = " ".join(ngram)
        print(f"Count: {count:<5} | First appeared near line {ngram_first_occurrence[ngram]:<5} | N-gram: '{ngram_str}'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <path_to_log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    analyze_log(log_file)
