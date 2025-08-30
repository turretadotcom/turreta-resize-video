# Turreta Resize Video

A simple Python script to **resize `.mpg` video files** using [FFmpeg](https://ffmpeg.org/).  
The script appends a `-rs` suffix to processed files, skips already resized ones,  
processes only **N files per run** (default: 5), and generates a log file for each run.

## Features
- ✅ Explicit FFmpeg binary path (set via `--ffmpeg-path`)
- ✅ Resizes `.mpg` files to a target width (height auto-calculated)
- ✅ Converts output to **H.264 MP4** with good quality
- ✅ Appends `-rs` suffix to output filenames
- ✅ Skips files that already contain `-rs`
- ✅ Limit how many files are processed per run (**default: 5**)
- ✅ Option to delete originals after successful processing
- ✅ Logs each run to a unique file under `logs/` (next to the script)

## Requirements
- [Python 3.7+](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org/download.html) installed  
  (point to it via `--ffmpeg-path`, e.g. `C:\ffmpeg\bin\ffmpeg.exe`)

## Usage

### Basic
```bash
python turreta-resize-video.py "D:\Videos" --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe"
