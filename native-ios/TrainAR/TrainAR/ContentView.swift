import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = AppleVoiceBridge()

    var body: some View {
        TrainARWebView(bridge: bridge)
            .ignoresSafeArea()
            // Phone-camera demo path uses no glasses Bluetooth, so the voice
            // coach (phone mic/speaker) is safe to run alongside it.
            .onAppear { bridge.connect() }
    }
}
