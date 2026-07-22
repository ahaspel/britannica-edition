"""Publish the download bundle to a HuggingFace dataset repo.

Prereqs (one-time):
    uv add huggingface_hub
    huggingface-cli login          # paste a WRITE token, OR set HF_TOKEN=hf_...

Usage:
    uv run python tools/publish_hf.py <namespace>/<name> [--private]

Uploads the whole ``data/derived/download/`` directory — the four data files,
the manifest, LICENSE, schema.json, and README.md (which IS the dataset card,
so the HF page renders it automatically).  Run a full rebuild first so the
bundle exists and is current.  Re-running just uploads a new revision.
"""
from __future__ import annotations

import sys
from pathlib import Path

BUNDLE = Path("data/derived/download")


def main(repo_id: str, private: bool = False) -> None:
    from huggingface_hub import HfApi

    if not (BUNDLE / "README.md").exists():
        sys.exit(f"No bundle at {BUNDLE}/ — run a rebuild (Phase 6h) first.")

    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", private=private, exist_ok=True)
    api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=str(BUNDLE),
        commit_message="Publish Encyclopædia Britannica 1911 corpus + knowledge graphs",
    )
    print(f"Published -> https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        sys.exit("Usage: publish_hf.py <namespace>/<name> [--private]")
    main(args[0], private="--private" in sys.argv)
