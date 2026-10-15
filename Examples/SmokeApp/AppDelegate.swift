import UIKit
import NTESQuickPass
import NTESQuickPassSPM

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        precondition(NTESQuickPassResources.isInstalledInMainBundle)
        let model = NTESQuickLoginModel()
        _ = model
        let controller = UIViewController()
        controller.view.backgroundColor = .white
        let label = UILabel()
        label.text = "NTESQuickPass SPM loaded"
        label.translatesAutoresizingMaskIntoConstraints = false
        controller.view.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: controller.view.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: controller.view.centerYAnchor)
        ])
        window = UIWindow(frame: UIScreen.main.bounds)
        window?.rootViewController = controller
        window?.makeKeyAndVisible()
        return true
    }
}
