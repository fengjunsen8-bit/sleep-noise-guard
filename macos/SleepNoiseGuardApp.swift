import SwiftUI
import Foundation

struct AppSettings {
    var thresholdDb = "45"
    var durationSeconds = ""
    var noiseEvents = ""
    var feedbackRepeats = ""
    var cooldownSeconds = "60"
    var calibrationDb = "94"
    var inputDevice = ""
    var outputDevice = ""
    var soundsDir = "sounds"
    var logPath = "logs/noise_events.csv"
}

final class GuardController: ObservableObject {
    @Published var settings = AppSettings()
    @Published var isListening = false
    @Published var status = "就绪"
    @Published var currentDb = "--"
    @Published var dbfs = "--"
    @Published var triggerCount = 0
    @Published var lastSound = "暂无"
    @Published var hourlyNoise = "0"
    @Published var hourlyTriggers = "0"
    @Published var dailyNoise = "0"
    @Published var dailyTriggers = "0"
    @Published var activeLogPath = "logs/noise_events.csv"
    @Published var logLines: [String] = []

    private var process: Process?
    private var outputPipe: Pipe?
    private let projectRoot: URL

    init() {
        self.projectRoot = Self.loadProjectRoot()
    }

    func startListening() {
        guard process == nil else { return }

        let command = Process()
        command.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        command.currentDirectoryURL = projectRoot
        command.environment = ProcessInfo.processInfo.environment.merging(["PYTHONUNBUFFERED": "1"]) { _, new in new }

        var arguments = [
            "-m", "sleep_noise_guard.cli",
            "--sounds-dir", settings.soundsDir,
            "--threshold-db", settings.thresholdDb,
            "--cooldown", settings.cooldownSeconds,
            "--calibration-offset-db", settings.calibrationDb,
            "--log-path", settings.logPath
        ]

        if !settings.durationSeconds.trimmingCharacters(in: .whitespaces).isEmpty {
            arguments.append(contentsOf: ["--min-duration", settings.durationSeconds])
        }
        if !settings.noiseEvents.trimmingCharacters(in: .whitespaces).isEmpty {
            arguments.append(contentsOf: ["--noise-events", settings.noiseEvents])
        }
        if !settings.feedbackRepeats.trimmingCharacters(in: .whitespaces).isEmpty {
            arguments.append(contentsOf: ["--feedback-repeats", settings.feedbackRepeats])
        }
        if !settings.inputDevice.trimmingCharacters(in: .whitespaces).isEmpty {
            arguments.append(contentsOf: ["--input-device", settings.inputDevice])
        }
        if !settings.outputDevice.trimmingCharacters(in: .whitespaces).isEmpty {
            arguments.append(contentsOf: ["--output-device", settings.outputDevice])
        }

        command.arguments = arguments

        let pipe = Pipe()
        command.standardOutput = pipe
        command.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            DispatchQueue.main.async {
                self?.handleOutput(text)
            }
        }

