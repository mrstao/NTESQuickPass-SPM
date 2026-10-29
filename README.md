# NTESQuickPass-SPM

网易易盾一键登录 / 本机验证 SDK 的非官方 Swift Package Manager 封装。

| 组件 | 固定版本 |
| --- | --- |
| NTESQuickPass | 3.8.0 |
| NTESBaseComponent | 2.0 |
| 平台 | iOS 12.0+ |
| 工具链 | Xcode 15+ / Swift tools 5.9+ |
| 架构 | arm64 真机；arm64 / x86_64 模拟器 |

Package 的 iOS 12.0 声明与官方 3.7.10 podspec 一致；实际可构建的最低系统还受所用 Xcode/SDK 限制。随仓库的 SmokeApp 使用 iOS 15.0，以兼容本次验证所用的 Xcode 27；本次未验证 iOS 12–14 运行。

5 个官方 XCFramework 均直接随仓库提供，包含三大运营商依赖，无需 CocoaPods、下载插件或额外二进制服务器。模拟器可用于编译，实际号码认证需要支持的 SIM 卡和蜂窝网络。

## 1. 添加 Package

在 Xcode → File → Add Package Dependencies 输入 `https://github.com/mrstao/NTESQuickPass-SPM.git`，选择产品 **NTESQuickPass**，添加到 App target。仓库为公开仓库，无需私有仓库访问权限。

推荐选择 **Up to Next Major Version**，起始版本填写 **`3.8.0`**，对应范围为 `3.8.0..<4.0.0`。需要锁定版本时选择 **Exact Version `3.8.0`**；跟随开发分支时也可以选择 **Branch `main`**。

若此前使用 `1.0.0 – Next Major`，请将起始版本改为 `3.8.0`，再执行 File → Packages → Resolve Package Versions。`1.0.0..<2.0.0` 无法匹配 `3.7.10`。SPM 版本由仓库的 Git tag 提供，`main` 分支不会自动成为版本号。

已有项目应先移除同名 SDK 的 CocoaPods / 手动集成，避免重复符号。若其他易盾 SDK 也依赖 NTESBaseComponent，需统一由一份依赖提供。

## 2. 添加链接参数

App target → Build Settings → Other Linker Flags 添加：

```text
$(inherited) -ObjC
```

这是官方接入指南要求的配置。Package 已声明 libc++、libz 和依赖的系统框架；未使用 unsafeFlags，以允许其他 Swift Package 继续依赖此产品。

## 3. 复制官方资源（必需）

SDK 是静态库，其内部按原有 bundle 位置读取图片和运营商文件。SPM 的 Bundle.module 会多嵌套一层，因此仅添加 Package 还不够。

App target → Build Phases → 新建 Run Script Phase，放在 Copy Bundle Resources 之后，Shell 使用 `/bin/bash`，填入：

```bash
set -euo pipefail
package_root="${NTES_QUICKPASS_SPM_DIR:-}"
if [ -z "$package_root" ]; then
    checkout_root="${BUILD_DIR%/Build/*}/SourcePackages/checkouts"
    for candidate in "$checkout_root"/*; do
        if [ -f "$candidate/Scripts/copy-resources.sh" ] &&
           [ -d "$candidate/Frameworks/NTESQuickPass.xcframework" ]; then
            package_root="$candidate"
            break
        fi
    done
fi
if [ -z "$package_root" ]; then
    echo 'error: NTESQuickPass-SPM checkout not found. Set NTES_QUICKPASS_SPM_DIR to its absolute path.' >&2
    exit 1
fi
/bin/bash "$package_root/Scripts/copy-resources.sh"
```

取消这个脚本阶段的 **Based on dependency analysis**；App target 的 **User Script Sandboxing** 设置为 **No**，使脚本可以访问 Package checkout。若使用本地 Package 或 `-clonedSourcePackagesDirPath`，添加用户自定义 Build Setting `NTES_QUICKPASS_SPM_DIR`，填写对应的 Package 绝对路径。

脚本会把 `NTESResource.bundle` 放到 App 主包，同时把 4 份官方隐私清单分别保留到独立资源 bundle，不覆盖 App 自己的隐私清单。可在生成的 `.app` 中检查：

```text
YourApp.app/
  NTESResource.bundle/
  NTESQuickPassSPM_NTESQuickPass_Privacy.bundle/
  NTESQuickPassSPM_EAccountApiSDK_Privacy.bundle/
  NTESQuickPassSPM_OAuth_Privacy.bundle/
  NTESQuickPassSPM_TYRZUISDK_Privacy.bundle/
```

NTESBaseComponent 2.0 上游未附带 PrivacyInfo.xcprivacy，本封装没有代为编造声明。

## 4. 使用

Swift 原有业务代码继续导入官方模块：

