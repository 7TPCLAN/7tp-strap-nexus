"""Local, reversible services for 7TP Nexus Strap.

These features manage user-selected files inside the app's own data directory.
They do not patch Roblox files or change game behavior automatically.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "7TPCLAN" / "NexusStrap"
PACKS_DIR = APP_DIR / "packs"
SKIES_DIR = APP_DIR / "skies"
PROFILES_DIR = APP_DIR / "profiles"
CONFIG_DIR = APP_DIR / "config"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
PACK_EXTENSIONS = IMAGE_EXTENSIONS | {".dds", ".ktx", ".ktx2"}
SKY_FACES = ("sky512_bk.png", "sky512_dn.png", "sky512_ft.png", "sky512_lf.png", "sky512_rt.png", "sky512_up.png")
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024
MAX_ARCHIVE_FILES = 5000
MAX_IMAGE_PIXELS = 16_777_216


def ensure_dirs() -> None:
    for folder in (PACKS_DIR, SKIES_DIR, PROFILES_DIR, CONFIG_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9 _.-]", "", value).strip(" .")
    name = re.sub(r"\s+", " ", name)[:60]
    if not name:
        raise ValueError("Please enter a name containing letters or numbers.")
    return name


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", safe_name(value).lower()).strip("-") or "item"


def _unique_destination(base: Path, label: str) -> Path:
    candidate = base / slug(label)
    suffix = 2
    while candidate.exists():
        candidate = base / f"{slug(label)}-{suffix}"
        suffix += 1
    return candidate


def list_packs() -> list[dict[str, Any]]:
    ensure_dirs()
    result = []
    for folder in sorted(PACKS_DIR.iterdir()):
        manifest = folder / "nexus-pack.json"
        if folder.is_dir() and manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                result.append({
                    "name": str(data.get("name", folder.name)),
                    "path": str(folder),
                    "assets": int(data.get("assets", 0)),
                    "source": str(data.get("source", "local import")),
                    "pack_type": str(data.get("pack_type", "textures")),
                    "rules": int(data.get("rules", 0)),
                })
            except (OSError, ValueError, TypeError):
                continue
    return result


def _copy_pack_folder(source: Path, staging: Path) -> int:
    count = 0
    for path in source.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name == "nexus-pack.json":
            continue
        if path.suffix.lower() not in PACK_EXTENSIONS:
            continue
        relative = path.relative_to(source)
        if any(part in {"..", "."} for part in relative.parts):
            continue
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        count += 1
    return count


def _extract_pack_zip(source: Path, staging: Path) -> int:
    total = 0
    count = 0
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError(f"Archive has too many entries (limit {MAX_ARCHIVE_FILES}).")
        for info in members:
            if info.is_dir():
                continue
            normalized = info.filename.replace("\\", "/")
            parts = Path(normalized).parts
            if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized) or ".." in parts:
                raise ValueError("The archive contains an unsafe file path and was not imported.")
            if info.file_size < 0 or info.file_size > MAX_ARCHIVE_BYTES:
                raise ValueError("The archive contains an oversized file.")
            total += info.file_size
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("The unpacked archive exceeds the 500 MB safety limit.")
            if Path(normalized).suffix.lower() not in PACK_EXTENSIONS:
                continue
            destination = staging.joinpath(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as input_file, destination.open("wb") as output_file:
                shutil.copyfileobj(input_file, output_file, length=1024 * 1024)
            count += 1
    return count


def import_pack(source_text: str, requested_name: str) -> dict[str, Any]:
    ensure_dirs()
    source = Path(source_text).expanduser().resolve()
    if not source.exists() or (not source.is_file() and not source.is_dir()):
        raise ValueError("Choose an existing ZIP archive or folder.")
    name = safe_name(requested_name)
    destination = _unique_destination(PACKS_DIR, name)
    staging = Path(tempfile.mkdtemp(prefix=".nexus-pack-", dir=PACKS_DIR))
    try:
        if source.is_dir():
            count = _copy_pack_folder(source, staging)
            source_kind = "folder"
        elif source.suffix.lower() == ".zip":
            count = _extract_pack_zip(source, staging)
            source_kind = "ZIP archive"
        else:
            raise ValueError("Please choose a ZIP archive or a folder containing pack assets.")
        if count == 0:
            raise ValueError("No supported texture files were found. Supported files include PNG, JPG, WEBP, DDS and KTX.")
        manifest = {"name": name, "assets": count, "source": source_kind, "format_version": 1}
        (staging / "nexus-pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        staging.rename(destination)
        return {"name": name, "assets": count, "path": str(destination)}
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def import_json_pack(source_text: str, requested_name: str = "") -> dict[str, Any]:
    """Validate and store a Rivals replacement-rules JSON pack without applying it."""
    ensure_dirs()
    source = Path(source_text).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".json":
        raise ValueError("Choose a .json replacement pack file.")
    if source.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("The JSON pack is larger than the 10 MB import limit.")
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("The pack must be a JSON object.")
    rules = data.get("replacement_rules")
    if not isinstance(rules, list):
        raise ValueError("This JSON does not contain a replacement_rules list.")
    if not rules:
        raise ValueError("The replacement_rules list is empty.")
    if len(rules) > 10000:
        raise ValueError("This pack contains too many replacement rules (limit 10,000).")
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule #{index} must be a JSON object.")
        if "enabled" in rule and not isinstance(rule["enabled"], bool):
            raise ValueError(f"Rule #{index}: enabled must be true or false.")
    name_value = requested_name.strip() or str(data.get("name") or data.get("pack_name") or source.stem)
    name = safe_name(name_value)
    destination = _unique_destination(PACKS_DIR, name)
    staging = Path(tempfile.mkdtemp(prefix=".nexus-json-pack-", dir=PACKS_DIR))
    try:
        saved_pack = staging / "replacement-pack.json"
        saved_pack.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest = {
            "name": name,
            "assets": 0,
            "source": "JSON replacement-rules configuration",
            "pack_type": "json-config",
            "rules": len(rules),
            "format_version": 1,
        }
        (staging / "nexus-pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        staging.rename(destination)
        enabled = sum(1 for rule in rules if rule.get("enabled", True) is True)
        return {"name": name, "rules": len(rules), "enabled": enabled, "disabled": len(rules) - enabled, "path": str(destination)}
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def read_json_pack(path_text: str) -> dict[str, Any]:
    target = Path(path_text).resolve()
    if target.parent != PACKS_DIR.resolve() or not target.is_dir():
        raise ValueError("That pack is not inside the Nexus Packs directory.")
    manifest_path = target / "nexus-pack.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Could not read this pack's manifest.") from exc
    if manifest.get("pack_type") != "json-config":
        raise ValueError("Select a JSON replacement-rules pack to inspect its rules.")
    try:
        data = json.loads((target / "replacement-pack.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Could not read the saved JSON pack.") from exc
    rules = data.get("replacement_rules")
    if not isinstance(rules, list):
        raise ValueError("Saved pack has an invalid replacement_rules list.")
    return {"name": manifest.get("name", target.name), "data": data, "rules": rules}



def delete_pack(path_text: str) -> None:
    target = Path(path_text).resolve()
    if target.parent != PACKS_DIR.resolve() or not target.is_dir():
        raise ValueError("That pack is not inside the Nexus Packs directory.")
    shutil.rmtree(target)


def list_skies() -> list[dict[str, str]]:
    ensure_dirs()
    result = []
    for folder in sorted(SKIES_DIR.iterdir()):
        if folder.is_dir() and all((folder / face).is_file() for face in SKY_FACES):
            result.append({"name": folder.name, "path": str(folder)})
    return result


def import_sky(image_paths: list[str], requested_name: str) -> dict[str, str]:
    """Create a local sky preset from one image (all faces) or six images."""
    ensure_dirs()
    if len(image_paths) not in (1, 6):
        raise ValueError("Choose one image to use on every face, or select exactly six images.")
    name = safe_name(requested_name)
    destination = _unique_destination(SKIES_DIR, name)
    staging = Path(tempfile.mkdtemp(prefix=".nexus-sky-", dir=SKIES_DIR))
    try:
        for index, face in enumerate(SKY_FACES):
            source = Path(image_paths[0 if len(image_paths) == 1 else index]).expanduser().resolve()
            if not source.is_file() or source.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("A selected image is missing or larger than 64 MB.")
            with Image.open(source) as original:
                image = ImageOps.fit(original.convert("RGB"), (512, 512), method=Image.Resampling.LANCZOS)
                image.save(staging / face, format="PNG", optimize=True)
        (staging / "nexus-sky.json").write_text(
            json.dumps({"name": name, "faces": list(SKY_FACES), "format_version": 1}, indent=2),
            encoding="utf-8",
        )
        staging.rename(destination)
        return {"name": name, "path": str(destination)}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def apply_sky_to_roblox(path_text: str) -> dict[str, str]:
    """Apply a saved six-face sky preset with timestamped backups of client files."""
    ensure_dirs()
    preset = Path(path_text).resolve()
    if preset.parent != SKIES_DIR.resolve() or not preset.is_dir():
        raise ValueError("Select a sky preset inside the Nexus Skies library.")
    if os.name != "nt":
        raise ValueError("Applying a sky to Roblox is currently supported only on Windows.")
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    versions_root = local_app_data / "Roblox" / "Versions"
    if not versions_root.is_dir():
        raise ValueError("Roblox Player was not found. Install or launch Roblox Player first.")
    candidates = []
    for version_dir in versions_root.iterdir():
        player = version_dir / "RobloxPlayerBeta.exe"
        sky_dir = version_dir / " content" / "textures" / "sky"
        if version_dir.is_dir() and player.is_file():
            actual_sky_dir = version_dir / "content" / "textures" / "sky"
            if actual_sky_dir.is_dir():
                try:
                    candidates.append((player.stat().st_mtime, version_dir, actual_sky_dir))
                except OSError:
                    continue
    if not candidates:
        raise ValueError("Could not find a Roblox Player install with content/textures/sky. Client layout can vary between versions.")
    _, version_dir, sky_dir = max(candidates, key=lambda item: item[0])
    faces = ("sky512_bk", "sky512_dn", "sky512_ft", "sky512_lf", "sky512_rt", "sky512_up")
    for face in faces:
        source = preset / f"{face}.png"
        if not source.is_file():
            raise ValueError(f"This preset is missing {face}.png; no files were changed.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = APP_DIR / "backups" / "skies" / f"{version_dir.name}_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    try:
        for face in faces:
            target = sky_dir / f"{face}.tex"
            if target.exists():
                shutil.copy2(target, backup_dir / target.name)
        for face in faces:
            shutil.copy2(preset / f"{face}.png", sky_dir / f"{face}.tex")
    except Exception:
        # Best-effort rollback if applying any face fails.
        for face in faces:
            target = sky_dir / f"{face}.tex"
            backup = backup_dir / target.name
            if backup.is_file():
                shutil.copy2(backup, target)
        raise
    return {"version": str(version_dir), "sky_dir": str(sky_dir), "backup": str(backup_dir)}


def delete_sky(path_text: str) -> None:
    target = Path(path_text).resolve()
    if target.parent != SKIES_DIR.resolve() or not target.is_dir():
        raise ValueError("That sky preset is not inside the Nexus Skies directory.")
    shutil.rmtree(target)


def load_flags() -> dict[str, Any]:
    ensure_dirs()
    path = CONFIG_DIR / "client_flags.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Could not read saved flags: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("The flags file must contain a JSON object.")
    return data


def save_flags(data: dict[str, Any]) -> None:
    ensure_dirs()
    if not isinstance(data, dict):
        raise ValueError("Flags must be a JSON object.")
    path = CONFIG_DIR / "client_flags.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def apply_flags_to_roblox(data: dict[str, Any]) -> str:
    """Write FastFlags JSON to the newest detected Roblox Player install with a backup."""
    ensure_dirs()
    if not isinstance(data, dict) or not data:
        raise ValueError("Provide a non-empty JSON object before applying settings.")
    if os.name != "nt":
        raise ValueError("Automatic FastFlag application is currently supported only on Windows.")
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    versions_root = local_app_data / "Roblox" / "Versions"
    if not versions_root.is_dir():
        raise ValueError("Roblox was not found in your Windows Local AppData folder. Install Roblox Player first.")
    candidates = []
    for version_dir in versions_root.iterdir():
        if version_dir.is_dir():
            player = version_dir / "RobloxPlayerBeta.exe"
            if player.is_file():
                try:
                    candidates.append((player.stat().st_mtime, version_dir))
                except OSError:
                    continue
    if not candidates:
        raise ValueError("Could not find RobloxPlayerBeta.exe in Roblox\\Versions. Launch/install Roblox Player, then try again.")
    version_dir = max(candidates, key=lambda item: item[0])[1]
    client_settings = version_dir / "ClientSettings"
    client_settings.mkdir(parents=True, exist_ok=True)
    target = client_settings / "ClientAppSettings.json"
    if target.exists():
        backup_dir = APP_DIR / "backups" / "fastflags"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(target, backup_dir / f"ClientAppSettings_{stamp}.json")
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)
    return str(target)


def list_profiles() -> list[str]:
    ensure_dirs()
    return sorted(path.stem for path in PROFILES_DIR.glob("*.json") if path.is_file())


def save_profile(name: str, flags: dict[str, Any]) -> str:
    ensure_dirs()
    clean = safe_name(name)
    target = PROFILES_DIR / f"{slug(clean)}.json"
    payload = {"name": clean, "client_flags": flags, "format_version": 1}
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)
    return target.stem


def load_profile(profile_id: str) -> dict[str, Any]:
    ensure_dirs()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", profile_id):
        raise ValueError("Invalid profile name.")
    target = (PROFILES_DIR / f"{profile_id}.json").resolve()
    if target.parent != PROFILES_DIR.resolve() or not target.is_file():
        raise ValueError("Profile not found.")
    data = json.loads(target.read_text(encoding="utf-8"))
    flags = data.get("client_flags", {})
    if not isinstance(flags, dict):
        raise ValueError("This profile has an invalid flags object.")
    return {"name": str(data.get("name", profile_id)), "client_flags": flags}
