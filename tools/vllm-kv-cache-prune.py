#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bound the filesystem-backed vLLM KV cache by evicting oldest block files."""

import fcntl
import os
import stat
import sys
from pathlib import Path


ROOT = Path(
    os.environ.get("KV_DISK_CACHE_DIR", "/mnt/models/vLLM/kv-cache")
).resolve()
LIMIT = int(os.environ.get("KV_DISK_MAX_BYTES", str(60 * 1024**3)))
LOW_WATERMARK = LIMIT * 9 // 10

if LIMIT <= 0:
    print("KV_DISK_MAX_BYTES must be positive", file=sys.stderr)
    raise SystemExit(2)

ROOT.mkdir(parents=True, exist_ok=True)
lock_path = ROOT / ".quota-prune.lock"
with lock_path.open("a") as lock:
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(0)

    candidates = []
    total = 0
    for directory, subdirs, filenames in os.walk(ROOT, followlinks=False):
        subdirs[:] = [
            name
            for name in subdirs
            if not (Path(directory) / name).is_symlink()
        ]
        for name in filenames:
            if not name.endswith(".bin"):
                continue
            path = Path(directory) / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            total += info.st_size
            candidates.append((info.st_mtime_ns, str(path), info.st_size))

    if total <= LIMIT:
        print(f"KV cache: {total / 1024**3:.2f} GiB / {LIMIT / 1024**3:.2f} GiB")
        raise SystemExit(0)

    candidates.sort()
    removed = 0
    for mtime_ns, raw_path, size in candidates:
        if total <= LOW_WATERMARK:
            break
        path = Path(raw_path)
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                continue
            if info.st_mtime_ns != mtime_ns or info.st_size != size:
                continue
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError as error:
            print(f"Could not evict {path}: {error}", file=sys.stderr)
            continue
        total -= size
        removed += size

    print(
        f"KV cache pruned: removed {removed / 1024**3:.2f} GiB; "
        f"remaining {total / 1024**3:.2f} GiB; "
        f"limit {LIMIT / 1024**3:.2f} GiB"
    )
    if total > LIMIT:
        print(
            "KV cache remains over limit; some files could not be removed",
            file=sys.stderr,
        )
        raise SystemExit(1)
