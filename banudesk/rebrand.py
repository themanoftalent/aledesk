#!/usr/bin/env python3
"""One-time rebrand of a RustDesk 1.4.9 fork into BanuDesk.

Run once from the repository root, review `git diff`, then commit:
    python3 banudesk/rebrand.py

What it changes (all in the main repository, so the change is committed):
  * product name, description, copyright and macOS bundle id in the build metadata
  * the macOS app bundle name (BanuDesk.app) everywhere the build expects it
  * the URI scheme registered on macOS (banudesk://)
  * the Windows MSI: custom-client mode, app name, manufacturer
  * GitHub Actions: Windows + macOS only, manual trigger only, and a step that
    runs banudesk/ci_patch.py after every checkout (that script brands the
    hbb_common submodule and bakes in your server, see ci_patch.py)
  * every icon, rendered from banudesk/brand/*.svg

It is safe to run twice: each edit checks whether it was already applied.
Every edit fails loudly if upstream moved the text it expects, so a future
upstream merge cannot silently ship a half-branded build.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
B = json.load(open(os.path.join(ROOT, "banudesk", "brand.json"), encoding="utf-8"))
APP = B["app_name"]
APP_LC = APP.lower()
BUNDLE = B["bundle_id"]
MANU = B["manufacturer"]
DESC = B["description"]
COPY = B["copyright"]

errors = []


def rel(path):
    return os.path.relpath(path, ROOT)


def edit(path, pairs, regex=False):
    """Apply (old, new) replacements. Skip pairs already applied; record failures."""
    full = os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as f:
        text = f.read()
    orig = text
    for old, new in pairs:
        if regex:
            text2, n = re.subn(old, new, text, flags=re.M)
            if n == 0 and new not in text:
                errors.append(f"{path}: pattern not found: {old}")
            text = text2
        else:
            if old in text:
                text = text.replace(old, new)
            elif new not in text:
                errors.append(f"{path}: text not found: {old!r}")
    if text != orig:
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print("  edited", path)
    else:
        print("  unchanged", path)


def remove(path):
    full = os.path.join(ROOT, path)
    if os.path.exists(full):
        os.remove(full)
        print("  removed", path)


CI_STEP = """
      - name: Apply BanuDesk branding and server
        shell: bash
        env:
          BANUDESK_ID_SERVER: ${{ secrets.BANUDESK_ID_SERVER }}
          BANUDESK_KEY: ${{ secrets.BANUDESK_KEY }}
          BANUDESK_API_SERVER: ${{ secrets.BANUDESK_API_SERVER }}
        run: python3 banudesk/ci_patch.py
