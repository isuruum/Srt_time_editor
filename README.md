# SRT Subtitle Time Editor

A simple, user-friendly Python GUI application for shifting and adjusting the timing of `.srt` subtitle files. 

If you have a subtitle file that is out of sync with your video, this tool allows you to easily shift all timestamps by simply providing the desired starting time of the first subtitle. The app calculates the necessary offset and applies it to the entire file automatically.

## Modules and Features

- **Classic GUI:** Built with Python's `tkinter`, providing an easy-to-use graphical interface.
- **Drag & Drop Support:** Easily drag and drop your `.srt` files into the app window.
- **Smart Dialogue Selection:** View a preview of the first few subtitles. Click the actual start of the movie to bypass an intro text or translator credits, ensuring accurate time calculation.
- **Easy Time shifting:** Just input the target time you want the selected subtitle to appear at, and the tool calculates and applies the offset to all subtitles.
- **Advanced Sections Mode:** Need to fix subtitles for a video with ads or cut scenes? Toggle the sections option to search for specific subtitles and apply custom time shifts to different segments of the video independently!
- **Flexible Formats:** Accepts standard SRT timecodes (e.g., `00:02:11,583`) or raw seconds (e.g., `131.583`).
- **Safe Output Options:** Choose to either overwrite the original file, save a new copy with an `_adjusted` suffix, or specify a custom save location.
- **Settings & Preferences:** Toggle **Dark Mode** on/off, and configure auto-clear or auto-close behaviors upon successful syncing!

## Requirements

- **Python 3.x**
- **tkinterdnd2** package (required for drag & drop capabilities). 
  Install it via command line:
  ```bash
  pip install tkinterdnd2
  ```

## How to Run

1. Clone or download this repository to your local machine.
2. Open your terminal or command prompt.
3. Navigate to the folder containing the project files.
4. Run the application using Python:

```bash
python srt_editor_gui.py
```

## Usage Instructions

1. **Select File:** Click the **Browse** button or simply **Drag & Drop** your out-of-sync `.srt` file into the app.
2. **Choose Mode:** If your video has ads or cut sections, check the **"Content contain ads or sections?"** box to reveal advanced settings. Otherwise, proceed with the basic flow.

### Basic Time Adjustment
3. **Select First Dialogue:** In the subtitle preview list, click on the entry where the actual movie dialogue begins (this allows you to safely ignore intro text or translation credits).
4. **Review Original Time:** The **Original Time** box will automatically populate with the timestamp of the subtitle you selected.
5. **Set Target Time:** Type the exact time where this subtitle *should* actually appear in the **Target Time** box.

### Advanced Sections Time Adjustment
- **Search:** Find the start of the section you want to adjust by typing a word or phrase into the search box and clicking **Search**.
- **Pick Start:** Click a search result to set the section's original **Start Time**.
- **Pick End (Optional):** Enter an end time if the shift shouldn't apply until the end of the file.
- **Set Target:** Enter the time this section should start in the **New Target Start Time for Section** box.
- **Add Section:** Click **Add Section Shift** to queue this adjustment. You can add as many sections as you need!

### Finalizing
6. **Choose Output:** Select whether you want to save a new file, select a custom save location, or overwrite the existing file.
7. **Apply/Clear:** Click **Process Subtitles**. The app will calculate the differences, shift all the timestamps based on your rules, and save your synced file. Use the **Clear Details** button to quickly reset the inputs for another file.

**Note:** You can also check the **Settings** menu at the top to enable **Dark Mode**, **Auto Clear**, or **Auto Close** on success!

## Viewing Milliseconds in VLC (Optional)

If you are using VLC Media Player to find the exact target time for your subtitles, you might notice that VLC does not display milliseconds by default. 

To view exact milliseconds for precise syncing, advanced users can install a VLC extension:
- **Plugin Download:** [Time extension](https://addons.videolan.org/p/1154032)
- **Installation Guide:** [Viewing milliseconds in VLC Media Player](https://agatedragon.blog/2024/04/16/viewing-milliseconds-in-vlc-media-player/)
