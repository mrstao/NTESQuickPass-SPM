#!/bin/bash
set -euo pipefail

package_root="$(cd "$(dirname "$0")/.." && pwd)"
: "${TARGET_BUILD_DIR:?Run this script in the app target Build Phases}"
: "${UNLOCALIZED_RESOURCES_FOLDER_PATH:?Missing app resource directory}"
destination="${TARGET_BUILD_DIR}/${UNLOCALIZED_RESOURCES_FOLDER_PATH}"
mkdir -p "$destination"

# Static vendor code searches for this exact bundle outside Bundle.module.
source_bundle="$package_root/Sources/NTESQuickPassSPM/Resources/NTESResource.bundle"
test -d "$source_bundle"
mkdir -p "$destination/NTESResource.bundle"
/usr/bin/rsync -a --delete "$source_bundle/" "$destination/NTESResource.bundle/"

# Preserve each vendor's privacy declaration in a separate, discoverable bundle.
# Do not merge declarations or replace an application's PrivacyInfo.xcprivacy.
for framework in NTESQuickPass EAccountApiSDK OAuth TYRZUISDK; do
    container="$package_root/Frameworks/$framework.xcframework"
    manifest=""
    for slice in "$container"/ios-*; do
        case "$slice" in *simulator*) continue ;; esac
        candidate="$slice/$framework.framework/PrivacyInfo.xcprivacy"
        if [ -f "$candidate" ]; then manifest="$candidate"; break; fi
    done
    if [ -z "$manifest" ]; then
        echo "error: Missing vendor privacy manifest for $framework" >&2
        exit 1
    fi
    privacy_bundle="$destination/NTESQuickPassSPM_${framework}_Privacy.bundle"
    mkdir -p "$privacy_bundle"
    cp "$manifest" "$privacy_bundle/PrivacyInfo.xcprivacy"
    cat > "$privacy_bundle/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>local.ntesquickpassspm.${framework}.privacy</string>
<key>CFBundleName</key><string>${framework} Privacy</string>
<key>CFBundlePackageType</key><string>BNDL</string>
<key>CFBundleVersion</key><string>1</string>
</dict></plist>
PLIST
done
echo "NTESQuickPass: copied resource bundle and four original privacy declarations."
