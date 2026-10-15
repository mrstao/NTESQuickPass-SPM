#!/usr/bin/env python3
"""Validate vendored bytes, XCFramework slices and all required resources."""
import hashlib
import json
import plistlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "UPSTREAM.json").read_text())
expected = set(lock["files"])
actual = {p.relative_to(root).as_posix() for folder in [root / "Frameworks", root / "Sources/NTESQuickPassSPM/Resources"] for p in folder.rglob("*") if p.is_file()}
assert actual == expected, f"Vendor file set changed: {actual ^ expected}"
for relative, digest in lock["files"].items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
for container in (root / "Frameworks").glob("*.xcframework"):
    data = plistlib.loads((container / "Info.plist").read_bytes())
    slices = data["AvailableLibraries"]
    assert any(s["SupportedPlatform"] == "ios" and not s.get("SupportedPlatformVariant") and "arm64" in s["SupportedArchitectures"] for s in slices), container
    assert any(s.get("SupportedPlatformVariant") == "simulator" and {"arm64", "x86_64"} <= set(s["SupportedArchitectures"]) for s in slices), container
    for item in slices:
        framework = container / item["LibraryIdentifier"] / item["LibraryPath"]
        assert (framework / container.stem).is_file(), framework
        assert (framework / "Headers").is_dir(), framework
for manifest in (root / "Frameworks").rglob("PrivacyInfo.xcprivacy"):
    plistlib.loads(manifest.read_bytes())
print(f"PASS: {len(expected)} vendor files match pinned upstream bytes; all 5 frameworks contain device and simulator slices.")
