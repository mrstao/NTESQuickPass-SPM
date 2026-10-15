import XCTest
import NTESQuickPass
import NTESQuickPassSPM

final class ResourceTests: XCTestCase {
    func testPackagedImagesAndCarrierFilesExist() throws {
        let url = try XCTUnwrap(NTESQuickPassResources.bundleURL)
        for path in ["back@3x.png", "checked.png", "ctc.png", "cucc.png", "files/aes.js", "files/md5.js"] {
            XCTAssertTrue(FileManager.default.fileExists(atPath: url.appendingPathComponent(path).path), path)
        }
    }

    func testPublicSDKModelLinks() {
        XCTAssertNotNil(NTESQuickLoginModel())
    }
}
