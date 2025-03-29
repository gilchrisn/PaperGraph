import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import logging

logger = logging.getLogger(__name__)

# Modern color palette
COLORS = {
    "background": "#f8f9fa",
    "header_bg": "#2c3e50",
    "header_fg": "#ecf0f1",
    "odd_row": "#ffffff",
    "even_row": "#f8f9fa",
    "true": "#27ae60",
    "false": "#c0392b",
    "na": "#7f8c8d",
    "border": "#bdc3c7",
    "hover": "#3498db",
    "tooltip_bg": "#f0fff0"
}

class EnhancedToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.current_content = None
        
    def showtip(self, text, x, y):
        # Avoid recreating tooltip if content hasn't changed
        if text == self.current_content and self.tipwindow:
            self.tipwindow.wm_geometry(f"+{int(x)}+{int(y)}")
            return

        self.hidetip()
        if not text:
            return

        self.current_content = text
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        
        # Calculate dynamic width and height based on the text
        import tkinter.font as tkfont
        import textwrap

        # Calculate dynamic width based on text (same as before)
        font_obj = tkfont.Font(font=("Palatino Linotype", 14))
        lines = text.split('\n')
        max_line_width = max(font_obj.measure(line) for line in lines) if lines else 0
        avg_char_width = font_obj.measure("0")
        calculated_width = max(int(max_line_width / avg_char_width) + 2, 20)
        max_width_chars = 60
        width_chars = min(calculated_width, max_width_chars)

        # Re-wrap text using the computed width (in characters)
        wrapped_lines = []
        for line in lines:
            # Only wrap if needed
            if len(line) > width_chars:
                wrapped_lines.extend(textwrap.wrap(line, width=width_chars))
            else:
                wrapped_lines.append(line)
        # Now compute height based on the wrapped text
        height_lines = len(wrapped_lines) + 2

        # Create text widget with computed dimensions
        text_widget = tk.Text(tw, wrap=tk.WORD, width=width_chars, height=height_lines,
                              relief=tk.SOLID, borderwidth=1,
                              font=("Palatino Linotype", 14), bg=COLORS["tooltip_bg"])
        
        # Configure text tags for different colors
        text_widget.tag_configure("green", foreground=COLORS["true"])
        text_widget.tag_configure("red", foreground=COLORS["false"])
        text_widget.tag_configure("gray", foreground=COLORS["na"])

        # Insert text and apply tags
        for i, line in enumerate(lines):
            start_pos = f"{i+1}.0"
            text_widget.insert(start_pos, line + ('\n' if i < len(lines)-1 else ''))
            # Search and tag specific keywords
            for word in ["True", "False", "N/A"]:
                start_idx = line.find(word)
                while start_idx != -1:
                    if (start_idx == 0 or not line[start_idx-1].isalnum()) and \
                    (start_idx + len(word) == len(line) or not line[start_idx + len(word)].isalnum()):
                        tag = ""
                        if word.lower() == "true":
                            tag = "green"
                        elif word.lower() == "false":
                            tag = "red"
                        elif word.lower() == "n/a":
                            tag = "gray"
                        if tag:
                            text_widget.tag_add(tag, f"{i+1}.{start_idx}", f"{i+1}.{start_idx + len(word)}")
                    start_idx = line.find(word, start_idx + 1)

        text_widget.config(state=tk.DISABLED)  # Make read-only
        text_widget.pack(ipadx=5, ipady=3)
        
        tw.update_idletasks()
        tw_width = tw.winfo_reqwidth()
        tw_height = tw.winfo_reqheight()

        # Ensure tooltip stays within screen boundaries
        if x + tw_width > screen_width:
            x = screen_width - tw_width - 10
        if y + tw_height > screen_height:
            y = screen_height - tw_height - 10

        tw.wm_geometry(f"+{int(x)}+{int(y)}")

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
            self.current_content = None

