import SwiftUI
import WebKit

struct TrainARWebView<B: GlassesBridge>: UIViewRepresentable {
    @ObservedObject var bridge: B

    func makeCoordinator() -> Coordinator<B> {
        Coordinator(bridge: bridge)
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.userContentController.add(context.coordinator, name: "trainarNative")
        configuration.userContentController.addUserScript(Self.bootstrapScript)
        configuration.userContentController.addUserScript(Self.lockViewportScript)

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        // Side-swipe must not navigate the page away during a workout.
        webView.allowsBackForwardNavigationGestures = false
        context.coordinator.attach(webView)

        // Lock the content in place: vertical scrolling stays for tall screens,
        // but no pinch zoom, no rubber-band bounce, no horizontal drift.
        //
        // NOTE: we deliberately do NOT clamp min/maxZoomScale. Doing so traps the
        // view if WebKit's input-focus auto-zoom kicks in (the user can no longer
        // pinch back out). Instead we disable the pinch recognizer so users can't
        // zoom, and prevent focus-zoom at its source via injected CSS (16px inputs).
        let scrollView = webView.scrollView
        scrollView.bounces = false
        scrollView.bouncesZoom = false
        scrollView.alwaysBounceVertical = false
        scrollView.alwaysBounceHorizontal = false
        scrollView.pinchGestureRecognizer?.isEnabled = false
        scrollView.contentInsetAdjustmentBehavior = .never
        // Definitive zoom kill: as the scroll view's delegate we return nil from
        // viewForZooming, so there is nothing to zoom. Scrolling is unaffected.
        scrollView.delegate = context.coordinator

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

    /// Keeps the layout viewport fixed and — more importantly — prevents the
    /// iOS input-focus auto-zoom by guaranteeing every form control renders at
    /// >= 16px. WebKit only auto-zooms when a focused field is smaller than that,
    /// so forcing 16px removes the trigger entirely (deterministic, unlike the
    /// often-ignored `maximum-scale` viewport hint).
    static var lockViewportScript: WKUserScript {
        WKUserScript(
            source: """
            (function() {
              var content = 'width=device-width, initial-scale=1.0, viewport-fit=cover';
              function lockViewport() {
                var meta = document.querySelector('meta[name=viewport]');
                if (!meta) {
                  meta = document.createElement('meta');
                  meta.name = 'viewport';
                  (document.head || document.documentElement).appendChild(meta);
                }
                if (meta.getAttribute('content') !== content) {
                  meta.setAttribute('content', content);
                }
              }
              function injectNoZoomCSS() {
                if (document.getElementById('trainar-nozoom-style')) return;
                var style = document.createElement('style');
                style.id = 'trainar-nozoom-style';
                // 16px minimum on form controls stops WebKit's focus auto-zoom.
                style.textContent =
                  'input, select, textarea { font-size: 16px !important; }';
                (document.head || document.documentElement).appendChild(style);
              }
              lockViewport();
              injectNoZoomCSS();
              document.addEventListener('DOMContentLoaded', function() {
                lockViewport();
                injectNoZoomCSS();
              });
              // Backstop: block the Safari gesture events used for pinch zoom,
              // and the double-tap-to-zoom path, in case the page re-enables them.
              ['gesturestart', 'gesturechange', 'gestureend'].forEach(function(evt) {
                document.addEventListener(evt, function(e) { e.preventDefault(); }, { passive: false });
              });
            })();
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
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
              window.TrainARNative.postMessage('speakResponse', { text: text });
            });
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
    }
}

final class Coordinator<B: GlassesBridge>: NSObject, WKNavigationDelegate, WKScriptMessageHandler, UIScrollViewDelegate {
    // Returning nil disables pinch/double-tap zoom entirely while leaving
    // normal scrolling intact. This is the reliable way to stop WKWebView
    // zoom — clamping zoomScale traps the view if focus-zoom ever fires.
    func viewForZooming(in scrollView: UIScrollView) -> UIView? { nil }

    private let bridge: B
    private weak var webView: WKWebView?
    private var eventTask: Task<Void, Never>?

    init(bridge: B) {
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
