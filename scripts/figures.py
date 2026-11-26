"""Convert figures to WebP, upload them to R2 and record them in content/figures.lock.json.

    python scripts/figures.py push           upload new and changed figures
    python scripts/figures.py push --local   only convert and record (R2 not set up yet)
    python scripts/figures.py selftest
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageOps

from validate import FIGURES, LOCK, ROOT, load_lock

OUT = ROOT / ".build-cache" / "figures"
MAX_WIDTH = 1600


def convert(source, target):
    """Write `source` as WebP at most MAX_WIDTH wide. Returns (width, height)."""
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGBA" if image.has_transparency_data else "RGB")
        if image.width > MAX_WIDTH:
            image = image.resize((MAX_WIDTH, round(image.height * MAX_WIDTH / image.width)), Image.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Diagrams (png) stay lossless so thin lines do not blur.
        image.save(target, "WEBP", lossless=Path(source).suffix.lower() == ".png", quality=85, method=6)
        return image.size


def upload(bucket, key, path):
    npx = shutil.which("npx") or sys.exit("figures: install Node (npx) first")
    subprocess.run(
        [npx, "--yes", "wrangler", "r2", "object", "put", f"{bucket}/{key}", "--file", str(path),
         "--content-type", "image/webp", "--remote"],
        check=True,
    )


def push(local):
    files = sorted(p for p in FIGURES.glob("*") if p.suffix in (".png", ".jpg"))
    stems = [p.stem for p in files]
    clashes = sorted({s for s in stems if stems.count(s) > 1})
    if clashes:
        sys.exit(f"figures: two files share a name (png and jpg): {', '.join(clashes)}")
    bucket = yaml.safe_load((ROOT / "site.yml").read_text(encoding="utf-8"))["r2_bucket"]
    lock, done = load_lock(), 0
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        old = lock.get(path.name, {})
        if old.get("sha256") == digest and (local or old.get("uploaded")):
            continue
        webp = OUT / f"{path.stem}.webp"
        width, height = convert(path, webp)
        if not local:
            upload(bucket, f"fig/{webp.name}", webp)
        lock[path.name] = {"sha256": digest, "width": width, "height": height, "uploaded": not local}
        # Saved after every file, so a failed upload keeps the earlier ones.
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        done += 1
    waiting = sum(not info.get("uploaded") for info in lock.values())
    print(f"figures: {done} {'recorded' if local else 'uploaded'}, {len(files)} local, {waiting} not yet uploaded")


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        source, target = Path(tmp, "big.png"), Path(tmp, "big.webp")
        Image.new("RGB", (3200, 1000), "white").save(source)
        assert convert(source, target) == (1600, 500)
        with Image.open(target) as out:
            assert out.format == "WEBP" and out.size == (1600, 500)
    print("figures selftest: ok")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["push", "selftest"])
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    selftest() if args.command == "selftest" else push(args.local)
