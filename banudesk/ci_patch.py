#!/usr/bin/env python3
"""Build-time branding for BanuDesk. GitHub Actions runs this after every checkout.

Why at build time: libs/hbb_common is a git submodule pinned to upstream, so
edits to it cannot be committed in this fork without also forking hbb_common.
Patching after checkout keeps the fork to one repository and makes upstream
merges simple.

It sets:
  * the app name (drives config paths, Windows service name, install folder,
    macOS /Applications/<name>.app, URI scheme, and turns off RustDesk's
    auto-updater because the client now counts as a custom client)
  * the config organisation
  * your ID server and its public key, compiled in as defaults
  * your API server (address book, login) as the default instead of
    admin.rustdesk.com

Environment (GitHub repository secrets):
  BANUDESK_ID_SERVER   e.g. remote.bandirma.edu.tr or 1.2.3.4
  BANUDESK_KEY         contents of id_ed25519.pub on the server
  BANUDESK_API_SERVER  optional, default http://<ID server host>:21114

Leave BOTH unset to build against RustDesk's public servers (testing only).

Local dry run:
  BANUDESK_ID_SERVER=example.org BANUDESK_KEY=<44-char key> python3 banudesk/ci_patch.py
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
B = json.load(open(os.path.join(ROOT, "banudesk", "brand.json"), encoding="utf-8"))


def fail(msg):
    print(f"::error::BanuDesk ci_patch: {msg}")
    sys.exit(1)


def sub_once(path, pattern, repl, label):
    full = os.path.join(ROOT, path)
    text = open(full, encoding="utf-8").read()
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n == 0:
        if re.search(re.escape(repl), text):
            print(f"  already set: {label}")
            return
        fail(f"{path}: could not find {label}; upstream moved it, update ci_patch.py")
    open(full, "w", encoding="utf-8", newline="").write(new)
    print(f"  set {label}")


def main():
    server = (os.environ.get("ALEDESK_ID_SERVER") or os.environ.get("BANUDESK_ID_SERVER") or "").strip()
    key = (os.environ.get("ALEDESK_KEY") or os.environ.get("BANUDESK_KEY") or "").strip()
    api = (os.environ.get("ALEDESK_API_SERVER") or os.environ.get("BANUDESK_API_SERVER") or "").strip()

    app = B["app_name"]
    org = B["org"]
    cfg = "libs/hbb_common/src/config.rs"

    if not server and not key:
        # Public-server mode: brand the app but keep RustDesk's public ID/relay
        # servers, so a build works before your own server exists. Add the
        # secrets and rebuild to switch to your own server.
        print(f"::warning::BanuDesk: no server secrets set, building against RustDesk public servers")
        sub_once(cfg,
                 r'(pub static ref APP_NAME: RwLock<String> = RwLock::new\(")[^"]*(".to_owned\(\)\);)',
                 rf'\g<1>{app}\g<2>', "APP_NAME")
        sub_once(cfg,
                 r'(pub static ref ORG: RwLock<String> = RwLock::new\(")[^"]*(".to_owned\(\)\);)',
                 rf'\g<1>{org}\g<2>', "ORG")
        print("Done (public-server mode).")
        return
    if not server:
        fail("BANUDESK_KEY is set but BANUDESK_ID_SERVER is empty. Set both, or neither for public-server mode.")
    if not re.fullmatch(r"[A-Za-z0-9.\-]+(:\d{2,5})?", server):
        fail(f"BANUDESK_ID_SERVER must be a host or host:port, no scheme. Got {server!r}")
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
        fail("BANUDESK_KEY must be the 44-character base64 public key from id_ed25519.pub")
    host = server.split(":")[0]
    if not api:
        api = f"http://{host}:21114"
    if not re.fullmatch(r"https?://[A-Za-z0-9.\-]+(:\d{2,5})?(/[^\s\"]*)?", api):
        fail(f"BANUDESK_API_SERVER must look like http(s)://host[:port]. Got {api!r}")
    api = api.rstrip("/")

    print(f"Applying {app} branding, server {server}, api {api}")

    sub_once(cfg,
             r'(pub static ref APP_NAME: RwLock<String> = RwLock::new\(")[^"]*(".to_owned\(\)\);)',
             rf'\g<1>{app}\g<2>', "APP_NAME")
    sub_once(cfg,
             r'(pub static ref ORG: RwLock<String> = RwLock::new\(")[^"]*(".to_owned\(\)\);)',
             rf'\g<1>{org}\g<2>', "ORG")
    sub_once(cfg,
             r'^pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
             f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{server}"];', "RENDEZVOUS_SERVERS")
    sub_once(cfg,
             r'^pub const RS_PUB_KEY: &str = "[^"]*";',
             f'pub const RS_PUB_KEY: &str = "{key}";', "RS_PUB_KEY")
    sub_once("src/common.rs",
             r'"https://admin\.rustdesk\.com"\.to_owned\(\)',
             f'"{api}".to_owned()', "default API server")
    # Remove powered by RustDesk override so custom branding applies globally
    lang_rs = os.path.join(ROOT, "src/lang.rs")
    if os.path.exists(lang_rs):
        content = open(lang_rs, encoding="utf-8").read()
        if '&& name != "powered_by_me"' in content:
            open(lang_rs, "w", encoding="utf-8", newline="").write(
                content.replace('&& name != "powered_by_me"', '')
            )
            print("  removed powered_by_me exception in src/lang.rs")

    print("Done.")


if __name__ == "__main__":
    main()
