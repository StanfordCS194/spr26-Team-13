# Glasses Chat — One-Time Setup

This branch adds a wake-word ("coach") → LLM → TTS loop that runs entirely
in the native iOS shell. Audio routes through whichever Bluetooth headset
is paired — including Ray-Ban Display glasses, which appear to iOS as a
standard BT audio device.

Wake-word detection is done with Apple's on-device
`SFSpeechRecognizer` (continuous, with `requiresOnDeviceRecognition = true`)
matching the literal word "coach" via whole-word regex in the live transcript.
Same approach used in VisionClaw's iOS shell. **No third-party SDKs, accounts,
or downloaded model files** — everything is built on stock iOS frameworks.

---

## 1. Backend setup

### OpenAI API key

In the repo root, create or edit `.env`:

```
OPENAI_API_KEY=sk-...
```

Optional override (defaults to `gpt-4.1-mini`):

```
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

### Run the server

```bash
cd ~/dev/spr26-Team-13
./.venv/bin/python -m src.main --demo --port 5002
```

> Use `-m src.main`, not `python src/main.py`. The latter puts `src/` on
> `sys.path` instead of the project root and breaks the `from src.X`
> imports inside the app.

You should see Flask start on `http://127.0.0.1:5002`. The chat route
is at `POST /api/chat`.

### Smoke test the route

```bash
curl -sX POST http://127.0.0.1:5002/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"text": "what is a good warmup for squats?"}' | jq
```

Expected: `{"reply": "Start with..."}`. If you see `503 OpenAI client not
configured`, your `OPENAI_API_KEY` isn't set or the `openai` package is
missing.

---

## 2. iOS prerequisites

There's no SPM package to add and no model files to ship. The bridge uses
the `Speech` framework that's already in iOS, plus the same
`SFSpeechRecognizer` that was cherry-picked from PR #82.

Requirements baked into the implementation:

- **iOS 13+** (`requiresOnDeviceRecognition` requires iOS 13)
- **A12 Bionic or newer** (on-device speech models ship on A12+). iPhone XS
  / XR or later — pretty much anything from late 2018 onward.
- **English (en-US)** — the locale is hardcoded in `AppleVoiceBridge.init()`.
  Change `Locale(identifier: "en-US")` to use a different language.

The bridge checks `recognizer.supportsOnDeviceRecognition` at startup and
emits a `voiceError` if the device can't do on-device recognition (which
is required because the cloud STT caps at ~1 minute per session — not
viable for always-listening).

---

## 3. End-to-end verification

### On a physical iPhone (no glasses yet)

1. In Xcode: `open native-ios/TrainAR/TrainAR.xcodeproj`, set the target
   to your iPhone, build & run.
2. Grant Microphone + Speech Recognition permissions when prompted.
3. **Point the app at your Flask server.** The iPhone can't reach
   `127.0.0.1` on your laptop, so `ChatEndpointURL` in `Info.plist`
   needs a reachable URL. Two paths — pick one:

   **Path A — ngrok tunnel (recommended, works on any network).**
   In a terminal:

   ```bash
   brew install ngrok          # one-time, if not installed
   brew upgrade ngrok          # ngrok requires v3.20+ to authenticate
   ngrok http 5002
   ```

   Copy the `https://...ngrok-free.app` URL from the output, then in
   `Info.plist` set:

   ```xml
   <key>ChatEndpointURL</key>
   <string>https://abc123.ngrok-free.app/api/chat</string>
   ```

   (don't forget the `/api/chat` suffix — ngrok forwards the host
   only). This is HTTPS + internet-routable, so it bypasses iOS's
   local-network privacy gate entirely and works on any Wi-Fi
   (including locked-down university/corporate networks that block
   peer-to-peer LAN traffic).

   The free ngrok URL changes on every restart of the tunnel —
   re-paste each time, or get a free static domain from your ngrok
   account if it becomes annoying.

   **Path B — direct LAN IP (only on a permissive network).**
   Find your laptop's LAN IP (`ipconfig getifaddr en0`) and use
   `http://<that-ip>:5002/api/chat`. Add the IP as an
   `NSExceptionDomains` entry in `NSAppTransportSecurity` to allow
   plain HTTP. On first run, accept the *"TrainAR Would Like to Find
   and Connect to Devices on Your Local Network"* popup (declared via
   `NSLocalNetworkUsageDescription`). If the popup never appears, the
   network probably isolates clients — fall back to Path A.
