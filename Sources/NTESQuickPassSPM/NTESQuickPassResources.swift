import Foundation
import NTESQuickPass

/// Resource access for applications using the SPM distribution.
/// The vendor SDK also needs NTESResource.bundle at the app bundle root;
/// see Scripts/copy-resources.sh and the installation instructions.
public enum NTESQuickPassResources {
    public static let sdkVersion = "3.7.10"
    public static let baseComponentVersion = "2.0"

    public static var bundleURL: URL? {
        Bundle.module.url(forResource: "NTESResource", withExtension: "bundle")
    }

    public static var isInstalledInMainBundle: Bool {
        Bundle.main.url(forResource: "NTESResource", withExtension: "bundle") != nil
    }
}
