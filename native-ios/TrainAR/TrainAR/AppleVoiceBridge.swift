import AVFoundation
import Combine
import Foundation
import Speech

/// Apple-only voice bridge used in iPhone-mode (no DAT SDK, no glasses).
///
/// Lifecycle:
///   * `connect()` requests mic + speech recognition permission and emits
///     a `connected` event so the web UI can show the green pill.
///   * Web sends `startListening` → we run an AVAudioEngine + SFSpeech tap
///     and emit a `voiceCommand` event with the final transcript.
///   * Web sends `speakResponse` → we synthesise the text on-device.
final class AppleVoiceBridge: NSObject, GlassesBridge, AVSpeechSynthesizerDelegate {
    @Published private(set) var isConnected: Bool = false

    private let stream: AsyncStream<GlassesBridgeEvent>
    private let continuation: AsyncStream<GlassesBridgeEvent>.Continuation

    private let audioEngine = AVAudioEngine()
    private let synthesizer = AVSpeechSynthesizer()
    private let recognizer: SFSpeechRecognizer?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var lastTranscript: String = ""

    var events: AsyncStream<GlassesBridgeEvent> { stream }

    override init() {
        var cont: AsyncStream<GlassesBridgeEvent>.Continuation!
        self.stream = AsyncStream { cont = $0 }
        self.continuation = cont
        self.recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        super.init()
        self.synthesizer.delegate = self
    }

    // MARK: - GlassesBridge

    func connect() {
        Task { @MainActor in
            let mic = await Self.requestMicrophonePermission()
            let speech = await Self.requestSpeechAuthorization()

            if mic && speech == .authorized {
                self.isConnected = true
                self.emit(type: "connected", payload: [
                    "deviceName": "iPhone Voice",
                    "battery": "100"
                ])
            } else {
                self.isConnected = false
                self.emit(type: "permissionDenied", payload: [
                    "mic": mic ? "granted" : "denied",
                    "speech": Self.describe(speech)
                ])
            }
        }
    }

    func disconnect() {
        stopListening()
        isConnected = false
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
        case "startListening":
            startListening()
        case "stopListening":
            stopListening()
        case "speakResponse":
            let text = (body?["text"] as? String) ?? ""
            speak(text: text)
        case "mockConnect":
            connect()
        case "mockDisconnect":
            disconnect()
        default:
            emit(type: "webCommandReceived", payload: ["command": type])
        }
    }

    // MARK: - Speech recognition

    private func startListening() {
        guard isConnected else {
            connect()
            return
        }
        guard let recognizer, recognizer.isAvailable else {
            emit(type: "voiceError", payload: ["message": "Speech recognizer unavailable"])
            return
        }
        if recognitionTask != nil {
            stopListening()
        }

        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            emit(type: "voiceError", payload: ["message": "audio session: \(error.localizedDescription)"])
            return
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        recognitionRequest = request
        lastTranscript = ""

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }

        recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                let transcript = result.bestTranscription.formattedString
                self.lastTranscript = transcript
                if result.isFinal {
                    self.finishTranscript(transcript)
                }
            }
            if error != nil {
                self.finishTranscript(self.lastTranscript)
            }
        }

        audioEngine.prepare()
        do {
            try audioEngine.start()
            emit(type: "listening", payload: ["state": "started"])
        } catch {
            emit(type: "voiceError", payload: ["message": "audio engine: \(error.localizedDescription)"])
            stopListening()
        }
    }

    private func stopListening() {
        if audioEngine.isRunning {
            audioEngine.stop()
        }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        emit(type: "listening", payload: ["state": "stopped"])
    }

    private func finishTranscript(_ transcript: String) {
        stopListening()
        let trimmed = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        emit(type: "voiceCommand", payload: ["transcript": trimmed])
    }

    // MARK: - TTS

    private func speak(text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        let utterance = AVSpeechUtterance(string: trimmed)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        synthesizer.speak(utterance)
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        emit(type: "spoke", payload: ["text": utterance.speechString])
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
