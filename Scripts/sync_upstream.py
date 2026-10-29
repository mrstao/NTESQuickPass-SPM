#!/usr/bin/env python3
"""Sync the latest stable NTESQuickPass tag into this SPM wrapper.

The official NTESBaseComponent is intentionally kept separately pinned.
Any upstream framework layout change stops the workflow for manual review.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/yidun/NTESQuickPass"
UPSTREAM_GIT = UPSTREAM + ".git"
FRAMEWORKS = ["NTESQuickPass", "EAccountApiSDK", "OAuth", "TYRZUISDK"]
RESOURCE_SOURCE = "Assets/NTESResource.bundle"
RESOURCE_DEST = "Sources/NTESQuickPassSPM/Resources/NTESResource.bundle"


def version_key(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Unsupported stable version: {version}")
    return tuple(int(part) for part in version.split("."))


def emit(updated, version):
    values = f"updated={'true' if updated else 'false'}\nversion={version}\n"
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as handle:
            handle.write(values)
    print(values.strip().replace("\n", " "))


def run(command, **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def copy_directory(source, destination):
    if not source.is_dir():
        raise FileNotFoundError(f"Missing upstream directory: {source}")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, symlinks=True)


def calculate_hashes():
    files = {}
    roots = [ROOT / "Frameworks", ROOT / RESOURCE_DEST]
    for base in roots:
        for path in sorted(base.rglob("*")):
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(files.items()))


def replace_once(pattern, replacement, content, label):
    updated, count = re.subn(pattern, replacement, content, count=1)
    if count != 1:
        raise RuntimeError(f"Could not update README section: {label}")
    return updated


def update_readme(current, latest):
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")

    content = replace_once(
        r"(?m)^(\| NTESQuickPass \| )\d+\.\d+\.\d+(\s*\|)$",
        rf"\g<1>{latest}\g<2>",
        content,
        "version table",
    )

    content = replace_once(
        r"(起始版本填写 \*\*\x60)\d+\.\d+\.\d+(\x60\*\*，对应范围为 \x60)"
        r"\d+\.\d+\.\d+(\.\.<4\.0\.0\x60。需要锁定版本时选择 "
        r"\*\*Exact Version \x60)\d+\.\d+\.\d+(\x60\*\*)",
        rf"\g<1>{latest}\g<2>{latest}\g<3>{latest}\g<4>",
        content,
        "SPM version recommendation",
    )

    content = replace_once(
        r"(起始版本改为 \x60)\d+\.\d+\.\d+(\x60)",
        rf"\g<1>{latest}\g<2>",
        content,
        "migration guidance",
    )

    content = replace_once(
        r"\[\d+\.\d+\.\d+ 一键登录接入指南\]",
        f"[{latest} 一键登录接入指南]",
        content,
        "quick login documentation label",
    )
    content = replace_once(
        r"\[\d+\.\d+\.\d+ 本机验证接入指南\]",
        f"[{latest} 本机验证接入指南]",
        content,
        "phone verification documentation label",
    )

    content = content.replace(f"/blob/{current}/doc/", f"/blob/{latest}/doc/")
    path.write_text(content, encoding="utf-8")


def main():
    lock_path = ROOT / "UPSTREAM.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    source = next(
        item for item in lock["sources"]
        if item["repository"] == UPSTREAM
    )
    current = source["tag"]

    output = subprocess.check_output(
        ["git", "ls-remote", "--tags", "--refs", UPSTREAM_GIT],
        text=True,
    )
    versions = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        match = re.fullmatch(r"refs/tags/(\d+\.\d+\.\d+)", fields[1])
        if match:
            versions.append(match.group(1))

    if not versions:
        raise RuntimeError("No stable semantic-version tags found.")

    latest = max(versions, key=version_key)
    if version_key(latest) <= version_key(current):
        print(f"Already up to date: {current}")
        emit(False, current)
        return

    if version_key(latest)[0] != version_key(current)[0]:
        raise RuntimeError(
            f"Major version changed: {current} -> {latest}. "
            "Manual migration required."
        )

    with tempfile.TemporaryDirectory() as temporary:
        upstream_dir = Path(temporary) / "upstream"
        run([
            "git", "clone", "--depth", "1", "--filter=blob:none",
            "--sparse", "--branch", latest, UPSTREAM_GIT,
            str(upstream_dir),
        ])
        run([
            "git", "-C", str(upstream_dir), "sparse-checkout",
            "set", "Classes", "Assets",
        ])

        podspec_path = upstream_dir / "NTESQuickPass.podspec"
        podspec = podspec_path.read_text(encoding="utf-8")
        match = re.search(
            r"""spec\.version\s*=\s*['"]([^'"]+)['"]""",
            podspec,
        )
        if not match or match.group(1) != latest:
            raise RuntimeError("Upstream podspec version does not match its tag.")

        classes_dir = upstream_dir / "Classes"
        actual = {
            path.name.removesuffix(".xcframework")
            for path in classes_dir.glob("*.xcframework")
        }
        if actual != set(FRAMEWORKS):
            raise RuntimeError(
                "Upstream framework layout changed. "
                f"Expected {FRAMEWORKS}, got {sorted(actual)}"
            )

        for name in FRAMEWORKS:
            copy_directory(
                classes_dir / f"{name}.xcframework",
                ROOT / "Frameworks" / f"{name}.xcframework",
            )

        copy_directory(
            upstream_dir / RESOURCE_SOURCE,
            ROOT / RESOURCE_DEST,
        )

        source["tag"] = latest
        source["commit"] = subprocess.check_output(
            ["git", "-C", str(upstream_dir), "rev-parse", "HEAD"],
            text=True,
        ).strip()

    # Recompute hashes for all vendored files, including the unchanged
    # NTESBaseComponent, so the lock file stays complete and deterministic.
    lock["files"] = calculate_hashes()
    lock_path.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_readme(current, latest)

    print(f"Synced upstream {current} -> {latest}")
    emit(True, latest)


if __name__ == "__main__":
    main()
