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
        self.root.geometry("520x560")
        self.root.resizable(False, False)
        
        # --- Variables for Settings ---
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.auto_clear_var = tk.BooleanVar(value=False)
        self.auto_close_var = tk.BooleanVar(value=False)
        
        # --- Create Menu Bar ---
        self.menubar = tk.Menu(root)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_checkbutton(label="Enable Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        self.settings_menu.add_checkbutton(label="Auto Clear on Success", variable=self.auto_clear_var)
        self.settings_menu.add_checkbutton(label="Auto Close on Success", variable=self.auto_close_var)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
        self.root.config(menu=self.menubar)
        
        # Enable drag and drop on the whole window
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # --- File Selection ---
        tk.Label(root, text="1. Select or Drag & Drop SRT File:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        file_frame = tk.Frame(root)
        file_frame.pack(fill="x", padx=20)
        self.file_path_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.file_path_var, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(file_frame, text="Browse", command=self.browse_file).pack(side="right")
        
        # --- First Subtitles List ---
        tk.Label(root, text="2. Select First Actual Dialogue (to ignore intro text):", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        list_frame = tk.Frame(root)
        list_frame.pack(fill="x", padx=20)
        
        self.sub_listbox = tk.Listbox(list_frame, height=5, selectmode=tk.SINGLE, font=("Consolas", 9))
        self.sub_listbox.pack(side="left", fill="x", expand=True)
        self.sub_listbox.bind('<<ListboxSelect>>', self.on_subtitle_select)
        
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.sub_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.sub_listbox.config(yscrollcommand=scrollbar.set)
        
        self.sub_data = [] # Will store tuples of (time_str, text)
        
        # --- Time Adjustment ---
        tk.Label(root, text="3. Calculate Shift Offset:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        time_frame = tk.Frame(root)
        time_frame.pack(fill="x", padx=20)
        
        tk.Label(time_frame, text="Original Time (Auto-detected)").grid(row=0, column=0, sticky="w")
        tk.Label(time_frame, text="Target Time").grid(row=0, column=1, sticky="w", padx=20)
        
        tk.Label(time_frame, text=" ").grid(row=1, column=0, sticky="w") # Spacer
        tk.Label(time_frame, text="(e.g. 1:50 or 00:01:50,318)").grid(row=1, column=1, sticky="w", padx=20)
        
        self.old_time_var = tk.StringVar()
        self.old_time_entry = tk.Entry(time_frame, textvariable=self.old_time_var, width=22, state="readonly")
        self.old_time_entry.grid(row=2, column=0, pady=5, sticky="w")
        ToolTip(self.old_time_entry, "Original time detected from the uploaded SRT file's first subtitle timeframe.")
        
        self.new_time_var = tk.StringVar()
        tk.Entry(time_frame, textvariable=self.new_time_var, width=22).grid(row=2, column=1, pady=5, padx=20, sticky="w")
        
        # --- Save Options ---
        tk.Label(root, text="4. Output Options:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.save_mode_var = tk.StringVar(value="new")
        tk.Radiobutton(root, text="Save as new file (appends '_adjusted')", variable=self.save_mode_var, value="new").pack(anchor="w", padx=20)
        tk.Radiobutton(root, text="Overwrite original file", variable=self.save_mode_var, value="overwrite", fg="red").pack(anchor="w", padx=20)
        
        # --- Action Buttons ---
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Apply Subtitle Shift", command=self.process_file, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="left", padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_data, bg="#f44336", fg="white", font=("Arial", 11, "bold"), width=10).pack(side="left", padx=10)
        
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, fg="#666666").pack(side="bottom", pady=10)

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
            if index < len(self.sub_data):
                time_val = self.sub_data[index][0]
                self.old_time_entry.config(state="normal")
                self.old_time_var.set(time_val)
                self.old_time_entry.config(state="readonly")

    def load_file(self, path):
        self.file_path_var.set(path)
        self.sub_listbox.delete(0, tk.END)
        self.sub_data.clear()
        
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
            # Regex to find all subtitles: index, timeframe, and text
            # We look for: newline(s) or start of string block, number, timeframe, text
            blocks = re.split(r'\n\s*\n', content.replace('\r', '').strip())
            
            for block in blocks[:15]: # Display up to 15 subtitles
                lines = block.strip().split('\n')
                if len(lines) >= 2:
                    match = re.search(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->", lines[1])
                    if not match:
                        # Sometimes index is missing, try first line
                        match = re.search(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->", lines[0])
                        text_start = 1 if match else 2
                    else:
                        text_start = 2
                        
                    if match:
                        time_str = match.group(1)
                        # Join subtitle text lines, strip HTML tags if any, replace newlines with spaces
                        text_str = " ".join(lines[text_start:]).strip()
                        text_preview = re.sub(r'<[^>]*>', '', text_str)
                        if len(text_preview) > 50:
                            text_preview = text_preview[:47] + "..."
                            
                        self.sub_data.append((time_str, text_preview))
                        self.sub_listbox.insert(tk.END, f"{time_str} | {text_preview}")

            if self.sub_data:
                # Select the first item by default
                self.sub_listbox.select_set(0)
                self.on_subtitle_select(None)
            else:
                self.old_time_entry.config(state="normal")
                self.old_time_var.set("")
                self.old_time_entry.config(state="readonly")
        except Exception:
            self.old_time_entry.config(state="normal")
            self.old_time_var.set("")
            self.old_time_entry.config(state="readonly")

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
        self.sub_listbox.delete(0, tk.END)
        self.sub_data.clear()
        
        self.old_time_entry.config(state="normal")
        self.old_time_var.set("")
        self.old_time_entry.config(state="readonly")
        
        self.new_time_var.set("")
        self.status_var.set("Ready")

    def process_file(self):
        input_file = self.file_path_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid SRT file first.")
            return

        old_time_str = self.old_time_var.get()
        new_time_str = self.new_time_var.get()
        
        if not old_time_str or not new_time_str:
            messagebox.showerror("Error", "Please provide Target times.")
            return

        try:
            old_td = self.parse_time(old_time_str)
            new_td = self.parse_time(new_time_str)
            offset = new_td - old_td
        except Exception as e:
            messagebox.showerror("Error", f"Invalid time format provided.")
            return

        if self.save_mode_var.get() == "new":
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_adjusted{ext}"
        else:
            output_file = input_file

        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            def repl(match):
                start = self.parse_time(match.group(1))
                end = self.parse_time(match.group(2))
                
                new_start = start + offset
                new_end = end + offset
                
                if new_start.total_seconds() < 0: new_start = timedelta(0)
                if new_end.total_seconds() < 0: new_end = timedelta(0)
                    
                return f"{self.format_time(new_start)} --> {self.format_time(new_end)}"

            new_content = re.sub(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})", repl, content)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.status_var.set(f"Success! Saved: {os.path.basename(output_file)}")
            messagebox.showinfo("Success", f"Subtitles adjusted successfully!\nComputed Offset Applied: {offset.total_seconds():.3f} seconds.")
            
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
        
        # Function to recursively apply colors
        def apply_colors(widget):
            widget_type = widget.winfo_class()
            
            try:
                # Basic bg/fg classes
                if widget_type in ('Frame', 'Tk', 'Toplevel'):
                    widget.configure(bg=bg_color)
                elif widget_type in ('Label', 'Radiobutton', 'Checkbutton'):
                    widget.configure(bg=bg_color, fg=fg_color)
                    # handle specific Radiobutton tweaks if needed
                    if widget_type in ('Radiobutton', 'Checkbutton'):
                        widget.configure(selectcolor=entry_bg)
                elif widget_type == 'Entry':
                    widget.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, readonlybackground=readonly_bg)
                elif widget_type == 'Listbox':
                    widget.configure(bg=entry_bg, fg=entry_fg, selectbackground="#569CD6" if is_dark else "#0078D7", selectforeground="#ffffff")
                elif widget_type == 'Button':
                    # Leave colored buttons (like apply/clear) alone if they have custom backgrounds
                    if widget.cget("bg") not in ("#4CAF50", "#f44336"):
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
