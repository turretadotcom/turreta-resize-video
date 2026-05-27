import os
import time
import uuid
import argparse
import logging
import subprocess
from datetime import datetime

SUPPORTED_EXTENSIONS = ('.mpg', '.mp4')

def setup_logger(script_dir: str) -> logging.Logger:
    """Create logs/ under script directory and use a unique filename."""
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    log_path = os.path.join(logs_dir, f"resize_video_{ts}_{uid}.log")

    logger = logging.getLogger("turreta-resize-video")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    ffmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(ffmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    cfmt = logging.Formatter("[%(levelname)s] %(message)s")
    ch.setFormatter(cfmt)
    logger.addHandler(ch)

    logger.info(f"Log file: {log_path}")
    return logger

def build_ffmpeg_cmd(ffmpeg_path, input_path, output_path, scale_width, crf, preset):
    return [
        ffmpeg_path, "-y",
        "-i", input_path,
        "-vf", f"scale={scale_width}:-2",     # keep aspect ratio
        "-c:v", "libx264",
        "-preset", preset,                    # slower = smaller files at same quality
        "-crf", str(crf),                     # lower = better quality (18–23 is typical)
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",            # smoother playback start
        output_path
    ]

def transcode_video(
    logger: logging.Logger,
    ffmpeg_path: str,
    file_path: str,
    scale_width: int,
    crf: int,
    preset: str,
    delete_original: bool,
    max_retries: int = 3
) -> bool:
    d, base = os.path.split(file_path)
    name, _ = os.path.splitext(base)

    # Skip if already resized
    if "-rs" in name.lower():
        logger.info(f"[SKIP] Already marked as resized: {file_path}")
        return False

    output_path = os.path.join(d, f"{name}-rs.mp4")

    # Skip if target already exists
    if os.path.exists(output_path):
        logger.info(f"[SKIP] Output exists: {output_path}")
        return False

    cmd = build_ffmpeg_cmd(ffmpeg_path, file_path, output_path, scale_width, crf, preset)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[RUN ] ({attempt}/{max_retries}) {file_path} -> {output_path}")
            subprocess.run(cmd, check=True)
            if delete_original:
                # try:
                #     os.remove(file_path)
                #     logger.info(f"[OK  ] Saved {output_path} and deleted {file_path}")
                # except Exception as del_err:
                #     logger.warning(f"[WARN] Saved {output_path} but failed to delete original: {del_err}")

                try:

                    original_size = os.path.getsize(file_path)
                    resized_size = os.path.getsize(output_path)

                    logger.info(
                        f"[INFO] Original={original_size} bytes | "
                        f"Resized={resized_size} bytes"
                    )

                    # resized is smaller -> keep resized, delete original
                    if resized_size < original_size:

                        os.remove(file_path)

                        logger.info(
                            f"[OK  ] Saved smaller resized file: {output_path} "
                            f"and deleted original: {file_path}"
                        )

                    # resized is larger/same -> delete resized, rename original
                    else:
                        os.remove(output_path)
                        os.rename(file_path, output_path)
                        logger.info(
                            f"[OK  ] Resized file was larger/same size. "
                            f"Kept original and renamed to: {output_path}"
                        )
                except Exception as del_err:
                    logger.warning(
                        f"[WARN] Size comparison/cleanup failed: {del_err}"
                    )

            else:
                logger.info(f"[OK  ] Saved {output_path} (original kept)")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] FFmpeg failed: {e}")
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error: {e}")
        time.sleep(1)

    logger.error(f"[FAIL] Skipping after retries: {file_path}")
    return False

def scan_and_process_videos(
    logger: logging.Logger,
    base_dir: str,
    ffmpeg_path: str,
    scale_width: int,
    crf: int,
    preset: str,
    delete_original: bool,
    limit: int
):
    processed = 0
    for root, _, files in os.walk(base_dir):
        for filename in sorted(files):  # deterministic order
            if processed >= limit:
                logger.info(f"[INFO] Reached limit of {limit} files. Stopping.")
                return
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, filename)
                done = transcode_video(
                    logger=logger,
                    ffmpeg_path=ffmpeg_path,
                    file_path=full_path,
                    scale_width=scale_width,
                    crf=crf,
                    preset=preset,
                    delete_original=delete_original
                )
                if done:
                    processed += 1
    if processed == 0:
        logger.info("[INFO] No eligible .mpg files found (or all were skipped).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Resize/transcode .mpg videos to H.264 MP4 with '-rs' suffix.\n"
            "Skips files already containing '-rs' and existing outputs;\n"
            "processes only N files per run (default 5)."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("directory", help="Base directory to scan recursively")
    parser.add_argument("--ffmpeg-path", default="ffmpeg",
                        help=r"Path to ffmpeg executable (e.g. C:\ffmpeg\bin\ffmpeg.exe)")
    parser.add_argument("--width", type=int, default=1280,
                        help="Target width (height auto-calculated). Default: 1280")
    parser.add_argument("--crf", type=int, default=22,
                        help="Quality (lower=better; typical 18–23). Default: 22")
    parser.add_argument("--preset", default="slow",
                        choices=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"],
                        help="x264 preset. Slower = better compression. Default: slow")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max number of videos to process this run. Default: 5")
    parser.add_argument("--delete-originals", action="store_true",
                        help="If set, delete original .mpg after a successful transcode.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    logger = setup_logger(script_dir)

    if os.path.isdir(args.directory):
        logger.info(f"[START] base_dir={args.directory} width={args.width} crf={args.crf} "
                    f"preset={args.preset} limit={args.limit} delete_originals={args.delete_originals} "
                    f"ffmpeg_path={args.ffmpeg_path}")
        scan_and_process_videos(
            logger=logger,
            base_dir=args.directory,
            ffmpeg_path=args.ffmpeg_path,
            scale_width=args.width,
            crf=args.crf,
            preset=args.preset,
            delete_original=args.delete_originals,
            limit=args.limit
        )
        logger.info("[DONE]")
    else:
        logger.error(f"[ERROR] Invalid directory: {args.directory}")