```swift
import NTESQuickPass
import NTESQuickPassSPM

let model = NTESQuickLoginModel()
assert(NTESQuickPassResources.isInstalledInMainBundle,
       "请完成 README 第 3 步的资源复制配置")
```

Objective-C：

```objc
#import <NTESQuickPass/NTESQuickPass.h>

[[NTESQuickLoginManager sharedInstance] registerWithBusinessID:@"你的业务 ID"];
```

登录、预取号及服务端验 token 的业务流程保持官方 API。业务 ID 从易盾控制台获取；服务端密钥不要放入 App。

上面的 Swift 片段仅检查导入和资源，不会发起认证。一键登录在宿主 App 中还需完成：

1. 使用自己的业务 ID 初始化 `NTESQuickLoginManager`，调用 `shouldQuickLogin` 判断网络环境。
2. 预取号成功后，设置 `NTESQuickLoginModel.currentVC` 为当前可见控制器，配置自己的协议名称、链接以及包含 `《默认》` 的 `appPrivacyText`，再调用 `setupModel`。
3. 调用 `CUCMCTAuthorizeLoginCompletion` 拉起授权页；成功后把预取号的 `token` 和授权结果的 `accessToken` 交给自己的服务端调用易盾 check 接口。客户端取到 token 不等于账号登录成功。
4. 本机验证使用另一套入口 `NTESQuickPassManager.verifyPhoneNumber`，成功后同样需要服务端 check。预取号或授权失败时提供短信等降级入口。

官方说明 token 和 accessToken 有效期为两分钟且不能重复使用。双卡设备使用当前蜂窝数据卡；只有 Wi-Fi 或模拟器环境不能作为认证成功验收。

官方文档：[3.8.0 一键登录接入指南](https://github.com/yidun/NTESQuickPass/blob/3.8.0/doc/一键登录iOS%20SDK接入指南.md) · [3.8.0 本机验证接入指南](https://github.com/yidun/NTESQuickPass/blob/3.8.0/doc/本机验证%20iOS%20SDK接入指南.md)

## 官方仓库对照说明

- 已对照 3.7.10 的 podspec、两份接入文档、Demo Info.plist 和公开头文件。4 个认证 XCFramework、单独依赖的 NTESBaseComponent 2.0、NTESResource.bundle 及官方隐私清单均已包含。
- 本机验证旧文档仍列出 `TYRZSDK.framework`、`sdk_oauth.bundle` 和 `TYRZResource.bundle`；3.7.10 实际分发改为 `TYRZUISDK.xcframework`，资源只有 `Assets/NTESResource.bundle`。本封装按该版本真实分发内容打包，不混入旧版本文件。
- 官方 Demo 的 Info.plist 设置了 `NSAllowsArbitraryLoads = YES`。SPM 无法替宿主修改 Info.plist；当前 SmokeApp 只验证构建和资源，没有验证运营商请求的 ATS 兼容性。集成时应结合当前官方要求和真机失败日志确认需要的域名例外，避免直接照搬全局放开配置。
- 官方文档针对 `___llvm_profile_runtime` 链接错误给出 `-fprofile-instr-generate` 的处理方法。本次真机和两种模拟器架构链接均未遇到该问题，因此没有默认添加此参数。
- 第三方隐私清单已原样保留；业务 App 自己的隐私说明、授权页协议内容和真实认证流程仍由接入方配置。

## 验证

```bash
python3 Scripts/validate.py
swift package dump-package
xcodebuild -project Examples/SmokeApp/SmokeApp.xcodeproj -scheme SmokeApp \
  -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=NO build
xcodebuild -project Examples/SmokeApp/SmokeApp.xcodeproj -scheme SmokeApp \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build
xcodebuild -scheme NTESQuickPass-SPM \
  -destination 'platform=iOS Simulator,name=<本机可用的 iPhone 模拟器名称>' \
  CODE_SIGNING_ALLOWED=NO test
```

SmokeApp 会实际链接 SDK，并运行同一资源复制脚本。GitHub Actions 在 macOS 上执行结构校验、App 真机 / 模拟器编译和现有资源测试。

2026-10-15 本地验证：139 个上游文件 SHA-256 校验通过；真机 arm64、模拟器 arm64/x86_64 构建通过；两个现有 XCTest 测试均通过；两种平台的 App 包都包含完整的 12 个资源文件和 4 份原样隐私清单。真机构建禁用了签名，没有执行真机安装、三网认证或 App Store Archive 隐私报告验收。GitHub Actions 的实际结果请以仓库运行记录为准。

## 发布与更新

上游 tag、commit 和文件 SHA-256 记录在 `UPSTREAM.json`。二进制与资源保持官方原样，更新时需同时更新锁文件，并验证三大运营商登录和 App Archive 隐私报告。

本仓库仅提供 SPM 分发配置，不代表网易官方支持；第三方 SDK 的权利及使用条件见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