"""

# Jobs we do not build. The fork targets Windows and macOS only; this also
# keeps a public fork well inside the free Actions minutes.
SKIP_JOBS = [
    "build-for-windows-sciter",
    "build-rustdesk-ios",
    "build-rustdesk-android",
    "build-rustdesk-android-universal",
    "build-rustdesk-linux",
    "build-rustdesk-linux-sciter",
    "build-appimage",
    "build-flatpak",
    "build-rustdesk-web",
    "publish_unsigned",
]


def patch_build_workflow():
    path = ".github/workflows/flutter-build.yml"
    full = os.path.join(ROOT, path)
    text = open(full, encoding="utf-8").read()
    orig = text

    # 1. macOS bundle name and MSI branding
    text = text.replace('"RustDesk.app"', f'"{APP}.app"')
    text = text.replace("Release/RustDesk.app", f"Release/{APP}.app")
    msi_old = "python preprocess.py --arp -d ../../rustdesk"
    msi_new = (f'python preprocess.py --arp -c --app-name {APP} '
               f'-m "{MANU}" -d ../../rustdesk')
    if msi_old in text:
        text = text.replace(msi_old, msi_new)
    elif msi_new not in text:
        errors.append(f"{path}: MSI preprocess line not found")

    # 2. disable jobs we do not need
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m and m.group(1) in SKIP_JOBS:
            # drop an existing job-level `if:` within the next few header lines
            j = i + 1
            header = []
            while j < len(lines) and not lines[j].startswith("    steps:") and \
                    not re.match(r"^  [A-Za-z0-9_-]+:\s*$", lines[j]):
                header.append(lines[j])
                j += 1
            header = [h for h in header if not re.match(r"^    #?\s*if:", h)]
            out.append("    if: false # BanuDesk: Windows and macOS only")
            out.extend(header)
            i = j
            continue
        i += 1
    text = "\n".join(out)
    # collapse duplicate markers on re-run
    text = re.sub(r"(    if: false # BanuDesk: Windows and macOS only\n)(    if: false # BanuDesk: Windows and macOS only\n)+",
                  r"\1", text)

    # 3. run ci_patch.py right after every recursive checkout
    if "banudesk/ci_patch.py" not in text:
        pat = re.compile(r"(\n      - name: Checkout source code\n(?:        .*\n)*?          submodules: recursive\n)")
        text, n = pat.subn(lambda m: m.group(1) + CI_STEP.lstrip("\n"), text)
        if n == 0:
            errors.append(f"{path}: no recursive checkout steps found")
        else:
            print(f"  inserted ci_patch step after {n} checkouts")

    text = text.replace("name: Build the flutter version of the RustDesk",
                        f"name: Build {APP}")
    if text != orig:
        open(full, "w", encoding="utf-8", newline="").write(text)
        print("  edited", path)
    else:
        print("  unchanged", path)


def main():
    print(f"Rebranding to {APP} ({BUNDLE})")

    # Cargo metadata: Windows file properties and the cargo-bundle macOS info
    edit("Cargo.toml", [
        ('description = "RustDesk Remote Desktop"', f'description = "{DESC}"'),
        ('LegalCopyright = "Copyright © 2026 Purslane Tech Pte. Ltd. All rights reserved."',
         f'LegalCopyright = "{COPY}"'),
        ('ProductName = "RustDesk"', f'ProductName = "{APP}"'),
        ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{DESC}"'),
        ('name = "RustDesk"\nidentifier = "com.carriez.rustdesk"',
         f'name = "{APP}"\nidentifier = "{BUNDLE}"'),
    ])
    edit("libs/portable/Cargo.toml", [
        ('description = "RustDesk Remote Desktop"', f'description = "{DESC}"'),
        ('ProductName = "RustDesk"', f'ProductName = "{APP}"'),
        ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{DESC}"'),
    ])

    # Windows executable resources
    edit("flutter/windows/runner/Runner.rc", [
        ('VALUE "CompanyName", "Purslane Tech Pte. Ltd."', f'VALUE "CompanyName", "{MANU}"'),
        ('VALUE "FileDescription", "RustDesk Remote Desktop"', f'VALUE "FileDescription", "{DESC}"'),
        ('VALUE "LegalCopyright", "Copyright © 2026 Purslane Tech Pte. Ltd. All rights reserved."',
         f'VALUE "LegalCopyright", "{COPY}"'),
        ('VALUE "ProductName", "RustDesk"', f'VALUE "ProductName", "{APP}"'),
    ])

    # macOS app: bundle name, bundle id, URL scheme
    edit("flutter/macos/Runner/Configs/AppInfo.xcconfig", [
        (r"^PRODUCT_NAME = .*$", f"PRODUCT_NAME = {APP}"),
        (r"^PRODUCT_BUNDLE_IDENTIFIER = .*$", f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE}"),
        (r"^PRODUCT_COPYRIGHT = .*$", f"PRODUCT_COPYRIGHT = {COPY}"),
    ], regex=True)
    edit("flutter/macos/Runner.xcodeproj/project.pbxproj", [
        ("RustDesk.app", f"{APP}.app"),
        ("PRODUCT_BUNDLE_IDENTIFIER = com.carriez.rustdesk;", f"PRODUCT_BUNDLE_IDENTIFIER = {BUNDLE};"),
    ])
    edit("flutter/macos/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme", [
        ('BuildableName = "RustDesk.app"', f'BuildableName = "{APP}.app"'),
    ])
    edit("flutter/macos/Runner/Info.plist", [
        ("<string>com.carriez.rustdesk</string>", f"<string>{BUNDLE}</string>"),
        ("<string>rustdesk</string>", f"<string>{APP_LC}</string>"),
    ])

    # build.py copies the service binary into the .app; its path must match
    edit("build.py", [
        ("RustDesk.app", f"{APP}.app"),
        ('--volname \\"RustDesk Installer\\"', f'--volname \\"{APP} Installer\\"'),
    ])
    edit("res/osx-dist.sh", [("RustDesk.app", f"{APP}.app")])

    # Desktop tab bar shows a literal "RustDesk" next to the logo
    edit("flutter/lib/desktop/widgets/tabbar_widget.dart", [
        ('child: const Text(\n                              "RustDesk",',
         f'child: const Text(\n                              "{APP}",'),
    ])

    # Workflows: keep only what the Windows/macOS build needs
    for wf in ("ci.yml", "flutter-ci.yml", "fdroid.yml", "flutter-tag.yml", "playground.yml"):
        remove(f".github/workflows/{wf}")
    remove(".github/workflows/flutter-nightly.yml")
    nightly = os.path.join(ROOT, ".github/workflows/banudesk-build.yml")
    with open(nightly, "w", encoding="utf-8", newline="") as f:
        f.write(f"""name: {APP} Build

on:
  workflow_dispatch:

jobs:
  build:
    # New repositories give workflows a read-only token; publishing the
    # installers to the "nightly" release needs write access.
    permissions:
      contents: write
    uses: ./.github/workflows/flutter-build.yml
    secrets: inherit
    with:
      upload-artifact: true
      upload-tag: "nightly"
""")
    print("  wrote .github/workflows/banudesk-build.yml")
    patch_build_workflow()

    # Icons
    print("Rendering icons")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "banudesk", "make_icons.py")])
    if r.returncode != 0:
        errors.append("make_icons.py failed")

    if errors:
        print("\nFAILED. Upstream changed these spots; fix them by hand or update rebrand.py:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"\nDone. Review with `git diff --stat`, then commit.")


if __name__ == "__main__":
    main()
