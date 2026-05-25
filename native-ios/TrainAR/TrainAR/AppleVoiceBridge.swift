import AVFoundation
import Combine
import Foundation
import Speech

/// Voice bridge that drives the "say 'coach', ask a question, hear an answer" loop.
///
/// Single-recognizer architecture (modeled after VisionClaw's WakeWordDetector):
/// one `SFSpeechRecognizer` running with on-device recognition. In the wake-word
/// phase it watches the live transcript for "coach". Once detected the task is
/// torn down, a short audible cue plays, and a fresh recognition task captures
/// the user's actual utterance until silence.
///
///   listening for wake word ──► "coach" appears in transcript
///        ▲                          │
///        │                          ▼
///        │                  short audible cue ("yes?")
///        │                          │
///        │                          ▼
///        │                  SFSpeechRecognizer captures utterance
///        │                          │
///        │                          ▼ ~0.8s silence
///        │                  POST /api/chat
///        │                          │
///        │                          ▼
///        │                  AVSpeechSynthesizer speaks reply
///        │                          │
///        └──── speechSynthesizer didFinish ──┘
///
/// Audio I/O routes through whatever Bluetooth audio device is currently
/// active (Ray-Ban Display, AirPods, etc.) via the AVAudioSession config —
/// no glasses-specific SDK is involved.
final class AppleVoiceBridge: NSObject, GlassesBridge, AVSpeechSynthesizerDelegate {
    @Published private(set) var isConnected: Bool = false

    private let stream: AsyncStream<GlassesBridgeEvent>
    private let continuation: AsyncStream<GlassesBridgeEvent>.Continuation

    private let audioEngine = AVAudioEngine()
    private let synthesizer = AVSpeechSynthesizer()
    private let recognizer: SFSpeechRecognizer?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?

    // Utterance-capture bookkeeping
    private var lastTranscript: String = ""
    private var lastTranscriptUpdate: Date?
    private var silenceWatchdog: Task<Void, Never>?

    /// Whole-word, case-insensitive regex for the wake word. `\b` boundaries
    /// stop us matching inside "approach", "coaching", "encroach", etc.
    private static let wakeWordRegex: NSRegularExpression = {
        // swiftlint:disable:next force_try
        try! NSRegularExpression(pattern: "\\bcoach\\b", options: [.caseInsensitive])
    }()

    private let chatEndpoint: URL

    private enum Mode {
        case idle
        case listeningForWakeWord
        case acknowledgingWakeWord   // playing the "yes?" cue
        case capturingUtterance
        case awaitingReply
        case speakingReply
    }
    private var mode: Mode = .idle

    private let utteranceTimeoutSeconds: TimeInterval = 15.0
    private let utteranceSilenceSeconds: TimeInterval = 0.8

    var events: AsyncStream<GlassesBridgeEvent> { stream }

