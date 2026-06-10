import AVFoundation
import Combine
import CoreImage
import Foundation
import UIKit

#if canImport(MWDATCore)
import MWDATCore
import MWDATCamera
#endif

/// Glasses video bridge.
///
/// Goal: render the Ray-Ban Meta POV camera *behind* the transparent HUD
/// WebView, exactly where the phone-camera `AVCaptureVideoPreviewLayer` sits
/// today — so the existing `screens-hud.jsx` overlay (and its coach-driven
/// updates) composite on top of the real glasses feed.
///
/// The Meta Wearables Device Access Toolkit (iOS, `MWDATCore` + `MWDATCamera`)
/// streams the POV camera to the *phone app* over Bluetooth (≤720p/30fps) and
/// delivers each frame as a wrapper whose `makeUIImage()` returns a `UIImage`.
/// So the frame contract here is `(UIImage) -> Void`, and the preview is a
/// plain `UIImageView`.
///
/// The real SDK isn't wired (it needs the SPM package + a Meta dev account).
/// `MockCameraFrameSource` stands in with the phone camera so the whole
/// frame -> preview -> HUD path runs and is verifiable today. Swap in
/// `MetaGlassesFrameSource` once the package is added — same protocol.

// MARK: - Frame source abstraction

/// Produces a live stream of `UIImage` frames to show behind the HUD — matches
/// the Meta DAT `frame.makeUIImage()` contract. Phone-camera mock now, the DAT
/// video stream later.
protocol GlassesFrameSource: AnyObject {
    func start(onFrame: @escaping (UIImage) -> Void)
    func stop()
}

// MARK: - Preview view (renders UIImage frames behind the transparent HUD)

/// A `UIView` that shows the latest POV frame. Insert it at sublayer index 0 of
/// the HUD container (where `cameraPreviewLayer` goes today) and call
/// `display(_:)` on the main thread per frame.
final class GlassesVideoPreviewView: UIView {
    private let imageView = UIImageView()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .black
        imageView.contentMode = .scaleAspectFill   // fill like AR lens edge-to-edge
        imageView.frame = bounds
        imageView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        addSubview(imageView)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func display(_ image: UIImage) {
        imageView.image = image
    }
}

// MARK: - Mock frame source (phone camera stands in for the glasses)

/// Feeds the phone's back camera through `AVCaptureVideoDataOutput`, converting
/// each sample buffer to a `UIImage` so it matches the SDK's frame contract — a
/// real, compilable stand-in so the HUD-over-live-video loop runs without the
/// SDK or hardware.
final class MockCameraFrameSource: NSObject, GlassesFrameSource, AVCaptureVideoDataOutputSampleBufferDelegate {
    private let session = AVCaptureSession()
    private let output = AVCaptureVideoDataOutput()
    private let queue = DispatchQueue(label: "com.trainar.glasses.mock-camera")
    private let ciContext = CIContext(options: nil)
    private var onFrame: ((UIImage) -> Void)?

    func start(onFrame: @escaping (UIImage) -> Void) {
        self.onFrame = onFrame
        queue.async { [weak self] in
            guard let self else { return }
            self.configureIfNeeded()
            if !self.session.isRunning { self.session.startRunning() }
        }
    }

    func stop() {
        onFrame = nil
        queue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }

    private func configureIfNeeded() {
        guard session.inputs.isEmpty else { return }
        session.beginConfiguration()
        session.sessionPreset = .hd1280x720   // mirrors the SDK's 720p ceiling
        if let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
           let input = try? AVCaptureDeviceInput(device: device),
           session.canAddInput(input) {
            session.addInput(input)
        }
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: queue)
        if session.canAddOutput(output) { session.addOutput(output) }
        session.commitConfiguration()
    }

    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        guard let onFrame,
              let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        guard let cgImage = ciContext.createCGImage(ciImage, from: ciImage.extent) else { return }
        onFrame(UIImage(cgImage: cgImage))
    }
}

// MARK: - Real Meta DAT frame source (SDK seam)

/// Real Meta Wearables Device Access Toolkit video stream. The body compiles
/// only when the DAT package is linked (`#if canImport`), so the project still
/// builds without it. Add the package in Xcode
/// (https://github.com/facebook/meta-wearables-dat-ios) + fill the MWDAT
/// Info.plist keys, and `beginGlassesStream` picks this up automatically.
#if canImport(MWDATCamera)
final class MetaGlassesFrameSource: NSObject, GlassesFrameSource {
    private var onFrame: ((UIImage) -> Void)?
    private var session: DeviceSession?
    private var frameToken: Any?
    private var stateTask: Task<Void, Never>?

