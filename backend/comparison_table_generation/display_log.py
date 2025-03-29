import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

def load_file():
    """Prompt user to select a txt file and parse its JSON content."""
    file_path = filedialog.askopenfilename(
        title="Select Criteria Log File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not file_path:
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        messagebox.showerror("Error", f"Error reading file:\n{e}")
        return None

def create_table(frame, snapshot_title, active, removed):
    """Creates a Treeview table showing active criteria (with status) and removed ones."""
    title = tk.Label(frame, text=snapshot_title, font=("Helvetica", 14, "bold"))
    title.pack(pady=(10, 5))
    
    columns = ("criterion", "description", "status")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
    tree.heading("criterion", text="Criterion")
    tree.heading("description", text="Description")
    tree.heading("status", text="Status")
    
    tree.column("criterion", width=250)
    tree.column("description", width=450)
    tree.column("status", width=100)
    
    tree.pack(padx=10, pady=5, fill="x")
    
    # Insert active criteria (from full_snapshot)
    for item in active:
        tag = "new" if item["status"] == "new" else "normal"
        tree.insert("", "end", values=(item["criterion"], item["description"], item["status"]), tags=(tag,))
    
    # Insert removed criteria (from the delta) at the end
    for item in removed:
        tree.insert("", "end", values=(item["criterion"], item["description"], "removed"), tags=("removed",))
    
    # Style the rows
    tree.tag_configure("new", background="#d4f4dd")      # light green for new
    tree.tag_configure("removed", background="#f4d4d4")  # light red for removed
    tree.tag_configure("normal", background="#ffffff")   # normal white background

def process_and_display(data, container):
    """Process the JSON structure and create tables for each snapshot log."""
    # For simplicity, use the first run in the file
    run = data[0]
    logs = run.get("logs", [])
    
    # We'll loop through each log and display a snapshot table.
    # For each snapshot, the 'active' list comes from full_snapshot with a status based on content delta,
    # and the 'removed' list comes from content['removed'].
    for log in logs:
        snapshot_frame = ttk.Frame(container, relief="groove", borderwidth=2)
        snapshot_frame.pack(fill="x", padx=10, pady=5)
        
        # Title includes the step and version
        step = log.get("step", "unknown").capitalize()
        version = log.get("version", "")
        snapshot_title = f"Snapshot: {step} (Version: {version})"
        
        # Get the full snapshot of criteria
        full_snapshot = log.get("full_snapshot", [])
        # Get the delta details from "content"
        content = log.get("content", {})
        created_delta = content.get("created", [])
        removed_delta = content.get("removed", [])
        # Build sets for easy lookup (using criterion names)
        created_names = set(item.get("criterion") for item in created_delta)
        
        active = []
        for crit in full_snapshot:
            status = "new" if crit.get("criterion") in created_names else "unchanged"
            active.append({
                "criterion": crit.get("criterion", ""),
                "description": crit.get("description", ""),
                "status": status
            })
        # The removed ones are those that appear in the delta (they're not in the current full snapshot)
        removed = []
        for crit in removed_delta:
            removed.append({
                "criterion": crit.get("criterion", ""),
                "description": crit.get("description", "")
            })
        
        create_table(snapshot_frame, snapshot_title, active, removed)

def load_and_display():
    """Main function to load file and display snapshots."""
    data = load_file()
    if data is None:
        return
    
    # Clear the container frame if needed
    for widget in content_frame.winfo_children():
        widget.destroy()
    
    process_and_display(data, content_frame)

# --- Build the main Tkinter window ---
root = tk.Tk()
root.title("Criteria Evolution Diff Viewer")

# Create a top frame with a 'Load File' button
top_frame = ttk.Frame(root)
top_frame.pack(side="top", fill="x", padx=10, pady=10)

load_button = ttk.Button(top_frame, text="Load Criteria Log File", command=load_and_display)
load_button.pack()

# Create a scrollable frame for the snapshots
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
content_frame = ttk.Frame(canvas)

content_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=content_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

root.mainloop()
