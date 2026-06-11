import SwiftUI

#if canImport(MWDATCore)
import MWDATCore
#endif

@main
struct TrainARApp: App {
    init() {
        #if canImport(MWDATCore)
        // Configure the Meta Wearables SDK once at launch. Reads the MWDAT
        // Info.plist keys; no-op (and absent) until the DAT package is linked.
        try? Wearables.configure()
        #endif
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .onOpenURL { url in
                    #if canImport(MWDATCore)
                    // Complete the Meta AI registration/permission callback when
                    // it redirects back to trainar://. Without this the grant
                    // never finishes (PermissionError 5) and no device appears.
                    Task { _ = try? await Wearables.shared.handleUrl(url) }
                    #endif
                }
        }
    }
}

