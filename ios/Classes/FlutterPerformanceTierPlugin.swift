import Flutter
import UIKit
import Darwin

public class FlutterPerformanceTierPlugin: NSObject, FlutterPlugin {
  private static let deviceSignalsChannelName = "performance_tier/device_signals"
  private static let collectDeviceSignalsMethod = "collectDeviceSignals"
  private static let lowRamThresholdBytes = Int64(3 * 1024 * 1024 * 1024)
  private static let criticalMemoryWarningWindow: TimeInterval = 30
  private static let moderateMemoryWarningWindow: TimeInterval = 120

  private var lastMemoryWarningAt: Date?

  public override init() {
    super.init()
    NotificationCenter.default.addObserver(
      self,
      selector: #selector(handleMemoryWarningNotification(_:)),
      name: UIApplication.didReceiveMemoryWarningNotification,
      object: nil
    )
  }

  deinit {
    NotificationCenter.default.removeObserver(
      self,
      name: UIApplication.didReceiveMemoryWarningNotification,
      object: nil
    )
  }

  public static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(
      name: Self.deviceSignalsChannelName,
      binaryMessenger: registrar.messenger()
    )
    let instance = FlutterPerformanceTierPlugin()
    registrar.addMethodCallDelegate(instance, channel: channel)
  }

  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    guard call.method == Self.collectDeviceSignalsMethod else {
      result(FlutterMethodNotImplemented)
      return
    }
    result(collectDeviceSignals())
  }

  private func collectDeviceSignals() -> [String: Any] {
    let processInfo = ProcessInfo.processInfo
    let totalRamBytes = Int64(min(processInfo.physicalMemory, UInt64(Int64.max)))
    let isLowRamDevice = totalRamBytes <= Self.lowRamThresholdBytes
    let majorVersion = processInfo.operatingSystemVersion.majorVersion
    let memoryPressureLevel = memoryPressureLevel(now: Date())

    return [
      "platform": "ios",
      "deviceModel": deviceModelIdentifier(),
      "totalRamBytes": totalRamBytes,
      "isLowRamDevice": isLowRamDevice,
      "sdkInt": majorVersion,
      "thermalState": thermalStateName(processInfo.thermalState),
      "thermalStateLevel": thermalStateLevel(processInfo.thermalState),
      "isLowPowerModeEnabled": processInfo.isLowPowerModeEnabled,
      "memoryPressureState": memoryPressureStateName(level: memoryPressureLevel),
      "memoryPressureLevel": memoryPressureLevel,
    ]
  }

  @objc
  private func handleMemoryWarningNotification(_ notification: Notification) {
    lastMemoryWarningAt = Date()
  }

  private func deviceModelIdentifier() -> String? {
    var systemInfo = utsname()
    uname(&systemInfo)

    let identifier = withUnsafePointer(to: &systemInfo.machine) { pointer in
      pointer.withMemoryRebound(to: CChar.self, capacity: Int(_SYS_NAMELEN)) {
        String(cString: $0)
      }
    }
    return identifier.isEmpty ? nil : identifier
  }

  private func thermalStateName(_ state: ProcessInfo.ThermalState) -> String {
    switch state {
    case .nominal:
      return "nominal"
    case .fair:
      return "fair"
    case .serious:
      return "serious"
    case .critical:
      return "critical"
    @unknown default:
      return "unknown"
    }
  }

  private func thermalStateLevel(_ state: ProcessInfo.ThermalState) -> Int {
    switch state {
    case .nominal:
      return 0
    case .fair:
      return 1
    case .serious:
      return 2
    case .critical:
      return 3
    @unknown default:
      return -1
    }
  }

  private func memoryPressureLevel(now: Date) -> Int {
    guard let lastMemoryWarningAt else {
      return 0
    }

    let elapsed = now.timeIntervalSince(lastMemoryWarningAt)
    if elapsed <= Self.criticalMemoryWarningWindow {
      return 2
    }
    if elapsed <= Self.moderateMemoryWarningWindow {
      return 1
    }
    return 0
  }

  private func memoryPressureStateName(level: Int) -> String {
    switch level {
    case 2...:
      return "critical"
    case 1:
      return "moderate"
    default:
      return "normal"
    }
  }
}
