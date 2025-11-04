#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Zero‑overwrite a drive or file.")
    parser.add_argument("path", help="Path to device or file to wipe.")
    parser.add_argument("--chunk-size", type=int, default=1024 * 1024,
                        help="Size of the zero buffer to write each iteration (bytes).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without performing the wipe.")
    parser.add_argument("--wipe-all", action="store_true",
                        help="Wipe all drives, including the system drive (use with extreme caution).")
    return parser.parse_args()

def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to a human‑friendly string."""
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if size_bytes < 1024:
            return f"{size_bytes:6.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:6.2f} EiB"

def confirm_path(target: Path, wipe_all: bool) -> bool:
    """Ask the user to confirm that they really want to wipe this target."""
    if not wipe_all:
        print("\n######################### WARNING #########################")
        print(f"You are about to **PERMANENTLY ERASE** everything on:\n  {target}")
        print("This action cannot be undone.")
        confirmation = input(f"Type the target path again ({target}): ").strip()
        return confirmation == str(target)
    return True

def wipe(target: Path, chunk_size: int, dry_run: bool):
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")

    # Get total size
    try:
        total_size = target.stat().st_size
    except Exception:
        total_size = None

    if total_size is None:
        print("Could not determine size via stat(). Proceeding with blind wipe.")
    else:
        print(f"Total size to wipe: {human_readable_size(total_size)}")

    if dry_run:
        print("\nDry‑run mode – no data will actually be written.")
        sys.exit(0)

    zero_buffer = bytes(chunk_size)

    start_time = time.time()
    written = 0

    with open(target, "wb") as f:
        while True:
            written_bytes = f.write(zero_buffer)
            if written_bytes == 0:
                break
            written += written_bytes

            # Progress output
            if total_size:
                percent = (written / total_size) * 100
                sys.stdout.write(f"\rWritten: {human_readable_size(written)} ({percent:6.2f}%)")
            else:
                sys.stdout.write(f"\rWritten: {human_readable_size(written)}")
            sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\nDone! Total written: {human_readable_size(written)} in {elapsed:.1f}s ({written/elapsed/1024/1024:.2f} MiB/s)")

def main():
    args = parse_args()
    target = Path(args.path).resolve()

    if not confirm_path(target, args.wipe_all):
        print("Confirmation failed. Aborting.")
        sys.exit(1)

    wipe(target, args.chunk_size, args.dry_run)

if __name__ == "__main__":
    main()
