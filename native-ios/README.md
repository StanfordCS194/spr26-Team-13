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
4. Start the Python demo server from the repo root:

   ```bash
   python -m src.main --demo --host 127.0.0.1 --port 5002
   ```

5. Run the app in the iOS Simulator.

The default web URL is `http://127.0.0.1:5002/ios/`, which works in the
Simulator. On a physical iPhone, `127.0.0.1` points at the phone itself, so set
`TRAINAR_WEB_URL` in `TrainAR/Info.plist` to either:

- a LAN URL for your Mac, for example `http://192.168.1.20:5002/ios/`
- a deployed HTTPS URL, for example Vercel

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

