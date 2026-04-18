from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 64 * 1024


def _file_sha256(file_path: Path) -> tuple[str, int]:
    hasher = hashlib.sha256()
    total_size = 0
    with file_path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            total_size += len(chunk)
            hasher.update(chunk)
    return hasher.hexdigest(), total_size


def _iter_manifest_entries(file_paths: Iterable[str]) -> Iterable[dict]:
    for raw_path in file_paths:
        path = Path(raw_path)
        digest, size = _file_sha256(path)
        yield {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "filename": path.name,
            "hash": digest,
            "size_bytes": size,
        }


def generate_chain_of_custody(file_paths: list) -> dict:
    # FRE 702 + TRE 901(b)(9): deterministic hashing supports reliable methodology and system verification.
    entries = list(_iter_manifest_entries(file_paths))
    sorted_hashes = sorted(entry["hash"] for entry in entries)

    combined_hash = None
    if sorted_hashes:
        combined_hash = hashlib.sha256("".join(sorted_hashes).encode("utf-8")).hexdigest()

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": entries,
        "combined_hash": combined_hash,
    }

    Path("custody_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return manifest
