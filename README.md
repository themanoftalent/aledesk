# AleDesk Remote Desktop

**AleDesk** is a fast, secure, and self-hosted remote desktop solution engineered for seamless screen sharing and remote administration across macOS and Windows.

---

### ✨ Features

- **Blazing Fast**: Low-latency remote desktop streaming powered by Rust and Flutter.
- **Zero Mandatory Logins**: Completely private and independent—no third-party cloud accounts, tracking, or botnet-prevention login gates.
- **End-to-End Encrypted**: Built on strong asymmetric cryptography (Ed25519) and session encryption.
- **Self-Hosted Infrastructure**: Powered by dedicated private rendezvous and relay servers.
- **Cross-Platform**: Native builds optimized for macOS (Apple Silicon & Intel) and Windows (x86_64 & ARM64).

---

### 📥 Downloads

All latest pre-compiled installers are published on the **[Releases Page](https://github.com/themanoftalent/aledesk/releases/tag/nightly)**:

| Platform | Installer | Notes |
| :--- | :--- | :--- |
| **Windows (Portable EXE)** | [**Download EXE**](https://github.com/themanoftalent/aledesk/releases/download/nightly/aledesk-windows.exe) | Single executable, zero setup needed |
| **Windows (64-bit MSI)** | [**Download MSI**](https://github.com/themanoftalent/aledesk/releases/download/nightly/aledesk-1.4.9-x86_64.msi) | Windows 10 / 11 Installer |
| **Windows (Standard EXE)** | [**Download EXE**](https://github.com/themanoftalent/aledesk/releases/download/nightly/aledesk-1.4.9-x86_64.exe) | Standalone single executable |
| **macOS (Apple Silicon)** | [**Download DMG**](https://github.com/themanoftalent/aledesk/releases/download/nightly/aledesk-1.4.9-aarch64.dmg) | macOS 11+ (M1 / M2 / M3 / M4) |

---

### 🌐 Server Configuration

AleDesk client builds automatically connect to your dedicated infrastructure:

- **ID / Rendezvous Server**: `130.61.17.63`
- **Relay Server**: `130.61.17.63:21117`
- **API Server**: `http://130.61.17.63:21114`
- **Public Key**: `9JmJFCUpo3mqtRztgV1+6C3demoYNCv2tuNp2CNqs04=`

If you ever need to manually configure another device, enter these values in **Settings ⚙️ > ID/Relay Server**.

---

### 🛠️ Building from Source

AleDesk is built using **Flutter** and **Rust**:

```bash
# Clone the repository
git clone https://github.com/themanoftalent/aledesk.git
cd aledesk

# Apply branding and configuration
python3 banudesk/ci_patch.py

# Build with Flutter
cd flutter
flutter pub get
flutter build macos # or windows
```

---

### 💡 Acknowledgements

AleDesk is inspired by RustDesk and built upon modern open-source remote desktop technology.

---

---

## ☕ Sponsor or Buy Me a Coffee

If you find this project helpful, consider supporting it or reaching out for collaboration:

[![Buy Me A Coffee](https://img.shields.io/badge/BUY%20ME%20A%20COFFEE-SUPPORT%20PROJECT-green?style=for-the-badge&logo=buymeacoffee)](https://buymeacoffee.com/themanoftalent) [![GitHub Sponsors](https://img.shields.io/badge/SPONSOR-GITHUB%20SPONSORS-ea4aaa?style=for-the-badge&logo=githubsponsors)](https://github.com/sponsors/themanoftalent) [![Let's Connect](https://img.shields.io/badge/LET%27S%20CONNECT-EMAIL-blue?style=for-the-badge&logo=gmail)](mailto:cs.akifcifci@gmail.com)

---

### 📄 License

AleDesk is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
