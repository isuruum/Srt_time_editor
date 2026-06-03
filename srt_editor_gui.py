import tkinter as tk
from tkinter import filedialog, messagebox
import re
from datetime import timedelta
import os

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    messagebox.showerror("Dependency Error", "Please install tkinterdnd2: pip install tkinterdnd2")
    exit()

class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class SrtEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SRT Subtitle Time Editor")
        
        # Center the window
        window_width = 600
        window_height = 850
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # --- Variables for Settings ---
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.auto_clear_var = tk.BooleanVar(value=False)
        self.auto_close_var = tk.BooleanVar(value=False)
        self.has_sections_var = tk.BooleanVar(value=False)
        self.all_subs = []
        self.search_results = []
        self.added_sections = []
        
        # --- Create Menu Bar ---
        self.menubar = tk.Menu(root)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_checkbutton(label="Enable Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        self.settings_menu.add_checkbutton(label="Auto Clear on Success", variable=self.auto_clear_var)
        self.settings_menu.add_checkbutton(label="Auto Close on Success", variable=self.auto_close_var)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
        
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.edit_menu.add_command(label="Clear All", command=self.clear_data)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)
        
        self.root.config(menu=self.menubar)
        
        # Enable drag and drop on the whole window
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # --- Make entire window scrollable ---
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        container_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=container_frame, anchor="nw")
        
        def on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        container_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)
        
        def _on_mousewheel(event):
            # Cross-platform mouse wheel scrolling
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Create a padding frame inside the container to mimic original padding
        container = tk.Frame(container_frame)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- File Selection ---
        tk.Label(container, text="1. Select or Drag & Drop SRT File:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 5))
        
        file_frame = tk.Frame(container)
        file_frame.pack(fill="x")
        self.file_path_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.file_path_var, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(file_frame, text="Browse", command=self.browse_file).pack(side="right")
        
        tk.Checkbutton(container, text="Content contain ads or sections?", variable=self.has_sections_var, command=self.toggle_sections, font=("Arial", 10, "bold")).pack(anchor="w", pady=10)
        
        # --- First Subtitles List (Wrapped to toggle easily) ---
        self.intro_list_frame = tk.Frame(container)
        self.intro_list_frame.pack(fill="x", pady=(0, 10))
        tk.Label(self.intro_list_frame, text="2. Select First Actual Dialogue (to ignore intro text):", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 5))
        
        list_frame = tk.Frame(self.intro_list_frame)
        list_frame.pack(fill="x")
        
        self.sub_listbox = tk.Listbox(list_frame, height=5, selectmode=tk.SINGLE, font=("Consolas", 9), width=80)
        self.sub_listbox.pack(side="left", fill="x", expand=True)
        self.sub_listbox.bind('<<ListboxSelect>>', self.on_subtitle_select)
        
        list_scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        list_scrollbar.config(command=self.sub_listbox.yview)
        list_scrollbar.pack(side="right", fill="y")
        self.sub_listbox.config(yscrollcommand=list_scrollbar.set)

        # --- Time Adjustment ---
        self.basic_time_label = tk.Label(container, text="3. Basic Time Adjustment:", font=("Arial", 10, "bold"))
        self.basic_time_label.pack(anchor="w", pady=(10, 5))
        
        # Container to hold either basic mode or advanced mode
        self.modes_container = tk.Frame(container)
        self.modes_container.pack(fill="x", pady=5)
        
        self.basic_time_frame = tk.Frame(self.modes_container)
        self.basic_time_frame.pack(fill="x")
        
        tk.Label(self.basic_time_frame, text="Original Time (Auto-detected)").grid(row=0, column=0, sticky="w")
        tk.Label(self.basic_time_frame, text="Target Time").grid(row=0, column=1, sticky="w", padx=20)
        
        tk.Label(self.basic_time_frame, text=" ").grid(row=1, column=0, sticky="w") # Spacer
        tk.Label(self.basic_time_frame, text="(e.g. 1:50 or 00:01:50,318)").grid(row=1, column=1, sticky="w", padx=20)
        
        self.old_time_var = tk.StringVar()
        self.old_time_entry = tk.Entry(self.basic_time_frame, textvariable=self.old_time_var, width=22, state="readonly")
        self.old_time_entry.grid(row=2, column=0, pady=5, sticky="w")
        ToolTip(self.old_time_entry, "Original time detected from the uploaded SRT file's first subtitle timeframe.")
        
        self.new_time_var = tk.StringVar()
        tk.Entry(self.basic_time_frame, textvariable=self.new_time_var, width=22).grid(row=2, column=1, pady=5, padx=20, sticky="w")
        
        # --- Advanced Sections Frame (Hidden by default) ---
        self.sections_frame = tk.Frame(self.modes_container)
        
        tk.Label(self.sections_frame, text="Search Subtitles:").grid(row=0, column=0, sticky="w", pady=(10, 0))
        
        search_sub_frame = tk.Frame(self.sections_frame)
        search_sub_frame.grid(row=1, column=0, columnspan=2, sticky="we")
        self.search_var = tk.StringVar()
        tk.Entry(search_sub_frame, textvariable=self.search_var, width=30).pack(side="left", padx=(0, 5))
        tk.Button(search_sub_frame, text="Search", command=self.search_subs).pack(side="left")
        
        self.search_listbox = tk.Listbox(self.sections_frame, height=5, width=100)
        self.search_listbox.grid(row=2, column=0, columnspan=2, sticky="we", pady=5)
        self.search_listbox.bind('<<ListboxSelect>>', self.on_search_select)
        
        tk.Label(self.sections_frame, text="Section Start Time (Select from search results above):").grid(row=3, column=0, sticky="w", pady=(5,0))
        self.sec_start_var = tk.StringVar()
        tk.Entry(self.sections_frame, textvariable=self.sec_start_var, state="readonly", width=25).grid(row=4, column=0, sticky="w")
        
        tk.Label(self.sections_frame, text="Section End (optional, empty=EOF):").grid(row=5, column=0, sticky="w", pady=(5,0))
        self.sec_end_var = tk.StringVar()
        tk.Entry(self.sections_frame, textvariable=self.sec_end_var, width=25).grid(row=6, column=0, sticky="w")
        
        tk.Label(self.sections_frame, text="New Target Start Time for Section:").grid(row=7, column=0, sticky="w", pady=(5,0))
        self.sec_target_var = tk.StringVar()
        tk.Entry(self.sections_frame, textvariable=self.sec_target_var, width=25).grid(row=8, column=0, sticky="w")
        
        tk.Button(self.sections_frame, text="Add Section Shift", command=self.add_section, bg="#2196F3", fg="white").grid(row=9, column=0, sticky="we", pady=10)
        
        tk.Label(self.sections_frame, text="Added Sections:").grid(row=10, column=0, sticky="w")
        self.sections_listbox = tk.Listbox(self.sections_frame, height=4, width=80)
        self.sections_listbox.grid(row=11, column=0, columnspan=2, sticky="we")
        self.sections_listbox.bind('<<ListboxSelect>>', self.on_added_section_select)
        tk.Button(self.sections_frame, text="Remove Selected Section", command=self.remove_section).grid(row=12, column=0, sticky="we", pady=(5, 10))

        # --- Save Options ---
        self.save_options_label = tk.Label(container, text="4. Output Options:", font=("Arial", 10, "bold"))
        self.save_options_label.pack(anchor="w", pady=(10, 5))
        self.save_mode_var = tk.StringVar(value="new")
        tk.Radiobutton(container, text="Save as new file (appends '_adjusted')", variable=self.save_mode_var, value="new").pack(anchor="w", padx=10)
        tk.Radiobutton(container, text="Save to custom location...", variable=self.save_mode_var, value="custom").pack(anchor="w", padx=10)
        tk.Radiobutton(container, text="Overwrite original file", variable=self.save_mode_var, value="overwrite", fg="red").pack(anchor="w", padx=10)
        
        # --- Action Buttons ---
        button_frame = tk.Frame(container)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Process Subtitles", command=self.process_file, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="left", padx=10)
        tk.Button(button_frame, text="Clear Details", command=self.clear_data, bg="#f44336", fg="white", font=("Arial", 11, "bold"), width=10).pack(side="left", padx=10)
        
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(container, textvariable=self.status_var, fg="#666666").pack(side="bottom", pady=5)

    def toggle_sections(self):
        if self.has_sections_var.get():
            self.intro_list_frame.pack_forget()
            self.basic_time_label.config(text="2. Advanced Sections Time Adjustment:")
            self.save_options_label.config(text="3. Output Options:")
            self.basic_time_frame.pack_forget()
            self.sections_frame.pack(fill="x")
            
            # Automatically load all subtitles into the search box if a file is already loaded
            if self.all_subs and not self.search_results:
                self.search_subs()
        else:
            self.intro_list_frame.pack(fill="x", pady=(0, 10), before=self.basic_time_label)
            self.basic_time_label.config(text="3. Basic Time Adjustment:")
            self.save_options_label.config(text="4. Output Options:")
            self.sections_frame.pack_forget()
            self.basic_time_frame.pack(fill="x")

    def on_drop(self, event):
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        if path.lower().endswith('.srt'):
            self.load_file(path)
        else:
            messagebox.showerror("Invalid File", "Please drop a valid .srt file.")

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select an SRT file",
            filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
        )
        if path:
            self.load_file(path)
            
    def on_subtitle_select(self, event):
        selection = self.sub_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.all_subs):
                self.old_time_entry.config(state="normal")
                self.old_time_var.set(self.all_subs[index]['start'])
                self.old_time_entry.config(state="readonly")

    def load_file(self, path):
        self.file_path_var.set(path)
        self.all_subs.clear()
        self.sub_listbox.delete(0, tk.END)
        
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
            blocks = re.split(r'\n\s*\n', content.replace('\r', '').strip())
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 2:
                    match = re.search(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})", lines[1])
                    if not match:
                        match = re.search(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})", lines[0])
                        text_start = 1 if match else 2
                    else:
                        text_start = 2
                        
                    if match:
                        time_str = match.group(1)
                        # Remove all tags & join
                        text_preview = " ".join(lines[text_start:]).strip()
                        text_preview = re.sub(r'<[^>]*>', '', text_preview)
                        self.all_subs.append({
                            'start': time_str,
                            'end': match.group(2),
                            'text': text_preview
                        })
                        
                        if len(self.all_subs) <= 15: # display first 15 for selection
                            display_preview = text_preview
                            if len(display_preview) > 60:
                                display_preview = display_preview[:57] + "..."
                            self.sub_listbox.insert(tk.END, f"{time_str} | {display_preview}")

            if self.all_subs:
                self.sub_listbox.select_set(0)
                self.on_subtitle_select(None)
                if self.has_sections_var.get():
                    self.search_subs()
            else:
                self.old_time_entry.config(state="normal")
                self.old_time_var.set("")
                self.old_time_entry.config(state="readonly")
                
        except Exception:
            self.old_time_entry.config(state="normal")
            self.old_time_var.set("")
            self.old_time_entry.config(state="readonly")

    def search_subs(self):
        q = self.search_var.get().lower()
        self.search_listbox.delete(0, tk.END)
        self.search_results.clear()
        
        if not self.all_subs:
            messagebox.showwarning("Warning", "No subtitles loaded or file is empty.")
            return

        for sub in self.all_subs:
            if q in sub['text'].lower():
                self.search_results.append(sub)
                preview = f"{sub['start']} | {sub['text'][:40]}"
                self.search_listbox.insert(tk.END, preview)

    def on_search_select(self, event):
        selection = self.search_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.search_results):
                self.sec_start_var.set(self.search_results[index]['start'])

    def on_added_section_select(self, event):
        selection = self.sections_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.added_sections):
                section = self.added_sections[index]
                self.sec_start_var.set(section['start'])
                self.sec_target_var.set(section['target'])
                self.sec_end_var.set(section.get('end', ''))

    def add_section(self):
        start = self.sec_start_var.get()
        target = self.sec_target_var.get()
        end = self.sec_end_var.get().strip()
        
        if not start or not target:
            messagebox.showerror("Error", "Section Start and Target Time cannot be empty.")
            return
            
        self.added_sections.append({'start': start, 'target': target, 'end': end})
        self.sections_listbox.insert(tk.END, f"Start: {start} -> Shift to: {target} (End: {end if end else 'EOF'})")
        
        # Clear inputs for next
        self.sec_start_var.set("")
        self.sec_target_var.set("")
        self.sec_end_var.set("")

    def remove_section(self):
        selection = self.sections_listbox.curselection()
        if selection:
            index = selection[0]
            del self.added_sections[index]
            self.sections_listbox.delete(index)

    def parse_time(self, t_str):
        t_str = t_str.strip()
        time_part, ms_part = re.split(r'[,.]', t_str) if ',' in t_str or '.' in t_str else (t_str, '0')
        parts = time_part.split(':')
        
        h, m, s = 0, 0, 0
        if len(parts) == 3:
            h, m, s = parts
        elif len(parts) == 2:
            m, s = parts
        elif len(parts) == 1:
            s = parts[0]
            
        return timedelta(hours=int(h), minutes=int(m), seconds=float(s), milliseconds=int(ms_part))

    def format_time(self, td):
        total_seconds = int(td.total_seconds())
        milliseconds = int(round((td.total_seconds() - total_seconds) * 1000))
        if milliseconds < 0:
            milliseconds = 0
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def clear_data(self):
        self.file_path_var.set("")
        self.all_subs.clear()
        self.search_results.clear()
        self.added_sections.clear()
        self.sub_listbox.delete(0, tk.END)
        self.search_listbox.delete(0, tk.END)
        self.sections_listbox.delete(0, tk.END)
        self.search_var.set("")
        
        self.old_time_entry.config(state="normal")
        self.old_time_var.set("")
        self.old_time_entry.config(state="readonly")
        
        self.new_time_var.set("")
        self.sec_start_var.set("")
        self.sec_target_var.set("")
        self.sec_end_var.set("")
        
        self.status_var.set("Ready")

    def process_file(self):
        input_file = self.file_path_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid SRT file first.")
            return

        is_advanced = self.has_sections_var.get()

        parsed_secs = []
        global_offset = timedelta(0)

        if is_advanced:
            if not self.added_sections:
                messagebox.showerror("Error", "No sections added.")
                return
            try:
                for sec in self.added_sections:
                    s_td = self.parse_time(sec['start'])
                    t_td = self.parse_time(sec['target'])
                    e_td = self.parse_time(sec['end']) if sec['end'] else timedelta.max
                    offset = t_td - s_td
                    parsed_secs.append({'start': s_td, 'end': e_td, 'offset': offset})
            except Exception:
                messagebox.showerror("Error", "Invalid time format in Sections!")
                return
        else:
            old_time_str = self.old_time_var.get()
            new_time_str = self.new_time_var.get()
            if not old_time_str or not new_time_str:
                messagebox.showerror("Error", "Please provide Target times.")
                return
            try:
                old_td = self.parse_time(old_time_str)
                new_td = self.parse_time(new_time_str)
                global_offset = new_td - old_td
            except Exception:
                messagebox.showerror("Error", "Invalid time format provided.")
                return

        if self.save_mode_var.get() == "new":
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_adjusted{ext}"
        elif self.save_mode_var.get() == "custom":
            base, ext = os.path.splitext(input_file)
            suggested_filename = f"{os.path.basename(base)}_adjusted{ext}"
            output_file = filedialog.asksaveasfilename(
                title="Save Subtitle File As",
                initialfile=suggested_filename,
                defaultextension=".srt",
                filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
            )
            if not output_file:
                return
        else:
            output_file = input_file

        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            def repl(match):
                start = self.parse_time(match.group(1))
                end = self.parse_time(match.group(2))
                
                offset_to_apply = global_offset
                
                if is_advanced:
                    offset_to_apply = timedelta(0) # Default to 0 if not in any section
                    for sec in parsed_secs:
                        if sec['start'] <= start <= sec['end']:
                            offset_to_apply = sec['offset']
                            break
                
                new_start = start + offset_to_apply
                new_end = end + offset_to_apply
                
                if new_start.total_seconds() < 0: new_start = timedelta(0)
                if new_end.total_seconds() < 0: new_end = timedelta(0)
                    
                return f"{self.format_time(new_start)} --> {self.format_time(new_end)}"

            new_content = re.sub(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})", repl, content)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.status_var.set(f"Success! Saved: {os.path.basename(output_file)}")
            msg = "Subtitles adjusted successfully!"
            if is_advanced:
                msg += f"\nProcessed {len(parsed_secs)} sections."
            else:
                msg += f"\nComputed Offset: {global_offset.total_seconds():.3f} seconds."
            messagebox.showinfo("Success", msg)
            
            if self.auto_clear_var.get():
                self.clear_data()
            if self.auto_close_var.get():
                self.root.destroy()
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred reading or writing the file:\n{str(e)}")

    def toggle_dark_mode(self):
        is_dark = self.dark_mode_var.get()
        bg_color = "#2b2b2b" if is_dark else "SystemButtonFace"
        fg_color = "#ffffff" if is_dark else "#000000"
        entry_bg = "#3c3c3c" if is_dark else "#ffffff"
        entry_fg = "#ffffff" if is_dark else "#000000"
        readonly_bg = "#4d4d4d" if is_dark else "SystemButtonFace"
        
        def apply_colors(widget):
            widget_type = widget.winfo_class()
            try:
                if widget_type in ('Frame', 'Tk', 'Toplevel', 'Canvas'):
                    widget.configure(bg=bg_color)
                elif widget_type in ('Label', 'Radiobutton', 'Checkbutton'):
                    widget.configure(bg=bg_color, fg=fg_color)
                    if widget_type in ('Radiobutton', 'Checkbutton'):
                        widget.configure(selectcolor=entry_bg)
                elif widget_type == 'Entry':
                    widget.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, readonlybackground=readonly_bg)
                elif widget_type == 'Listbox':
                    widget.configure(bg=entry_bg, fg=entry_fg, selectbackground="#569CD6" if is_dark else "#0078D7", selectforeground="#ffffff")
                elif widget_type == 'Button':
                    if widget.cget("bg") not in ("#4CAF50", "#f44336", "#2196F3"):
                        widget.configure(bg=entry_bg, fg=entry_fg)
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                apply_colors(child)
        apply_colors(self.root)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = SrtEditorApp(root)
    root.mainloop()