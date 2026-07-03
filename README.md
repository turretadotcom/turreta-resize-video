# Turreta Resize Video

A simple Python script to **resize/transcode `.mpg` and `.mp4` video files** using [FFmpeg](https://ffmpeg.org/).

The script appends a `-rs` suffix to processed files, skips already resized ones, processes only **N files per run** by default, and generates a unique log file for each run.

It also supports a simple **INI control file** so you can set `emergencyStop=true` while the script is running. The current video will continue processing, but the script will stop before starting the next file.

## Features

* ✅ Explicit FFmpeg binary path, set via `--ffmpeg-path`
* ✅ Processes `.mpg` and `.mp4` files
* ✅ Resizes videos to a target width while auto-calculating height
* ✅ Converts output to **H.264 MP4**
* ✅ Appends `-rs` suffix to output filenames
* ✅ Skips files that already contain `-rs`
* ✅ Skips files when the `-rs.mp4` output already exists
* ✅ Limits how many files are processed per run, default: `5`
* ✅ Optional original deletion using `--delete-originals`
* ✅ If resized file is larger or same size, keeps the original and renames it to the `-rs.mp4` output name
* ✅ Logs each run to a unique file under `logs/` next to the script
* ✅ Supports `resize_video.ini` control file with `emergencyStop`

## Requirements

* [Python 3.7+](https://www.python.org/downloads/)
* [FFmpeg](https://ffmpeg.org/download.html) installed

You can either make `ffmpeg` available in your system `PATH`, or point to it directly using `--ffmpeg-path`.

Example:

```bash
--ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe"
```

## INI Control File

By default, the script reads this file from the **current directory where you run the command**:

```text
resize_video.ini
```

Create `resize_video.ini` with this content:

```ini
[control]
emergencyStop=false
```

To stop after the current video finishes, edit the file while the script is running:

```ini
[control]
emergencyStop=true
```

The script checks this flag **before starting each next file**.

This means:

```text
Current file: continues processing
Next file: will not start
Script: exits cleanly
```

If the INI file is missing, or if `[control] emergencyStop` is missing, the script assumes:

```ini
emergencyStop=false
```

## Usage

### Basic

```bash
python turreta-resize-video.py "D:\Videos" --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe"
```

### With target width

```bash
python turreta-resize-video.py "D:\Videos" --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe" --width 1280
```

### Process only 10 files

```bash
python turreta-resize-video.py "D:\Videos" --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe" --limit 10
```

### Delete originals after processing

```bash
python turreta-resize-video.py "D:\Videos" --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe" --delete-originals
```

When `--delete-originals` is used:

* If the resized file is smaller, the original file is deleted.
* If the resized file is larger or the same size, the resized file is deleted and the original file is renamed to the `-rs.mp4` output filename.

### Use a custom INI file path

```bash
python turreta-resize-video.py "D:\Videos" --config-path "D:\control\resize_video.ini"
```

## Command Line Arguments

| Argument             | Required | Default            | Description                                                           |
| -------------------- | -------: | ------------------ | --------------------------------------------------------------------- |
| `directory`          |      Yes | N/A                | Base directory to scan recursively                                    |
| `--ffmpeg-path`      |       No | `ffmpeg`           | Path to FFmpeg executable                                             |
| `--width`            |       No | `1280`             | Target video width. Height is auto-calculated                         |
| `--crf`              |       No | `22`               | Quality setting. Lower means better quality. Typical range is `18-23` |
| `--preset`           |       No | `slow`             | x264 preset. Slower gives better compression                          |
| `--limit`            |       No | `5`                | Maximum number of videos to process in one run                        |
| `--delete-originals` |       No | `false`            | Delete original only if the resized file is smaller                   |
| `--config-path`      |       No | `resize_video.ini` | Path to INI control file                                              |

## Supported Presets

The `--preset` value must be one of:

```text
ultrafast
superfast
veryfast
faster
fast
medium
slow
slower
veryslow
```

Default:

```text
slow
```

## Output Filename

For an input file like:

```text
sample.mpg
```

The output will be:

```text
sample-rs.mp4
```

For an input file like:

```text
sample.mp4
```

The output will also be:

```text
sample-rs.mp4
```

Files already containing `-rs` in the filename are skipped.

Example skipped files:

```text
sample-rs.mp4
holiday-RS.mp4
```

## Logs

Each run creates a unique log file under the `logs/` directory beside the script.

Example:

```text
logs/resize_video_20260703_143012_a1b2c3d4.log
```

The logs include:

* Start parameters
* Files skipped
* Files processed
* FFmpeg errors
* Original and resized file sizes
* Cleanup actions
* Emergency stop detection
* Done message

## Emergency Stop Behavior

The emergency stop flag does **not** kill FFmpeg while it is processing a video.

This is intentional to avoid partially written or corrupted output files.

The flow is:

1. Script starts processing a file.
2. You edit `resize_video.ini`.
3. Set `emergencyStop=true`.
4. Current FFmpeg process finishes.
5. Script checks the INI file before the next file.
6. Script stops cleanly.

## Example Full Command

```bash
python turreta-resize-video.py "D:\Videos" ^
  --ffmpeg-path "C:\ffmpeg\bin\ffmpeg.exe" ^
  --width 1280 ^
  --crf 22 ^
  --preset slow ^
  --limit 5 ^
  --delete-originals
```

## Notes

* The script scans folders recursively.
* File processing order is deterministic because filenames are sorted.
* The default INI path is relative to the directory where you run the command, not necessarily the folder where the script is located.
* If `resize_video.ini` is not found, the script logs a warning and continues with `emergencyStop=false`.
