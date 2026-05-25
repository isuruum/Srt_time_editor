# SRT Subtitle Time Editor

A simple, user-friendly Python GUI application for shifting and adjusting the timing of `.srt` subtitle files. 

If you have a subtitle file that is out of sync with your video, this tool allows you to easily shift all timestamps by simply providing the desired starting time of the first subtitle. The app calculates the necessary offset and applies it to the entire file automatically.

## Features

- **Intuitive GUI:** Built with Python's `tkinter`, providing an easy-to-use graphical interface.
- **Auto-Detection:** Automatically reads the selected `.srt` file and detects the first subtitle timestamp.
- **Easy Time shifting:** Just input the target time you want the first subtitle to appear at, and the tool calculates and applies the offset to all subtitles.
- **Flexible Formats:** Accepts standard SRT timecodes (e.g., `00:02:11,583`) or raw seconds (e.g., `131.583`).
- **Safe Output Options:** Choose to either overwrite the original file or easily save a new copy with an `_adjusted` suffix.

## Requirements

- **Python 3.x**
- No external packages required! The app uses Python's built-in standard libraries (`tkinter`, `re`, `datetime`, `os`, `sys`).

## How to Run

1. Clone or download this repository to your local machine.
2. Open your terminal or command prompt.
3. Navigate to the folder containing the project files.
4. Run the application using Python:

```bash
python srt_editor_gui.py
```

## Usage Instructions

1. **Select File:** Click the **Browse** button and select your out-of-sync `.srt` file.
2. **Review Original Time:** The **Original Time** box will automatically populate with the very first timestamp found in the subtitle file.
3. **Set Target Time:** Type the exact time where the first subtitle *should* actually appear in the **Target Time** box.
4. **Choose Output:** Select whether you want to save a new file (leaves your original untouched) or overwrite the existing file.
5. **Apply:** Click **Apply Subtitle Shift**. The app will calculate the difference, shift all the timestamps, and save your synced file!

## Viewing Milliseconds in VLC (Optional)

If you are using VLC Media Player to find the exact target time for your subtitles, you might notice that VLC does not display milliseconds by default. 

To view exact milliseconds for precise syncing, advanced users can install a VLC extension:
- **Plugin Download:** [Time extension](https://addons.videolan.org/p/1154032)
- **Installation Guide:** [Viewing milliseconds in VLC Media Player](https://agatedragon.blog/2024/04/16/viewing-milliseconds-in-vlc-media-player/)
