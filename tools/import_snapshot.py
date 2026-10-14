"""Maintainer-only import of an official Tov browser offline snapshot. No login."""
import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tov_bible.core import sha256, validate_payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "src/tov_bible/data")
    args = p.parse_args()
    source = args.source.read_bytes()
    original = json.loads(source)
    label_fields = ["lang", "book", "long_label", "short_label", "testament", "section", "initiality", "last_chapter"]
    verse_fields = ["lang", "code", "book", "chapter", "paragraph", "sentence"]
    # Allowlist: no cookies, account identifiers, notes, storage settings, dictionary.
    data = {"source_url": original["source_url"], "language": original["language"],
            "labels": [{k: r[k] for k in label_fields if k in r} for r in original["labels"]],
            "verses": [{k: r[k] for k in verse_fields} for r in original["verses"]]}
    counts = validate_payload(data)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    dataset_hash = sha256(raw)
    manifest = {"schema_version": 1, "source_url": data["source_url"], "translation": "토브성경 개역한글", "language": "kor",
                "dataset_version": original["acquired_at"][:10] + "-" + dataset_hash[:12], "acquired_at": original["acquired_at"],
                "acquisition": "Official Tov offline IndexedDB snapshot; original verse sentence preserved",
                "browser_export_sha256": sha256(source), "dataset_sha256": dataset_hash, "compressed_sha256": sha256(compressed),
                "counts": counts, "uncompressed_bytes": len(raw), "compressed_bytes": len(compressed),
                "scope": "Private personal/family use. No account data. No other Bible source."}
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        raise SystemExit("Destination is not empty; review updates before importing")
    (args.output / "kor.json.gz").write_bytes(compressed)
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
