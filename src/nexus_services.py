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
