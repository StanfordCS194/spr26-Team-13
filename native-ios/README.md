# TrainAR native iOS shell

This folder contains the native iOS handoff target for TrainAR. It is not a
separate product UI yet; it is a thin app shell that can be built in Xcode,
loads the existing TrainAR web experience in a `WKWebView`, and exposes a
native bridge for glasses events.

## Why this exists

The current `ios/` folder is a browser demo. Meta Wearables Device Access
Toolkit code must run inside a native iOS or Android app, so this wrapper gives
the project a real iOS build target without rewriting the whole app in Swift.

The intended flow is:

```text
Meta glasses -> Meta AI permissions/session -> native iOS shell -> TrainAR web UI -> Supabase/backend
```

## Run locally

1. Open `native-ios/TrainAR/TrainAR.xcodeproj` in Xcode.
2. Select the `TrainAR` target.
3. In **Signing & Capabilities**, select your team.
4. Start the Python demo server from the repo root.

   For the iOS Simulator:

   ```bash
   python -m src.main --demo --host 127.0.0.1 --port 5002
   ```

   For a physical iPhone on the same Wi-Fi as your Mac, bind Flask to all
   interfaces so the phone can reach it:

   ```bash
   python -m src.main --demo --host 0.0.0.0 --port 5002
   ```

5. Configure `TrainAR/Info.plist` before running on a physical iPhone.

   The default web URL, `http://127.0.0.1:5002/ios/`, only works in the
   Simulator. On a physical iPhone, `127.0.0.1` points at the phone itself.
   Find your Mac's current LAN IP:

   ```bash
   ipconfig getifaddr en0
   ```

   Update both local endpoints to use that IP:

   ```xml
   <key>TRAINAR_WEB_URL</key>
   <string>http://YOUR_MAC_IP:5002/ios/</string>
   <key>ChatEndpointURL</key>
   <string>http://YOUR_MAC_IP:5002/api/chat</string>
   ```

   Also add `YOUR_MAC_IP` under `NSAppTransportSecurity` ->
   `NSExceptionDomains`, matching the existing localhost/IP entries, so iOS
   allows local HTTP during development.

6. Run the app from Xcode.

   If the phone cannot connect, confirm:

   - the Mac and iPhone are on the same network
   - the server is running with `--host 0.0.0.0`
   - `TRAINAR_WEB_URL` and `ChatEndpointURL` use the same current Mac IP
   - the IP is present in `NSExceptionDomains`
   - iOS local-network permission was accepted

   On networks that isolate devices, use an HTTPS tunnel such as ngrok and set
   `TRAINAR_WEB_URL` / `ChatEndpointURL` to the tunnel URL instead.

## Bridge contract

Native code sends glasses events into the web app with:

```js
window.dispatchEvent(new CustomEvent('trainar:glasses', {
  detail: {
    type: 'connected',
    payload: { battery: 78 }
  }
}));
```

The web app can send commands to native iOS with:

```js
window.webkit.messageHandlers.trainarNative.postMessage({
  type: 'startWorkout',
  payload: { programId: '...' }
});
```

The current shell implements a mock bridge. Your teammate can replace
`MockGlassesBridge` with the real Meta Wearables implementation while keeping
the same `GlassesBridge` protocol and web event contract.

## Meta handoff points

The real Meta implementation belongs in:

- `TrainAR/GlassesBridge.swift`
- `TrainAR/MetaWearablesBridge.swift`
- `TrainAR/Info.plist`

Expected additions when your teammate has the SDK/team details:

- add the Meta Wearables Swift package in Xcode
- call `Wearables.configure()` on app launch
- implement registration/unregistration callbacks
- start and observe device sessions
- publish camera/photo/session events through `GlassesBridgeEvent`
- add the required `Info.plist` keys from Meta's docs