    func start(onFrame: @escaping (UIImage) -> Void) {
        self.onFrame = onFrame
        stateTask = Task { [weak self] in
            guard let self else { return }
            do {
                // 1. Ensure registered — only open the Meta AI prompt if we are
                //    NOT already registered (otherwise every tap re-prompts).
                var didRequestRegistration = false
                registrationLoop: for await state in Wearables.shared.registrationStateStream() {
                    if state == .registered { break registrationLoop }
                    if !didRequestRegistration {
                        didRequestRegistration = true
                        try? await Wearables.shared.startRegistration()
                    }
                }
                // 2. Ensure camera permission. Check first (best-effort — a
                //    throwing status check must NOT abort before we get to show the
                //    consent popup), then request it only if not already granted so
                //    we don't re-prompt every tap.
                let current = try? await Wearables.shared.checkPermissionStatus(.camera)
                NSLog("[MetaGlassesFrameSource] camera permission status: \(String(describing: current))")
                if current != .granted {
                    let requested = try await Wearables.shared.requestPermission(.camera)
                    guard requested == .granted else {
                        NSLog("[MetaGlassesFrameSource] camera permission not granted: \(String(describing: requested))")
                        return
                    }
                }
                // 3. devicesStream() yields device IDENTIFIERS (strings). Take the
                //    first one and open a session for it specifically — selecting
                //    the explicit device works where AutoDeviceSelector returned
                //    "No eligible device available".
                NSLog("[MetaGlassesFrameSource] waiting for a device…")
                deviceLoop: for await devices in Wearables.shared.devicesStream() {
                    guard let identifier = devices.first else {
                        NSLog("[MetaGlassesFrameSource] no devices yet…")
                        continue deviceLoop
                    }
                    NSLog("[MetaGlassesFrameSource] device \(identifier) — opening session")
                    let selector = SpecificDeviceSelector(device: identifier)
                    let session = try await Wearables.shared.createSession(deviceSelector: selector)
                    self.session = session
                    try await session.start()
                    for await sessionState in session.stateStream()
                    where sessionState == .started {
                        self.beginStream(on: session)
                        break
                    }
                    break deviceLoop
                }
            } catch {
                NSLog("[MetaGlassesFrameSource] start failed: \(error.localizedDescription)")
            }
        }
    }

    private func beginStream(on session: DeviceSession) {
        do {
            let config = StreamConfiguration(videoCodec: .raw, resolution: .high, frameRate: 30)
            guard let stream = try session.addStream(config: config) else { return }
            frameToken = stream.videoFramePublisher.listen { [weak self] frame in
                guard let image = frame.makeUIImage() else { return }
                self?.onFrame?(image)
            }
            Task { await stream.start() }
        } catch {
            NSLog("[MetaGlassesFrameSource] add/start stream failed: \(error.localizedDescription)")
        }
    }

    func stop() {
        stateTask?.cancel()
        stateTask = nil
        frameToken = nil
        try? session?.stop()
        session = nil
        onFrame = nil
    }
}
#else
/// Stub used until the DAT package is linked, so `MetaGlassesFrameSource` always
/// exists and the project compiles. Produces no frames.
final class MetaGlassesFrameSource: NSObject, GlassesFrameSource {
    private var onFrame: ((UIImage) -> Void)?
    func start(onFrame: @escaping (UIImage) -> Void) {
        self.onFrame = onFrame
        NSLog("[MetaGlassesFrameSource] Meta DAT SDK not linked — add the meta-wearables-dat-ios package to stream from the glasses.")
    }
    func stop() { onFrame = nil }
}
#endif

// MARK: - Bridge

/// `GlassesBridge` that streams the (mock for now) POV feed into a preview view
/// for compositing under the HUD. Voice stays on `AppleVoiceBridge`; this owns
/// video only — see the wiring notes for combining them.
final class MetaWearablesBridge: NSObject, GlassesBridge {
    @Published private(set) var isConnected = false

    /// Insert this behind the transparent HUD WebView (sublayer index 0 of the
    /// HUD container), in place of the phone `AVCaptureVideoPreviewLayer`.
    let previewView = GlassesVideoPreviewView()

    private let frameSource: GlassesFrameSource
    private let deviceName: String

    private let stream: AsyncStream<GlassesBridgeEvent>
    private let continuation: AsyncStream<GlassesBridgeEvent>.Continuation
    var events: AsyncStream<GlassesBridgeEvent> { stream }

    /// Defaults to the phone-camera mock. Pass `MetaGlassesFrameSource()` once
    /// the SDK is integrated.
    init(frameSource: GlassesFrameSource = MockCameraFrameSource(), deviceName: String = "Ray-Ban Meta (stream)") {
        self.frameSource = frameSource
        self.deviceName = deviceName
        var cont: AsyncStream<GlassesBridgeEvent>.Continuation!
        self.stream = AsyncStream { cont = $0 }
        self.continuation = cont
        super.init()
    }

    func connect() {
        frameSource.start { [weak self] image in
            DispatchQueue.main.async { self?.previewView.display(image) }
        }
        isConnected = true
        emit(type: "connected", payload: ["deviceName": deviceName, "battery": "78"])
    }

    func disconnect() {
        frameSource.stop()
        isConnected = false
        emit(type: "disconnected", payload: ["deviceName": deviceName])
    }

    func replayState() {
        emit(type: isConnected ? "connected" : "disconnected", payload: ["deviceName": deviceName])
    }

    func handleWebCommand(type: String, payload: Any?) {
        switch type {
        case "mockConnect", "startGlassesCamera":
            connect()
        case "mockDisconnect", "stopGlassesCamera":
            disconnect()
        default:
            emit(type: "webCommandReceived", payload: ["command": type])
        }
    }

    func configure() {
        // TODO (Meta DAT): one-time SDK configuration on app launch. Safe no-op
        // until the SDK is added.
    }

    private func emit(type: String, payload: [String: String]) {
        continuation.yield(GlassesBridgeEvent(type: type, payload: payload))
    }
}
