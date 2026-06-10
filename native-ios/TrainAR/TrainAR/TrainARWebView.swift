import SwiftUI
import WebKit
import AVFoundation

struct TrainARWebView<B: GlassesBridge>: UIViewRepresentable {
    @ObservedObject var bridge: B

    func makeCoordinator() -> Coordinator<B> {
        Coordinator(bridge: bridge)
    }

    func makeUIView(context: Context) -> UIView {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController.add(context.coordinator, name: "trainarNative")
        configuration.userContentController.addUserScript(Self.bootstrapScript)

        let containerView = UIView()
        containerView.backgroundColor = .black
        context.coordinator.attachCameraPreview(to: containerView)

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.allowsBackForwardNavigationGestures = false
        webView.scrollView.delegate = context.coordinator
        webView.scrollView.bounces = false
        webView.scrollView.alwaysBounceVertical = false
        webView.scrollView.alwaysBounceHorizontal = false
        webView.scrollView.showsVerticalScrollIndicator = false
        webView.scrollView.showsHorizontalScrollIndicator = false
        webView.scrollView.minimumZoomScale = 1
        webView.scrollView.maximumZoomScale = 1
        webView.scrollView.backgroundColor = .clear
        webView.translatesAutoresizingMaskIntoConstraints = false
        containerView.addSubview(webView)
        NSLayoutConstraint.activate([
            webView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            webView.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            webView.topAnchor.constraint(equalTo: containerView.topAnchor),
            webView.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
        ])
        context.coordinator.attach(webView)

        webView.load(URLRequest(url: Self.webURL))
        return containerView
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        if let webView = uiView.subviews.compactMap({ $0 as? WKWebView }).first {
            context.coordinator.attach(webView)
        }
        context.coordinator.attachCameraPreview(to: uiView)
    }
}

