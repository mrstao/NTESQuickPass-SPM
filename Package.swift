// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NTESQuickPass-SPM",
    platforms: [.iOS(.v12)],
    products: [
        .library(name: "NTESQuickPass", targets: ["NTESQuickPassSPM"])
    ],
    targets: [
        .target(
            name: "NTESQuickPassSPM",
            dependencies: ["NTESQuickPass", "NTESBaseComponent", "EAccountApiSDK", "OAuth", "TYRZUISDK"],
            resources: [.copy("Resources/NTESResource.bundle")],
            linkerSettings: [
                .linkedLibrary("c++"),
                .linkedLibrary("z"),
                .linkedFramework("Security"),
                .linkedFramework("CoreTelephony"),
                .linkedFramework("SystemConfiguration"),
                .linkedFramework("Network")
            ]
        ),
        .binaryTarget(name: "NTESQuickPass", path: "Frameworks/NTESQuickPass.xcframework"),
        .binaryTarget(name: "NTESBaseComponent", path: "Frameworks/NTESBaseComponent.xcframework"),
        .binaryTarget(name: "EAccountApiSDK", path: "Frameworks/EAccountApiSDK.xcframework"),
        .binaryTarget(name: "OAuth", path: "Frameworks/OAuth.xcframework"),
        .binaryTarget(name: "TYRZUISDK", path: "Frameworks/TYRZUISDK.xcframework"),
        .testTarget(name: "NTESQuickPassSPMTests", dependencies: ["NTESQuickPassSPM"])
    ]
)