def fetch_comparison_metadata(repository, main_paper_id: str, criterion_generation_strategy="hybrid", content_generation_strategy="rag"):
    """
    Fetch comparison data and paper metadata from the repository.
    """
    comparison_data = repository.get_paper_comparison_by_semantic_id(
        main_paper_id, criterion_generation_strategy, content_generation_strategy
    )["comparison_data"]

    # Extract paper IDs from the comparison data.
    paper_ids = set()
    for entry in comparison_data:
        comps = entry.get("comparisons", {})
        paper_ids.update(comps.keys())
    paper_ids = sorted(list(paper_ids))

    # Build mappings for paper metadata.
    paper_titles = {}
    paper_pdf_urls = {}
    paper_years = {}
    paper_venues = {}
    for pid in paper_ids:
        paper = repository.get_paper_by_semantic_id(pid)
        if paper:
            paper_titles[pid] = paper.get("title", pid)
            paper_pdf_urls[pid] = paper.get("open_access_pdf", None)
            paper_years[pid] = paper.get("year", "N/A")
            paper_venues[pid] = paper.get("venue", "N/A")
        else:
            paper_titles[pid] = pid
            paper_pdf_urls[pid] = None
            paper_years[pid] = "N/A"
            paper_venues[pid] = "N/A"

    paper_relevance = {}
    for pid in paper_ids:
        relation = repository.get_relation_by_source_and_target(main_paper_id, pid)
        if relation and relation.get("relevance_score") is not None:
            paper_relevance[pid] = relation["relevance_score"]
        else:
            paper_relevance[pid] = "N/A"

    metadata = {
        "comparison_data": comparison_data,
        "paper_ids": paper_ids,
        "paper_titles": paper_titles,
        "paper_pdf_urls": paper_pdf_urls,
        "paper_years": paper_years,
        "paper_venues": paper_venues,
        "paper_relevance": paper_relevance,
        "main_paper_id": main_paper_id
    }
    return metadata

