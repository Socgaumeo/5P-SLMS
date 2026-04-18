#!/usr/bin/env python3
"""Extract embedded images (logos) from DAINESE Excel files via zip extraction."""

import sys
import zipfile
import shutil
from pathlib import Path


def extract_images(xlsx_path, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = Path(xlsx_path).stem
    safe_base = "".join(c if c.isalnum() or c in '-_' else '_' for c in base)

    with zipfile.ZipFile(xlsx_path) as z:
        media = [n for n in z.namelist() if n.startswith('xl/media/')]
        for name in media:
            ext = Path(name).suffix
            target = out / f"{safe_base}__{Path(name).name}"
            with z.open(name) as src, open(target, 'wb') as dst:
                shutil.copyfileobj(src, dst)
            print(f"Extracted: {target}")
        return media


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: extract-images-and-embedded-objects-from-dainese-excel.py <xlsx> <out_dir>")
        sys.exit(1)
    extract_images(sys.argv[1], sys.argv[2])
