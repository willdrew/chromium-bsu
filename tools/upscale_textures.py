#!/usr/bin/env python3
"""Regenerate data/png/*.png at 4x with Real-ESRGAN, from the ORIGINAL upstream art.

The 2000-era textures are 8x8 to 256x256 and look soft when a 4K screen magnifies them.
This upscales each one 4x with Real-ESRGAN's realesrgan-x4plus model, which keeps the
weathered-metal detail better than the anime model.

  * Sources always come from git (default rev bb7c7d3, the last upstream commit), never
    from data/png itself, so re-running never upscales an already-upscaled image.
  * Textures drawn with GL_REPEAT tile across the playfield. Upscaling them alone makes
    their edges stop matching (visible seams), so they are upscaled as a 3x3 grid of
    themselves and the centre copy is cut out - its edges match its neighbours.
  * Alpha is preserved (realesrgan-ncnn-vulkan handles RGBA).

Needs realesrgan-ncnn-vulkan (https://github.com/xinntao/Real-ESRGAN release zip) and
ImageMagick 7 (`magick`).

  tools/upscale_textures.py --esrgan /path/to/realesrgan-ncnn-vulkan [--rev bb7c7d3]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# Drawn with GL_REPEAT (src/GroundMetal.cpp, src/GroundSea.cpp).
TILED = {"gndMetalBase00.png", "gndMetalBase01.png", "gndMetalBase02.png",
         "gndMetalBlip.png", "gndBaseSea.png"}
SCALE = 4
MODEL = "realesrgan-x4plus"


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--esrgan", required=True, help="path to realesrgan-ncnn-vulkan")
    ap.add_argument("--rev", default="bb7c7d3", help="git revision holding the original art")
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
    names = subprocess.check_output(["git", "-C", root, "ls-tree", "--name-only", a.rev, "data/png/"],
                                    text=True).split()
    names = [n for n in names if n.endswith(".png")]
    esrgan_dir = os.path.dirname(os.path.abspath(a.esrgan))  # it looks for ./models

    with tempfile.TemporaryDirectory() as tmp:
        src, plain_in, plain_out = (os.path.join(tmp, d) for d in ("src", "in", "out"))
        for d in (src, plain_in, plain_out):
            os.makedirs(d)
        for n in names:
            with open(os.path.join(src, os.path.basename(n)), "wb") as f:
                f.write(subprocess.check_output(["git", "-C", root, "show", f"{a.rev}:{n}"]))

        for f in sorted(os.listdir(src)):
            p = os.path.join(src, f)
            if f in TILED:
                # 3x3 grid -> upscale -> centre crop = a seamless 4x tile.
                w, h = map(int, subprocess.check_output(
                    ["magick", "identify", "-format", "%w %h", p], text=True).split())
                grid = os.path.join(tmp, "grid-" + f)
                run("magick", p, p, p, "+append", "(", "+clone", ")", "(", "+clone", ")",
                    "-append", grid)
                up = os.path.join(tmp, "gridup-" + f)
                run(a.esrgan, "-i", grid, "-o", up, "-n", MODEL, "-s", str(SCALE), "-f", "png")
                # -strip alone is not enough: ImageMagick writes fresh date:create/modify text and
                # tIME chunks on save. exclude-chunk keeps the output free of timestamps.
                run("magick", up, "-crop", f"{w * SCALE}x{h * SCALE}+{w * SCALE}+{h * SCALE}",
                    "+repage", "-strip", "-define", "png:exclude-chunk=date,time,tIME,bKGD,cHRM",
                    os.path.join(plain_out, f))
            else:
                shutil.copy(p, plain_in)
        subprocess.run([a.esrgan, "-i", plain_in, "-o", plain_out, "-n", MODEL, "-s", str(SCALE),
                        "-f", "png"], check=True, cwd=esrgan_dir,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        dst = os.path.join(root, "data", "png")
        done = 0
        for f in sorted(os.listdir(src)):
            out = os.path.join(plain_out, f)
            if not os.path.exists(out):
                sys.exit(f"missing output for {f}")
            shutil.copy(out, os.path.join(dst, f))
            done += 1
        print(f"wrote {done} textures to {dst} ({len(TILED & set(os.listdir(src)))} seamless-tiled)")


if __name__ == "__main__":
    main()
