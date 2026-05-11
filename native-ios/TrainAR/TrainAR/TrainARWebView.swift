import SwiftUI
import WebKit

struct TrainARWebView: UIViewRepresentable {
    @ObservedObject var bridge: MockGlassesBridge

    func makeCoordinator() -> Coordinator {
        Coordinator(bridge: bridge)
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController.add(context.coordinator, name: "trainarNative")
        configuration.userContentController.addUserScript(Self.bootstrapScript)

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true
        context.coordinator.attach(webView)

        webView.load(URLRequest(url: Self.webURL))
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        context.coordinator.attach(webView)
    }
}

extension TrainARWebView {
    static var webURL: URL {
        let configured = Bundle.main.object(forInfoDictionaryKey: "TRAINAR_WEB_URL") as? String
        let raw = configured?.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: raw?.isEmpty == false ? raw! : "http://127.0.0.1:5002/ios/")!
    }

    static let bootstrapScript = WKUserScript(
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
        """,
        injectionTime: .atDocumentStart,
        forMainFrameOnly: true
    )
}

final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    private let bridge: MockGlassesBridge
    private weak var webView: WKWebView?
    private var eventTask: Task<Void, Never>?

    init(bridge: MockGlassesBridge) {
        self.bridge = bridge
        super.init()
        startForwardingEvents()
    }

    func attach(_ webView: WKWebView) {
        self.webView = webView
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "trainarNative" else { return }
        guard let body = message.body as? [String: Any],
              let type = body["type"] as? String else {
            return
        }

        bridge.handleWebCommand(type: type, payload: body["payload"])
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        bridge.replayState()
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
