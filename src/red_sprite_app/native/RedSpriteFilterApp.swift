import Cocoa
import WebKit

final class RedSpriteAppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    private var window: NSWindow?
    private var webView: WKWebView?
    private var backendProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            let url = try startBackend()
            showWindow(url: url)
        } catch {
            showFatalError(error)
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        backendProcess?.terminate()
    }

    func windowWillClose(_ notification: Notification) {
        backendProcess?.terminate()
    }

    private func startBackend() throws -> URL {
        guard let resourcePath = Bundle.main.resourcePath else {
            throw AppError.message("无法定位 App 资源目录")
        }

        let appResourcePath = URL(fileURLWithPath: resourcePath).appendingPathComponent("app")
        let pythonLibPath = URL(fileURLWithPath: resourcePath).appendingPathComponent("python_lib")
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.currentDirectoryURL = appResourcePath
        process.arguments = ["-m", "red_sprite_app.backend", "--port", "0"]
        var environment = ProcessInfo.processInfo.environment
        let toolPath = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        if let existingPath = environment["PATH"], !existingPath.isEmpty {
            environment["PATH"] = "\(toolPath):\(existingPath)"
        } else {
            environment["PATH"] = toolPath
        }
        if let existingPythonPath = environment["PYTHONPATH"], !existingPythonPath.isEmpty {
            environment["PYTHONPATH"] = "\(pythonLibPath.path):\(appResourcePath.path):\(existingPythonPath)"
        } else {
            environment["PYTHONPATH"] = "\(pythonLibPath.path):\(appResourcePath.path)"
        }
        process.environment = environment

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        try process.run()
        backendProcess = process

        let handle = outputPipe.fileHandleForReading
        let deadline = Date().addingTimeInterval(20)
        var buffer = Data()

        while Date() < deadline {
            let chunk = handle.availableData
            if !chunk.isEmpty {
                buffer.append(chunk)
                if let text = String(data: buffer, encoding: .utf8),
                   let line = text.split(separator: "\n").first,
                   let url = URL(string: String(line)) {
                    return url
                }
            }
            if !process.isRunning {
                let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
                let errorText = String(data: errorData, encoding: .utf8) ?? "后端进程提前退出"
                throw AppError.message(errorText)
            }
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.05))
        }

        throw AppError.message("后端启动超时")
    }

    private func showWindow(url: URL) {
        let configuration = WKWebViewConfiguration()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = true

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.load(URLRequest(url: url))
        self.webView = webView

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1320, height: 860),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "红色精灵筛选器"
        window.center()
        window.contentView = webView
        window.delegate = self
        window.makeKeyAndOrderFront(nil)
        self.window = window
    }

    private func showFatalError(_ error: Error) {
        let alert = NSAlert()
        alert.messageText = "红色精灵筛选器启动失败"
        alert.informativeText = "\(error)"
        alert.alertStyle = .critical
        alert.runModal()
        NSApplication.shared.terminate(nil)
    }
}

enum AppError: Error, CustomStringConvertible {
    case message(String)

    var description: String {
        switch self {
        case .message(let text):
            return text
        }
    }
}

let app = NSApplication.shared
let delegate = RedSpriteAppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.activate(ignoringOtherApps: true)
app.run()
