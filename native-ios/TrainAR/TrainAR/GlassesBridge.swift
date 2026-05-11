import Foundation

struct GlassesBridgeEvent: Codable {
    let type: String
    let payload: [String: String]

    var jsonString: String? {
        guard let data = try? JSONEncoder().encode(self) else { return nil }
        return String(data: data, encoding: .utf8)
    }
}

protocol GlassesBridge: ObservableObject {
    var isConnected: Bool { get }
    var events: AsyncStream<GlassesBridgeEvent> { get }

    func connect()
    func disconnect()
    func replayState()
    func handleWebCommand(type: String, payload: Any?)
}

final class MockGlassesBridge: GlassesBridge {
    @Published private(set) var isConnected = false

    private let stream: AsyncStream<GlassesBridgeEvent>
    private let continuation: AsyncStream<GlassesBridgeEvent>.Continuation

    var events: AsyncStream<GlassesBridgeEvent> {
        stream
    }

    init() {
        var continuation: AsyncStream<GlassesBridgeEvent>.Continuation!
        self.stream = AsyncStream { streamContinuation in
            continuation = streamContinuation
        }
        self.continuation = continuation
    }

    func connect() {
        isConnected = true
        send(type: "connected", payload: [
            "deviceName": "Mock Ray-Ban Meta",
            "battery": "78"
        ])
    }

    func disconnect() {
        isConnected = false
        send(type: "disconnected", payload: [
            "deviceName": "Mock Ray-Ban Meta"
        ])
    }

    func replayState() {
        if isConnected {
            connect()
        } else {
            disconnect()
        }
    }

    func handleWebCommand(type: String, payload: Any?) {
        if type == "mockConnect" {
            connect()
            return
        }

        if type == "mockDisconnect" {
            disconnect()
            return
        }

        if type == "mockVoiceCommand" {
            let body = payload as? [String: Any]
            let transcript = body?["transcript"] as? String
            simulateVoiceCommand(transcript?.isEmpty == false ? transcript! : "Start my workout")
            return
        }

        if type == "mockPhotoCapture" {
            simulatePhotoCapture()
            return
        }

        send(type: "webCommandReceived", payload: [
            "command": type
        ])
    }

    func simulateVoiceCommand(_ transcript: String) {
        send(type: "voiceCommand", payload: [
            "transcript": transcript
        ])
    }

    func simulatePhotoCapture() {
        send(type: "photoCaptured", payload: [
            "source": "mock",
            "contentType": "image/jpeg"
        ])
    }

    private func send(type: String, payload: [String: String]) {
        continuation.yield(GlassesBridgeEvent(type: type, payload: payload))
    }
}