def create_comparison_window(metadata):
    """
    Create and display the Tkinter window for the comparison table using the fetched metadata.
    """
    comparison_data = metadata["comparison_data"]
    paper_ids = metadata["paper_ids"]
    paper_titles = metadata["paper_titles"]
    paper_pdf_urls = metadata["paper_pdf_urls"]
    paper_years = metadata["paper_years"]
    paper_venues = metadata["paper_venues"]
    paper_relevance = metadata["paper_relevance"]

    # Create the Tkinter window with improved title and styling
    root = tk.Tk()
    main_title = paper_titles.get(metadata["main_paper_id"], metadata["main_paper_id"])
    if len(main_title) > 40:
        main_title = main_title[:37] + "..."
    root.title(f"Paper Comparison: {main_title}")
    root.configure(bg=COLORS["background"])
    
    # Set window size to 90% of screen and center it
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.9)
    window_height = int(screen_height * 0.85)
    root.geometry(f"{window_width}x{window_height}+{int((screen_width-window_width)/2)}+{int((screen_height-window_height)/4)}")

    # Add help menu
    menubar = tk.Menu(root)
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="Instructions", command=lambda: show_help(root))
    menubar.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menubar)

    # Configure modern style with custom fonts
    style = ttk.Style(root)
    style.theme_use("clam")  # Use a modern theme
    custom_font = ("Palatino Linotype", 14)
    header_font = ("Palatino Linotype", 15, "bold")
    
    style.configure("Treeview", 
                   rowheight=40, 
                   font=custom_font,
                   background=COLORS["odd_row"], 
                   fieldbackground=COLORS["odd_row"])
                   
    style.configure("Treeview.Heading", 
                   font=header_font, 
                   background=COLORS["header_bg"], 
                   foreground=COLORS["header_fg"], 
                   padding=5)
                   
    style.map("Treeview.Heading", 
              background=[("active", COLORS["hover"])])
              
    style.configure("Treeview.Cell", 
                   font=custom_font, 
                   padding=5)

    # Add a main container frame
    main_frame = ttk.Frame(root, style="TFrame")
    main_frame.pack(expand=True, fill="both", padx=10, pady=10)
    
    # Add a status bar with modern styling
    status_bar = ttk.Label(root, text="Ready", anchor="w", padding=(5, 2), background=COLORS["background"])
    status_bar.pack(side="bottom", fill="x")

    # Create frame with grid layout for better control
    frame = ttk.Frame(main_frame)
    frame.pack(expand=True, fill="both")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Create scrollbars
    vscroll = ttk.Scrollbar(frame, orient="vertical")
    hscroll = ttk.Scrollbar(frame, orient="horizontal")

    # Create treeview with improved styling
    tree = ttk.Treeview(frame, yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
    vscroll.config(command=tree.yview)
    hscroll.config(command=tree.xview)
    
    # Grid layout for treeview and scrollbars
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns")
    hscroll.grid(row=1, column=0, sticky="ew")

    # The first column is for criteria, subsequent columns are for each paper.
    columns = ["Criterion"] + paper_ids
    tree["columns"] = columns[1:]
    tree.heading("#0", text="Attribute", anchor="w")
    tree.column("#0", anchor="w", width=300, minwidth=200)

    # Set column headers to truncated paper titles with year
    for pid in paper_ids:
        title = paper_titles.get(pid, pid)
        if len(title) > 35:
            title = title[:32] + "..."
        year = paper_years.get(pid, "N/A")
        header_text = f"{title}\n({year})"
        tree.heading(pid, text=header_text, anchor="w")
        tree.column(pid, anchor="w", width=300, minwidth=200, stretch=True)

    # Configure row styling and tags with new color scheme
    tree.tag_configure('oddrow', background=COLORS["odd_row"])
    tree.tag_configure('evenrow', background=COLORS["even_row"])

    # Add tags for each value type in each row type
    tree.tag_configure('oddrow_true', background=COLORS["odd_row"], foreground=COLORS["true"])
    tree.tag_configure('oddrow_false', background=COLORS["odd_row"], foreground=COLORS["false"])
    tree.tag_configure('oddrow_na', background=COLORS["odd_row"], foreground=COLORS["na"])

    tree.tag_configure('evenrow_true', background=COLORS["even_row"], foreground=COLORS["true"])
    tree.tag_configure('evenrow_false', background=COLORS["even_row"], foreground=COLORS["false"])
    tree.tag_configure('evenrow_na', background=COLORS["even_row"], foreground=COLORS["na"])

    # Populate the tree with data
    for idx, entry in enumerate(comparison_data):
        criterion = entry.get("criterion", "")
        comparisons = entry.get("comparisons", {})
        
        # Determine if this is an odd or even row
        row_base_tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
        
        # Format values with visual indicators based on content
        row_values = []
        
        # Add visual indicators for values
        for pid in paper_ids:
            value = comparisons.get(pid, "No relevant details found.")
            
            # Add visual indicators for boolean values with enhanced visibility
            if isinstance(value, str) and "N/A" in value.split():
                value = "⚪"  # Larger circle for N/A, with spacing
            elif isinstance(value, str) and "true" in value.split():
                value = "✓"
            elif isinstance(value, str) and "false" in value.split():
                value = "✗"
            elif value is True:
                value = "✓"  # Checkmark with uppercase and spacing
            elif value is False:
                value = "✗"  # X mark with uppercase and spacing
                
            row_values.append(value)
        
        # Insert row with appropriate tag
        tree.insert("", "end", text=criterion, values=row_values, tags=(row_base_tag,))

    # Create enhanced tooltip
    tooltip = EnhancedToolTip(tree)

    def update_status(message):
        """Update status bar with message and reset after 5 seconds"""
        status_bar.config(text=message)
        root.after(5000, lambda: status_bar.config(text="Ready"))

    def on_motion(event):
        """Enhanced tooltip handling with cursor changes"""
        region = tree.identify("region", event.x, event.y)
        col = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)
        
        # Change cursor to hand when hovering over paper headers with PDF available
        if region == "heading":
            try:
                index = int(col.replace("#", "")) - 1
                if 0 <= index < len(paper_ids):
                    pid = paper_ids[index]
                    if paper_pdf_urls.get(pid):
                        tree.config(cursor="hand2")
                    else:
                        tree.config(cursor="")
                    
                    # Show paper metadata tooltip
                    title = paper_titles.get(pid, pid)
                    year = paper_years.get(pid, "N/A")
                    venue = paper_venues.get(pid, "N/A")
                    relevance = paper_relevance.get(pid, "N/A")
                    pdf_status = "PDF available" if paper_pdf_urls.get(pid) else "No PDF available"
                    display_text = f"{title}\nYear: {year}\nVenue: {venue}\nRelevance: {relevance}\n{pdf_status}\n(Click to open PDF)"
                    tooltip.showtip(display_text, event.x_root + 20, event.y_root + 10)
                else:
                    tooltip.hidetip()
                    tree.config(cursor="")
            except Exception as e:
                logger.error("Error in motion event: %s", e)
                tooltip.hidetip()
                tree.config(cursor="")
        elif region in ("cell", "tree"):
            tree.config(cursor="")
            if row_id and col:
                item = tree.item(row_id)
                if col == "#0" or region == "tree":
                    idx = tree.index(row_id)
                    entry = comparison_data[idx]
                    criterion_text = entry.get("criterion", "")
                    description = entry.get("description", "No description available.")
                    cell_text = f"{criterion_text}\n{description}"
                else:
                    col_index = int(col.replace("#", "")) - 1
                    values = item.get("values", [])
                    cell_text = values[col_index] if col_index < len(values) else ""
                    pid = paper_ids[col_index]
                    relevance = paper_relevance.get(pid, "N/A")
                    cell_text = f"{cell_text}\nRelevance: {relevance}"
                tooltip.showtip(cell_text, event.x_root + 20, event.y_root + 10)
            else:
                tooltip.hidetip()
        else:
            tooltip.hidetip()
            tree.config(cursor="")

    def on_header_click(event):
        """Enhanced header click with status updates"""
        region = tree.identify("region", event.x, event.y)
        if region == "heading":
            col = tree.identify_column(event.x)
            try:
                index = int(col.replace("#", "")) - 1
                if 0 <= index < len(paper_ids):
                    pid = paper_ids[index]
                    pdf_url = paper_pdf_urls.get(pid)
                    if pdf_url:
                        update_status(f"Opening PDF for {paper_titles.get(pid, pid)}")
                        webbrowser.open_new(pdf_url)
                    else:
                        update_status("No PDF available for this paper")
            except Exception as e:
                logger.error("Error in header click: %s", e)
                update_status("Error opening PDF")

    # Bind events
    tree.bind("<Motion>", on_motion)
    tree.bind("<Leave>", lambda event: tooltip.hidetip())
    tree.bind("<Button-1>", on_header_click)
    
    # Add keyboard shortcuts
    root.bind("<Escape>", lambda e: tooltip.hidetip())
    root.bind("<Control-q>", lambda e: root.destroy())

    root.mainloop()

def display_comparison_table(repository, main_paper_id: str, criterion_generation_strategy="hybrid", content_generation_strategy="rag"):
    """
    Retrieve and display the comparison table in a Tkinter window.
    """
    metadata = fetch_comparison_metadata(repository, main_paper_id, criterion_generation_strategy, content_generation_strategy)
    create_comparison_window(metadata)

def show_help(parent):
    """Display help information dialog with modern styling"""
    help_text = """
    Paper Comparison Table Guide:
    
    • Hover over any cell to see detailed information
    • Click on paper headers to open the PDF (if available)
    • Use scrollbars to navigate large tables
    • Alternate row colors enhance readability
    
    Color coding:
    • True values appear in green
    • False values appear in red
    • N/A values appear in gray
    
    Keyboard shortcuts:
    • Esc: Close active tooltips
    • Ctrl+Q: Exit application
    
    The relevance score indicates how closely related 
    each paper is to the main paper being analyzed.
    """
    messagebox.showinfo("How to Use This Tool", help_text, parent=parent)