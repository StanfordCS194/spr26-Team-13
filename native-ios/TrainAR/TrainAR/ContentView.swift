import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = AppleVoiceBridge()

    var body: some View {
        TrainARWebView(bridge: bridge)
            .ignoresSafeArea()
            .onAppear { bridge.connect() }
    }
}
