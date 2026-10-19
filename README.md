# 7TP Nexus Strap

**PLAY. CREATE. OPTIMIZE.**  
By 7TPCLAN — Developer: ThunderPainYT

7TP Nexus Strap is a Windows-first desktop utility built with Python and PySide6, using an original 7TP interface and modular local services.

## Implemented in this build
- **Dashboard:** quick access and live system summary.
- **Nexus Boost:** read-only CPU and memory monitoring.
- **Nexus Capture:** optional FFmpeg desktop video recording, with frame-rate and quality choices. FFmpeg must be installed separately and available on PATH. This initial recorder captures video only, without system/game audio.
- **Nexus Packs:** import supported image/texture files from ZIP archives or folders into Nexus-managed storage. ZIP path traversal and archive-size limits are checked. This does not automatically apply packs to Roblox.
- **Nexus Skies:** create local six-face sky presets from one image or six images; images are resized to 512×512 PNGs. Applying these presets to Roblox is not implemented.
- **FastFlag Studio:** edit, validate, save and export JSON settings files. Exporting does not automatically modify Roblox files.
- **Nexus Profiles:** save and reload named JSON configurations.

## Run locally
1. Install Python 3.10 or newer.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Start the app: `python src/main.py`

## Windows build
GitHub Actions builds a Windows executable artifact on pushes to the main branch when app/dependency/workflow files change, or when manually triggered from the Actions tab.

## Reference projects and licensing
- [Fleasion](https://github.com/fleasion/Fleasion) was reviewed as a reference for texture-pack/asset workflows. Its repository is GPL-3.0; this project does not copy its source code.
- [Voidstrap](https://github.com/KloBraticc/Voidstrap) was reviewed for feature ideas such as configuration, custom sky presets and launcher settings. Its repository includes MIT-licensed components and other notices; this project does not copy its source code.

Nexus Strap is an independent implementation. Compatibility varies by game and platform. It does not bypass anti-cheat or promise unsupported game-file modifications.

## Current limitations
This is an early functional foundation, not a finished replacement for either reference project. Roblox-specific pack application, launcher replacement, automatic FastFlag installation, game patching, audio capture, update delivery and in-app crash reporting are not implemented.
