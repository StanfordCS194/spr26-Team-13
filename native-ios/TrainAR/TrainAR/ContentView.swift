import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = AppleVoiceBridge()

    var body: some View {
        TrainARWebView(bridge: bridge)
            .ignoresSafeArea()
            // Voice coach uses the phone mic/speaker (not the glasses' Bluetooth
            // HFP), so it coexists with DAT camera streaming.
            .onAppear { bridge.connect() }
    }
}