        command.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async {
                self?.process = nil
                self?.outputPipe = nil
                self?.isListening = false
                if self?.status != "错误" {
                    self?.status = "已停止"
                }
            }
        }

        do {
            try command.run()
            process = command
            outputPipe = pipe
            isListening = true
            status = "监听中"
            appendLog("已启动监听：\(projectRoot.path)")
        } catch {
            status = "错误"
            appendLog("启动失败：\(error.localizedDescription)")
        }
    }

    func stopListening() {
        process?.terminate()
        status = "正在停止"
    }

    func testSound() {
        let root = URL(fileURLWithPath: settings.soundsDir, relativeTo: projectRoot).standardizedFileURL
        let files = (try? FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)) ?? []
        let audio = files
            .filter { ["wav", "mp3", "m4a", "flac", "aif", "aiff", "ogg"].contains($0.pathExtension.lowercased()) }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }

        guard let sound = audio.first else {
            appendLog("没有找到可播放的音效文件：\(root.path)")
            return
        }

        let player = Process()
        player.executableURL = URL(fileURLWithPath: "/usr/bin/afplay")
        player.arguments = [sound.path]
        do {
            try player.run()
            lastSound = sound.lastPathComponent
            appendLog("已播放：\(sound.lastPathComponent)")
        } catch {
            appendLog("播放失败：\(error.localizedDescription)")
        }
    }

    func chooseSoundsFolder() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.directoryURL = URL(fileURLWithPath: settings.soundsDir, relativeTo: projectRoot)

        if panel.runModal() == .OK, let url = panel.url {
            let path = url.path
            if path.hasPrefix(projectRoot.path) {
                settings.soundsDir = String(path.dropFirst(projectRoot.path.count + 1))
            } else {
                settings.soundsDir = path
            }
        }
    }

    private func handleOutput(_ text: String) {
        for rawLine in text.split(whereSeparator: \.isNewline) {
            let line = String(rawLine)
            appendLog(line)
            parseStatus(line)
        }
    }

    private func parseStatus(_ line: String) {
        if line.contains("estimated="), let dbRange = line.range(of: "estimated=") {
            let suffix = line[dbRange.upperBound...]
            if let value = suffix.split(separator: " ").first {
                currentDb = String(value)
            }
            if let dbfsRange = line.range(of: "dbfs=") {
                dbfs = String(line[dbfsRange.upperBound...])
            }
        }
        if line.contains("Last feedback sound:"), let sound = line.split(separator: ":").last {
            triggerCount += 1
            lastSound = sound.trimmingCharacters(in: .whitespaces)
        }
        if line.contains("Log path:"), let path = line.split(separator: ":", maxSplits: 1).last {
            activeLogPath = path.trimmingCharacters(in: .whitespaces)
        }
        if line.contains("Stats:") {
            parseStats(line)
        }
        if line.lowercased().contains("error") {
            status = "错误"
        }
    }

    private func parseStats(_ line: String) {
        for part in line.split(separator: " ") {
            let pair = part.split(separator: "=", maxSplits: 1)
            guard pair.count == 2 else { continue }
            let key = String(pair[0])
            let value = String(pair[1])
            switch key {
            case "hour_noise":
                hourlyNoise = value
            case "hour_triggers":
                hourlyTriggers = value
            case "day_noise":
                dailyNoise = value
            case "day_triggers":
                dailyTriggers = value
            default:
                break
            }
        }
    }

    private func appendLog(_ line: String) {
        logLines.append(line)
        if logLines.count > 80 {
            logLines.removeFirst(logLines.count - 80)
        }
    }

    private static func loadProjectRoot() -> URL {
        if let url = Bundle.main.url(forResource: "project_path", withExtension: "txt"),
           let text = try? String(contentsOf: url, encoding: .utf8) {
            return URL(fileURLWithPath: text.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        return URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    }
}

struct ContentView: View {
    @StateObject private var controller = GuardController()

    var body: some View {
        HStack(spacing: 18) {
            VStack(alignment: .leading, spacing: 18) {
                header
                meterPanel
                logPanel
            }
            .frame(minWidth: 540)

            settingsPanel
                .frame(width: 330)
        }
        .padding(24)
        .background(Color(red: 0.97, green: 0.98, blue: 0.99))
        .frame(minWidth: 920, minHeight: 620)
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("睡眠噪音守卫")
                    .font(.system(size: 28, weight: .bold))
                Text("本地睡眠噪音监听器")
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(controller.status)
                .font(.system(size: 14, weight: .semibold))
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(controller.isListening ? Color.green.opacity(0.14) : Color.gray.opacity(0.14))
                .clipShape(Capsule())
        }
    }

    private var meterPanel: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("当前噪音")
                .foregroundStyle(.secondary)
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                Text(controller.currentDb)
                    .font(.system(size: 70, weight: .bold, design: .rounded))
                Text("估算分贝")
                    .foregroundStyle(.secondary)
            }

            Gauge(value: Double(controller.currentDb) ?? 0, in: 0...90) {
                EmptyView()
            }
            .gaugeStyle(.linearCapacity)
            .tint((Double(controller.currentDb) ?? 0) >= (Double(controller.settings.thresholdDb) ?? 45) ? .red : .green)

            HStack(spacing: 14) {
                statBox("触发次数", "\(controller.triggerCount)")
                statBox("上次音效", controller.lastSound)
                statBox("dBFS", controller.dbfs)
            }
            HStack(spacing: 14) {
                statBox("本小时噪音", controller.hourlyNoise)
                statBox("本小时触发", controller.hourlyTriggers)
                statBox("今日噪音", controller.dailyNoise)
                statBox("今日触发", controller.dailyTriggers)
            }

            HStack(spacing: 10) {
                Button {
                    controller.startListening()
                } label: {
                    Label("开始监听", systemImage: "waveform")
                }
                .buttonStyle(.borderedProminent)
                .disabled(controller.isListening)

                Button {
                    controller.stopListening()
                } label: {
                    Label("停止", systemImage: "stop.fill")
                }
                .disabled(!controller.isListening)

                Button {
                    controller.testSound()
                } label: {
                    Label("测试音效", systemImage: "speaker.wave.2.fill")
                }
            }
        }
        .padding(22)
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var settingsPanel: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("设置")
                    .font(.system(size: 20, weight: .bold))

                field("噪音阈值 dB", text: $controller.settings.thresholdDb)
                field("出现几秒后触发", text: $controller.settings.durationSeconds)
                field("出现几次后触发", text: $controller.settings.noiseEvents)
                field("每次反馈播放次数", text: $controller.settings.feedbackRepeats)
                field("冷却时间 秒", text: $controller.settings.cooldownSeconds)
                field("校准偏移", text: $controller.settings.calibrationDb)
                field("输入设备", text: $controller.settings.inputDevice)
                field("输出设备", text: $controller.settings.outputDevice)
                field("日志路径", text: $controller.settings.logPath)

                VStack(alignment: .leading, spacing: 6) {
                    Text("音效目录")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(.secondary)
                    HStack {
                        TextField("sounds", text: $controller.settings.soundsDir)
                        Button("浏览") {
                            controller.chooseSoundsFolder()
                        }
                    }
                }

                Text("出现几秒、出现几次、播放次数留空时，监测到噪音就反馈一次。设备字段留空时，将使用系统默认的蓝牙麦克风和音箱。")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(20)
        }
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var logPanel: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("运行记录")
                .font(.system(size: 16, weight: .bold))
            ScrollView {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(Array(controller.logLines.enumerated()), id: \.offset) { _, line in
                        Text(line)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
        .padding(18)
        .background(.white)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func statBox(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 15, weight: .bold))
                .lineLimit(1)
                .truncationMode(.middle)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color(red: 0.96, green: 0.97, blue: 0.98))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func field(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(.secondary)
            TextField(title, text: text)
                .textFieldStyle(.roundedBorder)
        }
    }
}

@main
struct SleepNoiseGuardNativeApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowStyle(.titleBar)
    }
}