4. Say **"coach"** — you should hear "What up, playa?" from the phone speaker.
5. Immediately ask: **"what's a good warmup for squats?"**
6. After ~0.8s of silence, the bridge POSTs to `/api/chat`. The reply
   plays through the phone speaker.
7. Try again: **"coach, how many sets for hypertrophy?"** — same loop.

### With Ray-Ban Meta / Display glasses paired

1. **Pair via the Meta AI app, not just iOS Settings.** During pairing the
   iPhone will show **two separate Bluetooth Pairing Request popups** —
   one for audio (HFP/A2DP) and one for BLE services. **You must accept
   both.** If you only accept one, music will play through the glasses
   but the mic won't be exposed to third-party apps and our wake-word
   loop will silently fall back to the phone mic.

   You can verify both pairings landed by going to Settings → Bluetooth
   and looking for **two entries** related to the glasses (sometimes one
   labeled with "LE" or similar). Both should show "Connected".
2. With both pairings in place, open TrainAR. The console should print:

   ```
   [AppleVoiceBridge] route(post-activate) ... availableInputs=...,Ray-Ban Meta[BluetoothHFP]
   ```

   If `BluetoothHFP` (or similar BT input) is in `availableInputs`,
   `AVAudioSession` will route both directions through the glasses.
3. Say "coach …" — wake word detected via glasses mic, reply played
   through glasses speakers.
4. Unpair mid-session → audio falls back to the phone with no app restart.

> **Heads up:** the simulator does not expose a real microphone, so
> wake-word testing requires a physical device.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `voiceError` event "Device does not support on-device speech recognition" | Device is pre-A12 (iPhone X or older) or iOS < 13. There's no workaround — `requiresOnDeviceRecognition` needs the on-device model. |
| `voiceError` event "Speech recognizer unavailable" | Speech permission denied, or the en-US recognizer isn't installed on the device. Settings → General → Keyboards → Dictation should be enabled. |
| Wake word triggers on conversation that doesn't include "coach" | False positive from the STT model. Tighten the regex in `containsWakeWord(_:)` — e.g., require a phrase like `"hey coach"` instead of bare `"coach"`. |
| Wake word never triggers | Confirm `SFSpeechRecognizer` is producing partial transcripts: watch Xcode's console for `wakeWordReady` and `wakeWordDetected` events. If no `wakeWordReady`, the audio engine failed to start. |
| `chatError` event "HTTP 503" | Backend has no `OPENAI_API_KEY`. |
| `chatError` event with network error on a physical phone | Phone can't reach `127.0.0.1`. Change `ChatEndpointURL` in `Info.plist` to your laptop's LAN IP, or use ngrok. |
| `Local network prohibited` in Xcode console, no permission popup ever appears | iOS local-network gate not triggering. Common on locked-down Wi-Fi (Stanford, corporate, hotel). Use Path A (ngrok) instead — it sidesteps the gate. |
| `ngrok` errors with `ERR_NGROK_121` "agent version too old" | `brew upgrade ngrok` to ≥3.20. |
| Music plays through glasses but TrainAR wake-word routes to phone mic | Only one of the two Ray-Ban Bluetooth pairings was accepted. Forget the device, re-pair via the Meta AI app, and accept *both* pairing prompts. Check `availableInputs` in the route log — `BluetoothHFP` must appear. |
| Capture cuts off too early after wake word | Increase `utteranceSilenceSeconds` in `AppleVoiceBridge.swift` (currently 0.8). |
| Capture runs past the user's question | Decrease `utteranceSilenceSeconds`, or lower `utteranceTimeoutSeconds` (currently 15s hard cap). |
| Reply takes >20s | Bump `request.timeoutInterval` in `postChat` past 20. |

---

## What this branch does NOT do

- **Tool calling / Supabase writes** — lives on PR #82, kept separate.
- **Display HUD on the glasses** — would require Meta DAT SDK + the
  Display-glasses display APIs.
- **Camera / photo capture** — same, DAT SDK territory.
- **Multi-turn memory** — each `/api/chat` call is independent.
- **Non-English wake words** — locale hardcoded to en-US.
