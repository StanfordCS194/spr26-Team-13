# iOS prototype

iPhone-side of TrainAR. Currently just the signup flow — backend hookup comes later.

To open it, just open `ios/index.html` in a browser. No build step. React + Babel are loaded from a CDN at the top of the HTML.

## Layout

- `index.html` — entry point, pulls in scripts in dependency order
- `tokens.css` — design tokens (dark theme, lime accent)
- `ui.jsx` — shared primitives (Icon, Button, Card, Input)
- `ios-frame.jsx` — iPhone device frame (status bar, dynamic island, home indicator)
- `screens-signup.jsx` — splash, auth, name screens
- `auth.js` — `useAuth()` stub — swap with real backend later
- `app.jsx` — wires the screens into the device frame
