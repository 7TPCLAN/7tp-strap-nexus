# 7TP Nexus Strap

**PLAY. CREATE. OPTIMIZE.**  
By 7TPCLAN — Developer: ThunderPainYT

7TP Nexus Strap is a Windows-first desktop utility built with Python and PySide6, using an original 7TP interface and modular local services.

## Implemented in this build
- **Dashboard:** quick access and live system summary.
- **Nexus Boost:** read-only CPU and memory monitoring.
- **Nexus Capture:** Roblox video recording with frame-rate and quality choices. The Windows GitHub Actions build bundles an LGPL FFmpeg executable, so users do not need to install FFmpeg separately or edit PATH. Recording is video-only; system/game audio is not captured yet. The release uses FFmpeg’s native MPEG-4 video encoder.
- **Nexus Packs:** import JSON replacement-rule texture packs only. ZIP, RAR, and folder imports are not supported. JSON packs are validated and stored; actual in-game asset replacement is not yet implemented.
- **Nexus Skies:** create local six-face sky presets from one image or six images; images are resized to 512×512 PNGs. Applying these presets to Roblox is not implemented.
- **FastFlag Studio:** edit, validate, save and export JSON settings files. Exporting does not automatically modify Roblox files.
- **Nexus Profiles:** save and reload named JSON configurations. The launcher also reads `launcher_rules.json` from the app configuration folder to choose a Roblox app-protocol launch and whether to fall back to the installed Player executable.

## Run locally
1. Install Python 3.10 or newer.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Start the app: `python src/main.py`

## Windows build
GitHub Actions downloads an LGPL FFmpeg Windows build, bundles it with the app, packages everything into a single `7TP-Nexus-Strap-Setup.exe` installer using Inno Setup, and uploads that installer as the build artifact. Pushing a version tag such as `v0.1.0` publishes a GitHub Release with the setup EXE as its only attached release asset. The installed app includes FFmpeg license and third-party notices.

## Third-party software and licensing
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for FFmpeg build and license information. The Windows release includes the LGPL license text beside the application.

## Reference projects and licensing
- [Fleasion](https://github.com/fleasion/Fleasion) was reviewed as a reference for texture-pack/asset workflows. Its repository is GPL-3.0; this project does not copy its source code.
- [Voidstrap](https://github.com/KloBraticc/Voidstrap) was reviewed for feature ideas such as configuration, custom sky presets and launcher settings. Its repository includes MIT-licensed components and other notices; this project does not copy its source code.

Nexus Strap is an independent implementation. Compatibility varies by game and platform. It does not bypass anti-cheat or promise unsupported game-file modifications.

## Current limitations
This is an early functional foundation, not a finished replacement for either reference project. JSON replacement-rule packs can currently be imported, validated and inspected. Their rules are not automatically applied because the replacement engine and exact pack mapping format have not yet been verified against a real compatible pack. The launcher now requests the Roblox app protocol (`roblox://`) instead of opening Roblox Home in a browser; the protocol may open the app without joining a specific experience. Launcher rules are stored in `launcher_rules.json` under the Nexus app configuration directory. Launcher replacement, audio capture, update delivery and in-app crash reporting are not implemented.
