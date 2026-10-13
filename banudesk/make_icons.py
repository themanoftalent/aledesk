#!/usr/bin/env python3
"""Render BanuDesk icons from banudesk/brand/*.svg into every place RustDesk ships an icon.

Usage (from the repository root):  python3 banudesk/make_icons.py
Needs: pip install cairosvg pillow
"""
import io
import os
import shutil
import sys

try:
    import cairosvg
    from PIL import Image
except ImportError:
    sys.exit("make_icons.py needs: pip install cairosvg pillow")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BRAND = os.path.join(ROOT, "banudesk", "brand")
ICON_SVG = os.path.join(BRAND, "icon.svg")
TRAY_SVG = os.path.join(BRAND, "tray.svg")


def p(*parts):
    return os.path.join(ROOT, *parts)


def render(svg, size, recolor=None):
    png = cairosvg.svg2png(url=svg, output_width=size, output_height=size)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    if recolor:
        r, g, b = recolor
        alpha = im.getchannel("A")
        im = Image.new("RGBA", im.size, (r, g, b, 255))
        im.putalpha(alpha)
    return im


def padded(svg, size, inner_ratio=824 / 1024):
    """macOS-style icon: artwork at ~80% of the canvas, centred."""
    inner = int(round(size * inner_ratio))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    art = render(svg, inner)
    off = (size - inner) // 2
    canvas.alpha_composite(art, (off, off))
    return canvas


def save_png(im, *parts):
    im.save(p(*parts))
    print("  wrote", os.path.join(*parts))


def save_ico(svg, sizes, *parts):
    big = render(svg, 256)
    big.save(p(*parts), format="ICO", sizes=[(s, s) for s in sizes])
    print("  wrote", os.path.join(*parts))


def main():
    for f in (ICON_SVG, TRAY_SVG):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")

    # PNG set used by Linux packages, Cargo bundle metadata and the Sciter UI
    save_png(render(ICON_SVG, 32), "res", "32x32.png")
    save_png(render(ICON_SVG, 64), "res", "64x64.png")
    save_png(render(ICON_SVG, 128), "res", "128x128.png")
    save_png(render(ICON_SVG, 256), "res", "128x128@2x.png")
    save_png(render(ICON_SVG, 1024), "res", "icon.png")
    save_png(padded(ICON_SVG, 1024), "res", "mac-icon.png")

    # Windows icons
    save_ico(ICON_SVG, [16, 32, 48, 64, 128], "res", "icon.ico")
    save_ico(ICON_SVG, [16, 32], "res", "tray-icon.ico")
    save_ico(ICON_SVG, [16, 32, 48, 256], "flutter", "windows", "runner", "resources", "app_icon.ico")

    # macOS menu-bar template images (monochrome; macOS tints them)
    save_png(render(TRAY_SVG, 60, recolor=(25, 25, 25)), "res", "mac-tray-dark-x2.png")
    save_png(render(TRAY_SVG, 48, recolor=(255, 255, 255)), "res", "mac-tray-light-x2.png")

    # macOS application icon
    icns = padded(ICON_SVG, 1024)
    icns.save(p("flutter", "macos", "Runner", "AppIcon.icns"), format="ICNS")
    print("  wrote flutter/macos/Runner/AppIcon.icns")

    # Vector copies used inside the Flutter UI and Linux packages
    for dst in (("flutter", "assets", "icon.svg"), ("res", "scalable.svg"), ("res", "logo.svg")):
        shutil.copyfile(ICON_SVG, p(*dst))
        print("  wrote", os.path.join(*dst))


if __name__ == "__main__":
    main()
