import json
import os
import glob
import re

# Directory to store log files.
LOG_DIR = "table_logging"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Global list to hold intermediate logs for the current run.
INTERMEDIATE_TABLES = []

def get_lowest_available_index(prefix="intermediate_comparison_tables_run", ext="txt"):
    """
    Find the lowest available index such that a file named like
    'prefix{index}.{ext}' does not exist yet in the LOG_DIR.
    """
    pattern = os.path.join(LOG_DIR, f"{prefix}*.{ext}")
    files = glob.glob(pattern)
    indices = []
    for file in files:
        match = re.search(f"{prefix}(\\d+)\\.{ext}$", os.path.basename(file))
        if match:
            indices.append(int(match.group(1)))
    i = 1
    while i in indices:
        i += 1
    return i

# Determine the next available filename.
index = get_lowest_available_index()
filename = os.path.join(LOG_DIR, f"intermediate_comparison_tables_run{index}.txt")
print("Next available filename:", filename)

def diff_lists(prev, curr):
    """
    Given two lists, return a dictionary with keys:
      - "created": items in curr but not in prev
      - "removed": items in prev but not in curr

    The similarity between items is determined by the name of the "criterion" key.
    """
    prev_set = set(item["criterion"] for item in prev)
    curr_set = set(item["criterion"] for item in curr)
    print("prev_set:", prev_set)
    print("curr_set:", curr_set)
    created = [{"criterion": item} for item in curr_set - prev_set]
    removed = [{"criterion": item} for item in prev_set - curr_set]
    return {"created": created, "removed": removed}

def log_intermediate_table(intermediate, step=None):
    """
    Log an intermediate result with versioning.
    If 'intermediate' is a list:
      - If no previous log exists, this is the "base" snapshot.
      - Otherwise compute diffs (i.e., delta) with respect to the previous full snapshot.
    For non-list objects, log as is.
    
    Each log entry will have:
      • "version": either "base" or "delta" (or "other" if not a list)
      • "full_snapshot": for list objects, always stores the full current state.
    """
    entry = {"step": step if step is not None else "unspecified"}
    if isinstance(intermediate, list):
        if not INTERMEDIATE_TABLES:
            # First snapshot: the base version.
            entry["version"] = "base"
            entry["content"] = {"created": intermediate, "removed": []}
            entry["full_snapshot"] = intermediate
        else:
            # Diff with previous full snapshot.
            prev_full = INTERMEDIATE_TABLES[-1].get("full_snapshot")
            # Compute diff using the "criterion" key:
            prev_set = set(item["criterion"] for item in prev_full)
            curr_set = set(item["criterion"] for item in intermediate)

            # TODO: investigate bug after here
            diff_created = [{"criterion": item} for item in curr_set - prev_set]
            diff_removed = [{"criterion": item} for item in prev_set - curr_set]
            print("diff_created:", diff_created)
            print("diff_removed:", diff_removed)
            print("\n"*3)
            entry["version"] = "delta"
            entry["content"] = {"created": diff_created, "removed": diff_removed}
            # Always store the full snapshot for later reference
            entry["full_snapshot"] = intermediate
    else:
        entry["content"] = intermediate
        entry["version"] = "other"
    INTERMEDIATE_TABLES.append(entry)
    
def save_intermediate_tables(filename=filename, details=None, time_taken=None, total_prompt_tokens=None, total_response_tokens=None):
    """
    Save all intermediate logs collected during this run to the specified file.
    The file stores a JSON array where each element is a run entry.
    If the file already exists, load its contents, append the current run,
    and write it back.
    """
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except Exception:
                data = []
    else:
        data = []
    
    data.append({
        "run": len(data) + 1,
        "details": details,
        "time_taken": time_taken,
        "total_prompt_tokens": total_prompt_tokens,
        "total_response_tokens": total_response_tokens,
        "logs": INTERMEDIATE_TABLES
    })
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
