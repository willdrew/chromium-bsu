# Chromium B.S.U. — 4K / HD fork

This is [Chromium B.S.U.](https://sourceforge.net/projects/chromium-bsu), the classic
top-down space shooter, with fixes for modern Linux, high-resolution screens and HD textures.
Upstream lives on SourceForge. This repo tracks it: `master` is an unmodified copy of
upstream, and **`4k`** is this fork.

## What's different
**Display**
- **Native-resolution fullscreen**, using `SDL_WINDOW_FULLSCREEN_DESKTOP`. A 4K monitor runs
  at 3840x2160 with no video mode switch, which plays much better on Wayland.
- **Correct rendering at whatever size the window actually gets.** That covers resized or
  compositor-shrunk windows and HiDPI. Menu clicks map correctly on widescreen.
- **Black pillarbox bars** outside the 4:3 playfield on wide screens.

**Graphics**
- **HD textures**: every texture is upscaled 4x with Real-ESRGAN (`realesrgan-x4plus`) from
  the original art. Tiling ground textures are seamless.
- **Mipmaps and trilinear filtering** for all textures, so one texture set looks right from
  1080p to 4K.

**Build and install**
- `configure` generates again on current autotools: GL/GLU/GLUT are found with pkg-config
  instead of autoconf-archive macros that break on autoconf ≥ 2.72.
- `make install DESTDIR=...` works (staged/package installs).
- The installed tree is **relocatable**: data is found relative to the executable.

The upstream release (0.9.16.1, 2016) only offers modes up to 1280x960.

## Build
```sh
autoreconf -fi
./configure --prefix="$PWD/_install"
make -j"$(nproc)" && make install
_install/bin/chromium-bsu -f      # fullscreen at your desktop's native resolution
```
You'll need SDL2, SDL2_mixer, SDL2_image, FTGL, fontconfig, GLU and freeglut development
packages, plus `autoconf-archive` and `gettext`.

## The HD textures
`tools/upscale_textures.py` regenerates `data/png/` from the original upstream art (commit
`bb7c7d3`) using [Real-ESRGAN ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN). It never
upscales its own output:
```sh
tools/upscale_textures.py --esrgan /path/to/realesrgan-ncnn-vulkan
```
The textures are a modified version of the original Chromium B.S.U. art and remain under the
Clarified Artistic License (see `COPYING`). The originals are in this repo's history.

## Status
The code fixes are intended for upstream as a separate patch series. The textures are offered
as optional.

Developed with help from an AI assistant (Claude). Every change was reviewed, built on Arch
and Ubuntu 24.04, and played at 3840x2160 and 1920x1080/1200.
