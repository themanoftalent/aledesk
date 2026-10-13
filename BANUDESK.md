# BanuDesk build kit

BanuDesk is a rebranded fork of RustDesk 1.4.9 for Bandırma Onyedi Eylül University. It runs on Windows and macOS, connects only to your own server, keeps its own name, config folders, Windows service, macOS bundle and URI scheme, so it can sit next to a stock RustDesk install without collisions. RustDesk's auto-updater is off, so an upstream update can never replace it.

This kit contains no compiled app. GitHub Actions builds the installers in your own fork, because the client needs your server address and key compiled in.

## What is in the kit

| Path | Purpose |
| --- | --- |
| banudesk-1.4.9.patch | Every source change, pre-applied for you. Apply this and commit. |
| banudesk/brand.json | Name, bundle id, organisation, manufacturer, copyright |
| banudesk/brand/icon.svg, tray.svg | The app icon and macOS menu-bar icon |
| banudesk/rebrand.py | Regenerates the patch from brand.json (only needed if you change the name or icon, or after an upstream update) |
| banudesk/make_icons.py | Renders every icon file from the SVGs |
| banudesk/ci_patch.py | Runs inside GitHub Actions; sets the app name and bakes in your server and key |
| banudesk/server/ | docker-compose and setup script for the ID, relay and API server |

## Step 1. Server (about 15 minutes)

You need one Ubuntu 22.04 or 24.04 VM with a public IP or a DNS name, 1 vCPU and 1 GB RAM are enough for a department. Ask IT to open TCP 21114 to 21119 and UDP 21116 on the campus firewall.

```
scp -r banudesk/server you@your-server:~/banudesk-server
ssh you@your-server
cd ~/banudesk-server
sudo ./setup.sh remote.bandirma.edu.tr
```

The script installs Docker, starts the server and prints three values. Keep that output; you need it in step 3. Back up the `data` folder and `.env`. If you lose `data/server/id_ed25519`, every client must be rebuilt.

## Step 2. Fork and apply the patch (about 10 minutes)

1. Sign in to GitHub, open https://github.com/rustdesk/rustdesk/fork and create the fork with the default options.
2. On your computer:

```
git clone https://github.com/<your-user>/rustdesk.git banudesk
cd banudesk
git fetch https://github.com/rustdesk/rustdesk.git tag 1.4.9 --no-tags
git checkout -b banudesk 1.4.9
git apply --binary /path/to/banudesk-1.4.9.patch
git add -A
git commit -m "Rebrand as BanuDesk"
git push -u origin banudesk
```

3. On GitHub, open your fork, Settings, General, Default branch, and switch it to `banudesk`. Actions only shows manual workflows from the default branch.

Keep the fork public. AGPL-3.0 requires you to publish the source of the version you distribute, and a public fork does that. A public repo also gets free Actions minutes; a private one runs out quickly with macOS builds.

## Step 3. Secrets and the build (about 60 to 90 minutes, unattended)

1. Fork, Settings, Secrets and variables, Actions, New repository secret. Add the three values from step 1:
   - BANUDESK_ID_SERVER, for example `remote.bandirma.edu.tr`
   - BANUDESK_KEY, the 44-character key
   - BANUDESK_API_SERVER, for example `http://remote.bandirma.edu.tr:21114`
2. Fork, Actions tab, click "I understand my workflows, go ahead and enable them".
3. Pick "BanuDesk Build" on the left, then "Run workflow".

The build stops in its first minute with a clear error if a secret is missing or malformed. When it finishes, open Releases, then the `nightly` pre-release. You get:

| File | For |
| --- | --- |
| rustdesk-1.4.9-x86_64.exe | Windows, portable or installs itself |
| rustdesk-1.4.9-x86_64.msi | Windows, for deployment through Group Policy or SCCM |
| rustdesk-1.4.9-aarch64.exe / .msi | Windows on ARM |
| rustdesk-1.4.9-aarch64(...).dmg | Macs with Apple silicon |
| rustdesk-1.4.9-x86_64(...).dmg | Intel Macs |

The file names still say rustdesk. The app inside is BanuDesk. Renaming the release files is cosmetic and left for later so the upstream packaging steps stay untouched.

## Step 4. Install

Windows: run the exe or msi. Because the build is unsigned, SmartScreen shows "Windows protected your PC". Click More info, then Run anyway. The app installs to `C:\Program Files\BanuDesk` and registers a `BanuDesk` service.

macOS: open the dmg and drag BanuDesk to Applications. Because the build is unsigned, the first launch is blocked. Run this once in Terminal, then open the app:

```
xattr -dr com.apple.quarantine /Applications/BanuDesk.app
```

Then grant System Settings, Privacy and Security, Screen Recording and Accessibility to BanuDesk. Without both, the Mac can be seen but not controlled.

Address book: in BanuDesk, log in with an account created in the web admin at `http://<server>:21114/_admin/`. Address books then sync across your machines.

## Before university-wide rollout

The unsigned builds are fine for a pilot in your own labs. For hundreds of users, three things remain:

- macOS: an Apple Developer ID and notarization. The workflow already supports it through the MACOS_P12_BASE64, MACOS_P12_PASSWORD and MACOS_CODESIGN_IDENTITY secrets plus a notarization key. Without it, every Mac user has to run the Terminal command above.
- Windows: a code-signing certificate, or deploy the msi through Group Policy so users never see SmartScreen.
- TLS for the API server: put it behind a reverse proxy with HTTPS before people log in from off campus, since logins currently travel over plain HTTP. Remote sessions themselves are end-to-end encrypted regardless.

## Changing the name or icon

Edit `banudesk/brand.json` or the SVGs, then from the repository root:

```
pip install cairosvg pillow
python3 banudesk/rebrand.py
git add -A && git commit -m "Update branding" && git push
```

## Updating to a new RustDesk release

```
git remote add upstream https://github.com/rustdesk/rustdesk.git
git fetch upstream --tags
git checkout -b banudesk-<new> <new-tag>
git checkout banudesk -- banudesk
python3 banudesk/rebrand.py
```

`rebrand.py` and `ci_patch.py` stop with a named error when upstream moved something they edit, so a half-branded build cannot slip through. Fix the named spot, commit, and run the build. Do this for every upstream security release; that is the ongoing cost of owning a fork.

## How it was tested

- `rebrand.py` applied cleanly to RustDesk 1.4.9 and is idempotent (a second run changes nothing).
- `ci_patch.py` rejects malformed secrets and edits the five build-time values; the patched `hbb_common` crate compiles with `cargo check`.
- Both workflow files parse as valid YAML; only the Windows and macOS jobs remain active.
- Not yet tested: a full GitHub Actions build. That runs in your fork in step 3. If it fails, send me the log of the failing step.
