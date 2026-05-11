import SwiftUI

struct ContentView: View {
    @StateObject private var bridge = MockGlassesBridge()

    var body: some View {
        TrainARWebView(bridge: bridge)
            .ignoresSafeArea()
    }
}