    override init() {
        var cont: AsyncStream<GlassesBridgeEvent>.Continuation!
        self.stream = AsyncStream { cont = $0 }
        self.continuation = cont
        self.recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))

        let endpointString = (Bundle.main.infoDictionary?["ChatEndpointURL"] as? String)
            ?? "http://127.0.0.1:5002/api/chat"
        self.chatEndpoint = URL(string: endpointString) ?? URL(string: "http://127.0.0.1:5002/api/chat")!

        super.init()
        self.synthesizer.delegate = self
    }

    // MARK: - GlassesBridge

    func connect() {
        Task { @MainActor in
            let mic = await Self.requestMicrophonePermission()
            let speech = await Self.requestSpeechAuthorization()

            guard mic && speech == .authorized else {
                self.isConnected = false
                self.emit(type: "permissionDenied", payload: [
                    "mic": mic ? "granted" : "denied",
                    "speech": Self.describe(speech)
                ])
                return
            }

            do {
                try self.configureAudioSession()
            } catch {
                self.emit(type: "voiceError", payload: ["message": "audio session: \(error.localizedDescription)"])
                return
            }

            self.isConnected = true
            self.emit(type: "connected", payload: [
                "deviceName": "iPhone Voice",
                "battery": "100"
            ])

            self.startWakeWordDetection()
        }
    }

    func disconnect() {
        stopRecognition()
        isConnected = false
        mode = .idle
        emit(type: "disconnected", payload: ["deviceName": "iPhone Voice"])
    }

    func replayState() {
        if isConnected {
            emit(type: "connected", payload: ["deviceName": "iPhone Voice", "battery": "100"])
        } else {
            emit(type: "disconnected", payload: ["deviceName": "iPhone Voice"])
        }
    }

    func handleWebCommand(type: String, payload: Any?) {
        let body = payload as? [String: Any]
        switch type {
        case "speakResponse":
            let text = (body?["text"] as? String) ?? ""
            // Pause wake-word recognition so we don't trigger on the reply text.
            stopRecognition()
            mode = .speakingReply
            speak(text: text)
        case "startListening":
            // Manual override — pretend the wake word just fired.
            handleWakeWordDetected()
        case "stopListening":
            stopRecognition()
            startWakeWordDetection()
        case "mockConnect":
            connect()
        case "mockDisconnect":
            disconnect()
        default:
            emit(type: "webCommandReceived", payload: ["command": type])
        }
    }

    // MARK: - Audio session

    /// Configures the shared audio session so mic + TTS route through Bluetooth
    /// when a BT audio device (Ray-Ban Display glasses, AirPods, etc.) is paired.
    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(
            .playAndRecord,
            mode: .voiceChat,
            options: [.allowBluetooth, .allowBluetoothA2DP, .duckOthers, .defaultToSpeaker]
        )
        try session.setActive(true, options: .notifyOthersOnDeactivation)
        logRouteSnapshot(reason: "post-activate")
    }

    /// Emits a one-line summary of what iOS thinks the active audio route is,
    /// plus the list of currently available BT inputs. Useful for figuring out
    /// whether paired glasses are actually visible to AVAudioSession.
    private func logRouteSnapshot(reason: String) {
        let session = AVAudioSession.sharedInstance()
        let route = session.currentRoute
        let inputs = route.inputs.map { "\($0.portName)[\($0.portType.rawValue)]" }.joined(separator: ",")
        let outputs = route.outputs.map { "\($0.portName)[\($0.portType.rawValue)]" }.joined(separator: ",")
        let available = (session.availableInputs ?? [])
            .map { "\($0.portName)[\($0.portType.rawValue)]" }
            .joined(separator: ",")
        let summary = "route(\(reason)) inputs=\(inputs) outputs=\(outputs) availableInputs=\(available)"
        NSLog("[AppleVoiceBridge] %@", summary)
        emit(type: "routeSnapshot", payload: ["summary": summary])
    }

    // MARK: - Recognition (shared wake-word + utterance plumbing)

    /// Starts a recognition task whose only job is to scan for "coach" in the
    /// live transcript. On detection it transitions into the utterance-capture
    /// phase.
    private func startWakeWordDetection() {
        guard isConnected else { return }
        guard let recognizer, recognizer.isAvailable else {
            emit(type: "voiceError", payload: ["message": "Speech recognizer unavailable"])
            return
        }

        if !recognizer.supportsOnDeviceRecognition {
            // Cloud STT caps at ~1 minute per session; without on-device support
            // we cannot run "always-listening" reliably. Fail loudly rather than
            // silently churn through 1-minute restarts.
            emit(type: "voiceError", payload: [
                "message": "Device does not support on-device speech recognition (needs A12+ / iOS 13+)."
            ])
            return
        }

        stopRecognition()

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        request.requiresOnDeviceRecognition = true
        recognitionRequest = request

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            guard buffer.frameLength > 0 else { return }
            self?.recognitionRequest?.append(buffer)
        }

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                let transcript = result.bestTranscription.formattedString
                if Self.containsWakeWord(transcript) {
                    Task { @MainActor in self.handleWakeWordDetected() }
                }
            }
            if error != nil {
                // Restart on error so we don't silently stop listening.
                Task { @MainActor in
                    if self.mode == .listeningForWakeWord {
                        self.stopRecognition()
                        self.startWakeWordDetection()
                    }
                }
            }
        }

        audioEngine.prepare()
        do {
            try audioEngine.start()
            mode = .listeningForWakeWord
            emit(type: "wakeWordReady", payload: ["keyword": "coach"])
        } catch {
            emit(type: "voiceError", payload: ["message": "audio engine: \(error.localizedDescription)"])
        }
    }

    private static func containsWakeWord(_ transcript: String) -> Bool {
        let range = NSRange(transcript.startIndex..<transcript.endIndex, in: transcript)
        return wakeWordRegex.firstMatch(in: transcript, options: [], range: range) != nil
    }

    /// Called when "coach" appears in the wake-word transcript. Stops the
    /// wake-word recognizer, plays an audible cue; utterance capture starts
    /// from the synthesizer's `didFinish` delegate.
    private func handleWakeWordDetected() {
        guard mode == .listeningForWakeWord else { return }
        mode = .acknowledgingWakeWord
        emit(type: "wakeWordDetected", payload: ["keyword": "coach"])
        stopRecognition()
        speak(text: "What up, champ?")
    }

    /// Starts a fresh recognition task to capture the user's actual question.
    /// Same audio engine + tap pattern; different result handler — this one
    /// finalizes on silence and POSTs the transcript.
    private func startUtteranceCapture() {
        guard let recognizer, recognizer.isAvailable else {
            emit(type: "voiceError", payload: ["message": "Speech recognizer unavailable"])
            startWakeWordDetection()
            return
        }
        stopRecognition()

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        // Cloud STT is fine here — utterance is bounded to a few seconds.
        recognitionRequest = request
        lastTranscript = ""
        lastTranscriptUpdate = Date()

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            guard buffer.frameLength > 0 else { return }
            self?.recognitionRequest?.append(buffer)
        }

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                let transcript = result.bestTranscription.formattedString
                if transcript != self.lastTranscript {
                    self.lastTranscript = transcript
                    self.lastTranscriptUpdate = Date()
                }
                if result.isFinal {
                    Task { @MainActor in self.finishUtteranceCapture(transcript: transcript) }
                }
            }
            if error != nil {
                Task { @MainActor in self.finishUtteranceCapture(transcript: self.lastTranscript) }
            }
        }

        audioEngine.prepare()
        do {
            try audioEngine.start()
            mode = .capturingUtterance
            emit(type: "listening", payload: ["state": "started"])
        } catch {
            emit(type: "voiceError", payload: ["message": "audio engine: \(error.localizedDescription)"])
            startWakeWordDetection()
            return
        }

        // Silence watchdog: polls the last-transcript timestamp; finalizes after
        // ~utteranceSilenceSeconds with no new tokens, or after a hard timeout.
        silenceWatchdog?.cancel()
        let started = Date()
        silenceWatchdog = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 200_000_000)
                guard let self else { return }
                if self.mode != .capturingUtterance { return }
                let elapsed = Date().timeIntervalSince(started)
                let sinceUpdate = Date().timeIntervalSince(self.lastTranscriptUpdate ?? started)
                if elapsed > self.utteranceTimeoutSeconds {
                    await MainActor.run {
                        self.finishUtteranceCapture(transcript: self.lastTranscript)
                    }
                    return
                }
                if !self.lastTranscript.isEmpty && sinceUpdate > self.utteranceSilenceSeconds {
                    await MainActor.run {
                        self.finishUtteranceCapture(transcript: self.lastTranscript)
                    }
                    return
                }
            }
        }
    }

    /// Tears down whatever recognition task is currently running (wake-word OR
    /// utterance) and stops the audio engine. Safe to call repeatedly.
    private func stopRecognition() {
        silenceWatchdog?.cancel()
        silenceWatchdog = nil
        if audioEngine.isRunning {
            audioEngine.stop()
        }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
    }

    /// Called once the captured utterance is finalized. Fires the chat call.
    private func finishUtteranceCapture(transcript: String) {
        guard mode == .capturingUtterance else { return }
        stopRecognition()
        let trimmed = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        emit(type: "listening", payload: ["state": "stopped"])
        emit(type: "voiceCommand", payload: ["transcript": trimmed])

        guard !trimmed.isEmpty else {
            startWakeWordDetection()
            return
        }

        mode = .awaitingReply
        Task { [weak self] in
            guard let self else { return }
            do {
                let reply = try await self.postChat(text: trimmed)
                await MainActor.run { self.speak(text: reply) }
            } catch {
                await MainActor.run {
                    self.emit(type: "chatError", payload: ["message": error.localizedDescription])
                    self.speak(text: "Sorry, I had trouble reaching the coach.")
                }
            }
        }
    }

    // MARK: - Chat API

    private struct ChatRequest: Encodable { let text: String }
    private struct ChatResponse: Decodable {
        let reply: String?
        let error: String?
    }

    private func postChat(text: String) async throws -> String {
        var request = URLRequest(url: chatEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONEncoder().encode(ChatRequest(text: text))
        request.timeoutInterval = 20

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        let decoded = (try? JSONDecoder().decode(ChatResponse.self, from: data))
        guard (200..<300).contains(http.statusCode) else {
            let detail = decoded?.error ?? "HTTP \(http.statusCode)"
            throw NSError(domain: "ChatAPI", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: detail])
        }
        let reply = (decoded?.reply ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !reply.isEmpty else {
            throw NSError(domain: "ChatAPI", code: 0, userInfo: [NSLocalizedDescriptionKey: "empty reply"])
        }
        return reply
    }

    // MARK: - TTS

    private func speak(text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        if mode == .awaitingReply {
            mode = .speakingReply
        }
        let utterance = AVSpeechUtterance(string: trimmed)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        synthesizer.speak(utterance)
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        emit(type: "spoke", payload: ["text": utterance.speechString])
        Task { @MainActor in
            switch mode {
            case .acknowledgingWakeWord:
                startUtteranceCapture()
            case .speakingReply:
                startWakeWordDetection()
            default:
                // Manual speakResponse from the web layer — return to wake-word mode if connected.
                if isConnected { startWakeWordDetection() }
            }
        }
    }

    // MARK: - Helpers

    private func emit(type: String, payload: [String: String]) {
        continuation.yield(GlassesBridgeEvent(type: type, payload: payload))
    }

    private static func requestMicrophonePermission() async -> Bool {
        await withCheckedContinuation { cont in
            if #available(iOS 17.0, *) {
                AVAudioApplication.requestRecordPermission { granted in
                    cont.resume(returning: granted)
                }
            } else {
                AVAudioSession.sharedInstance().requestRecordPermission { granted in
                    cont.resume(returning: granted)
                }
            }
        }
    }

    private static func requestSpeechAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
        await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { status in
                cont.resume(returning: status)
            }
        }
    }

    private static func describe(_ status: SFSpeechRecognizerAuthorizationStatus) -> String {
        switch status {
        case .authorized: return "authorized"
        case .denied: return "denied"
        case .notDetermined: return "notDetermined"
        case .restricted: return "restricted"
        @unknown default: return "unknown"
        }
    }
}