extension TrainARWebView {
    static var webURL: URL {
        let configured = Bundle.main.object(forInfoDictionaryKey: "TRAINAR_WEB_URL") as? String
        let raw = configured?.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: raw?.isEmpty == false ? raw! : "http://127.0.0.1:5002/ios/")!
    }

    static var bootstrapScript: WKUserScript {
        WKUserScript(
            source: """
            window.TRAINAR_NATIVE_APP = true;
            document.documentElement.classList.add('trainar-native');
            window.TrainARNative = {
              postMessage: function(type, payload) {
                if (!window.webkit || !window.webkit.messageHandlers || !window.webkit.messageHandlers.trainarNative) {
                  return;
                }
                window.webkit.messageHandlers.trainarNative.postMessage({ type: type, payload: payload || {} });
              }
            };
            window.sendTrainARNativeCommand = function(type, payload) {
              window.TrainARNative.postMessage(type, payload);
              return true;
            };
            // Forward in-page trainar:speak events to the native bridge so the
            // coach response gets spoken via AVSpeechSynthesizer.
            window.addEventListener('trainar:speak', function(event) {
              var detail = event.detail || {};
              var text = detail.text || '';
              if (!text) return;
              window.TrainARNative.postMessage('speakResponse', {
                text: text,
                continueListening: Boolean(detail.continueListening)
              });
            });
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
    }
}

final class Coordinator<B: GlassesBridge>: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, UIScrollViewDelegate {
    private let bridge: B
    private weak var webView: WKWebView?
    private weak var cameraContainerView: UIView?
    private var eventTask: Task<Void, Never>?
    private let cameraSession = AVCaptureSession()
    private let cameraSessionQueue = DispatchQueue(label: "com.trainar.hud.camera")
    private var cameraPreviewLayer: AVCaptureVideoPreviewLayer?
    private var cameraPosition: AVCaptureDevice.Position = .back
    private var cameraConfigured = false

    // Glasses POV stream (mock now, Meta DAT later). With useGlassesStream on,
    // the HUD's startHudCamera renders the glasses pipeline (UIImage frames ->
    // GlassesVideoPreviewView) behind the HUD instead of the phone AVCapture
    // preview. Flip the source to MetaGlassesFrameSource once the SDK is added.
    private let useGlassesStream = true
    private let glassesPreviewView = GlassesVideoPreviewView()
    private var glassesFrameSource: GlassesFrameSource?
    private var glassesAttached = false

    init(bridge: B) {
        self.bridge = bridge
        super.init()
        startForwardingEvents()
    }

    func attach(_ webView: WKWebView) {
        self.webView = webView
    }

    func attachCameraPreview(to containerView: UIView) {
        cameraContainerView = containerView
        if cameraPreviewLayer == nil {
            let previewLayer = AVCaptureVideoPreviewLayer(session: cameraSession)
            previewLayer.videoGravity = .resizeAspectFill
            previewLayer.isHidden = true
            containerView.layer.insertSublayer(previewLayer, at: 0)
            cameraPreviewLayer = previewLayer
        }
        cameraPreviewLayer?.frame = containerView.bounds

        // Glasses preview sits just above the phone-camera layer and just below
        // the transparent HUD WebView.
        if !glassesAttached {
            glassesPreviewView.isHidden = true
            glassesPreviewView.frame = containerView.bounds
            glassesPreviewView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            containerView.insertSubview(glassesPreviewView, at: 0)
            glassesAttached = true
        }
        glassesPreviewView.frame = containerView.bounds
    }

    private func updatePreviewLayerFrame() {
        guard let cameraContainerView, let cameraPreviewLayer else { return }
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        cameraPreviewLayer.frame = cameraContainerView.bounds
        if let connection = cameraPreviewLayer.connection, connection.isVideoOrientationSupported {
            connection.videoOrientation = currentVideoOrientation()
        }
        CATransaction.commit()
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "trainarNative" else { return }
        guard let body = message.body as? [String: Any],
              let type = body["type"] as? String else {
            return
        }

        if type == "startHudCamera" || type == "startGlassesCamera" {
            if useGlassesStream || type == "startGlassesCamera" {
                startGlassesCamera()
            } else {
                let payload = body["payload"] as? [String: Any]
                let facingMode = payload?["facingMode"] as? String
                startHudCamera(facingMode: facingMode)
            }
            return
        }

        if type == "stopHudCamera" || type == "stopGlassesCamera" {
            if useGlassesStream || type == "stopGlassesCamera" {
                stopGlassesCamera()
            } else {
                stopHudCamera()
            }
            return
        }

        if type == "switchHudCamera" {
            switchHudCamera()
            return
        }

        if type == "hudScreenActive" {
            updatePreviewLayerFrame()
            return
        }

        bridge.handleWebCommand(type: type, payload: body["payload"])
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        bridge.replayState()
    }

    @available(iOS 15.0, *)
    func webView(
        _ webView: WKWebView,
        requestMediaCapturePermissionFor origin: WKSecurityOrigin,
        initiatedByFrame frame: WKFrameInfo,
        type: WKMediaCaptureType,
        decisionHandler: @escaping (WKPermissionDecision) -> Void
    ) {
        guard type == .camera || type == .cameraAndMicrophone else {
            decisionHandler(.deny)
            return
        }

        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            decisionHandler(.grant)
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    decisionHandler(granted ? .grant : .deny)
                }
            }
        case .denied, .restricted:
            decisionHandler(.deny)
        @unknown default:
            decisionHandler(.prompt)
        }
    }

    func viewForZooming(in scrollView: UIScrollView) -> UIView? {
        nil
    }

    func scrollViewDidLayoutSubviews(_ scrollView: UIScrollView) {
        updatePreviewLayerFrame()
    }

    private func startHudCamera(facingMode: String?) {
        cameraPosition = facingMode == "user" ? .front : .back

        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            startConfiguredCamera()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.startConfiguredCamera()
                    } else {
                        self?.emitHudCameraEvent(status: "denied", message: "Camera permission was denied.")
                    }
                }
            }
        case .denied, .restricted:
            emitHudCameraEvent(status: "denied", message: "Camera permission is disabled for TrainAR.")
        @unknown default:
            emitHudCameraEvent(status: "failed", message: "Camera permission status is unknown.")
        }
    }

    private func startConfiguredCamera() {
        cameraSessionQueue.async { [weak self] in
            guard let self else { return }
            do {
                try self.configureCameraSession(position: self.cameraPosition)
                if !self.cameraSession.isRunning {
                    self.cameraSession.startRunning()
                }
                DispatchQueue.main.async {
                    self.cameraPreviewLayer?.isHidden = false
                    self.updatePreviewLayerFrame()
                    self.emitHudCameraEvent(status: "streaming", message: nil)
                }
            } catch {
                DispatchQueue.main.async {
                    self.emitHudCameraEvent(status: "failed", message: error.localizedDescription)
                }
            }
        }
    }

    private func stopHudCamera() {
        cameraSessionQueue.async { [weak self] in
            guard let self else { return }
            if self.cameraSession.isRunning {
                self.cameraSession.stopRunning()
            }
            DispatchQueue.main.async {
                self.cameraPreviewLayer?.isHidden = true
                self.emitHudCameraEvent(status: "stopped", message: nil)
            }
        }
    }

    private func switchHudCamera() {
        cameraPosition = cameraPosition == .back ? .front : .back
        startConfiguredCamera()
    }

    // MARK: - Glasses POV stream

    private func startGlassesCamera() {
        // The mock source uses the phone camera, so it needs camera permission.
        // The real Meta DAT source will request its own wearable permission.
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            beginGlassesStream()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.beginGlassesStream()
                    } else {
                        self?.emitHudCameraEvent(status: "denied", message: "Camera permission was denied.")
                    }
                }
            }
        case .denied, .restricted:
            emitHudCameraEvent(status: "denied", message: "Camera permission is disabled for TrainAR.")
        @unknown default:
            emitHudCameraEvent(status: "failed", message: "Camera permission status is unknown.")
        }
    }

    private func beginGlassesStream() {
        cameraPreviewLayer?.isHidden = true   // don't contend with the AVCapture preview
        let source: GlassesFrameSource
        if let existing = glassesFrameSource {
            source = existing
        } else {
            #if canImport(MWDATCamera)
            source = MetaGlassesFrameSource()   // real Ray-Ban POV once the DAT package is linked
            #else
            source = MockCameraFrameSource()    // phone-camera stand-in until then
            #endif
        }
        glassesFrameSource = source
        glassesPreviewView.isHidden = false
        if let container = cameraContainerView {
            glassesPreviewView.frame = container.bounds
        }
        source.start { [weak self] image in
            DispatchQueue.main.async { self?.glassesPreviewView.display(image) }
        }
        emitHudCameraEvent(status: "streaming", message: nil)
    }

    private func stopGlassesCamera() {
        glassesFrameSource?.stop()
        glassesFrameSource = nil
        glassesPreviewView.isHidden = true
        emitHudCameraEvent(status: "stopped", message: nil)
    }

    private func configureCameraSession(position: AVCaptureDevice.Position) throws {
        cameraSession.beginConfiguration()
        defer { cameraSession.commitConfiguration() }

        cameraSession.inputs.forEach { cameraSession.removeInput($0) }

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position) else {
            throw HudCameraError.unavailable
        }

        let input = try AVCaptureDeviceInput(device: device)
        guard cameraSession.canAddInput(input) else {
            throw HudCameraError.cannotAddInput
        }

        cameraSession.addInput(input)
        cameraSession.sessionPreset = cameraSession.canSetSessionPreset(.hd1280x720) ? .hd1280x720 : .high
        cameraConfigured = true
    }

    private func emitHudCameraEvent(status: String, message: String?) {
        let payload: [String: String] = [
            "status": status,
            "message": message ?? "",
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8) else {
            return
        }

        let script = """
        window.dispatchEvent(new CustomEvent('trainar:native-camera', { detail: \(json) }));
        """
        webView?.evaluateJavaScript(script)
    }

    private func currentVideoOrientation() -> AVCaptureVideoOrientation {
        guard let orientation = cameraContainerView?.window?.windowScene?.interfaceOrientation else {
            return .portrait
        }
        switch orientation {
        case .landscapeLeft:
            return .landscapeLeft
        case .landscapeRight:
            return .landscapeRight
        case .portraitUpsideDown:
            return .portraitUpsideDown
        default:
            return .portrait
        }
    }

    private func startForwardingEvents() {
        eventTask?.cancel()
        eventTask = Task { [weak self] in
            guard let self else { return }
            for await event in bridge.events {
                Task { @MainActor in
                    self.dispatch(event)
                }
            }
        }
    }

    @MainActor
    private func dispatch(_ event: GlassesBridgeEvent) {
        guard let webView else { return }
        guard let json = event.jsonString else { return }

        let script = """
        window.dispatchEvent(new CustomEvent('trainar:glasses', { detail: \(json) }));
        """
        webView.evaluateJavaScript(script)
    }
}

private enum HudCameraError: LocalizedError {
    case unavailable
    case cannotAddInput

    var errorDescription: String? {
        switch self {
        case .unavailable:
            return "No camera is available on this device."
        case .cannotAddInput:
            return "Could not attach the camera to the preview session."
        }
    }
}
