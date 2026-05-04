// Auth hook stub.
//
// The screens never call a backend directly — they only talk to useAuth().
// When a real backend is ready, replace the bodies of signUp/signIn/setName
// with fetch calls. The shape of `user` should stay the same so the screens
// don't need to change.
//
// Persists to localStorage so a refresh keeps you signed in.

(function () {
  const STORAGE_KEY = 'trainar.auth.v1';

  const loadUser = () => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_e) {
      return null;
    }
  };

  const saveUser = (user) => {
    try {
      if (user) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      else window.localStorage.removeItem(STORAGE_KEY);
    } catch (_e) { /* swallow — preview environments may block storage */ }
  };

  // Pretend to talk to a server.
  const fakeDelay = (ms = 600) => new Promise((r) => setTimeout(r, ms));

  // Tiny rules so the UI can show real-feeling validation errors.
  const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const validatePassword = (pw) => typeof pw === 'string' && pw.length >= 8;

  function useAuth() {
    const [user, setUser] = React.useState(loadUser);
    const [pending, setPending] = React.useState(false);
    const [error, setError] = React.useState(null);

    const signUp = async ({ email, password }) => {
      setError(null);
      if (!validateEmail(email))     { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }
      setPending(true);
      await fakeDelay();
      const next = { id: 'local-' + Date.now(), email, name: null };
      setUser(next); saveUser(next);
      setPending(false);
      return true;
    };

    const signIn = async ({ email, password }) => {
      setError(null);
      if (!validateEmail(email))     { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }
      setPending(true);
      await fakeDelay();
      const next = { id: 'local-' + Date.now(), email, name: null };
      setUser(next); saveUser(next);
      setPending(false);
      return true;
    };

    const setName = async (name) => {
      if (!user) return false;
      setPending(true);
      await fakeDelay(300);
      const next = { ...user, name };
      setUser(next); saveUser(next);
      setPending(false);
      return true;
    };

    const signOut = () => { setUser(null); saveUser(null); };

    return { user, pending, error, signUp, signIn, setName, signOut };
  }

  // Password strength scorer used by the signup form (0..4).
  function scorePassword(pw) {
    if (!pw) return 0;
    let score = 0;
    if (pw.length >= 8)  score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
    if (/[0-9]/.test(pw) || /[^A-Za-z0-9]/.test(pw)) score++;
    return Math.min(score, 4);
  }

  Object.assign(window, { useAuth, scorePassword });
})();
