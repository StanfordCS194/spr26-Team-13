// Supabase-backed auth hook. Screens still consume the same useAuth() shape:
// { user, pending, error, signUp, signIn, setName, signOut }.

(function () {
  const client = () => window.trainarSupabase;

  const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const validatePassword = (pw) => typeof pw === 'string' && pw.length >= 8;
  const messageFromError = (err, fallback) => {
    if (!err) return fallback;
    if (err.message === 'Load failed' || err.message === 'Failed to fetch') {
      return 'Could not reach Supabase. Check your network, localhost redirect URL, and browser console.';
    }
    return err.message || fallback;
  };
  const getEmailRedirectTo = () => {
    if (window.location.protocol === 'file:') return 'http://127.0.0.1:5002/ios/';
    return window.location.origin + window.location.pathname;
  };

  const toScreenUser = (authUser, profile) => {
    if (!authUser) return null;
    return {
      id: authUser.id,
      email: authUser.email || profile?.email || '',
      name: profile?.display_name || null,
      units: profile?.units || 'imperial',
      timezone: profile?.timezone || 'America/Los_Angeles',
    };
  };

  async function fetchProfile(userId) {
    if (!client() || !userId) return null;
    const { data, error } = await client()
      .from('profiles')
      .select('id,email,display_name,units,timezone,onboarded_at')
      .eq('id', userId)
      .maybeSingle();

    if (error) throw error;
    return data;
  }

  async function ensureProfile(authUser) {
    if (!client() || !authUser) return null;
    const existing = await fetchProfile(authUser.id);
    if (existing) return existing;

    const { data, error } = await client()
      .from('profiles')
      .upsert({ id: authUser.id, email: authUser.email || null }, { onConflict: 'id' })
      .select('id,email,display_name,units,timezone,onboarded_at')
      .single();

    if (error) throw error;
    return data;
  }

  function useAuth() {
    const [user, setUser] = React.useState(null);
    const [pending, setPending] = React.useState(true);
    const [error, setError] = React.useState(null);

    const refreshUser = React.useCallback(async (authUser) => {
      if (!authUser) {
        setUser(null);
        return null;
      }
      const profile = await ensureProfile(authUser);
      const next = toScreenUser(authUser, profile);
      setUser(next);
      return next;
    }, []);

    React.useEffect(() => {
      let active = true;
      if (!client()) {
        setError('Supabase is not configured.');
        setPending(false);
        return undefined;
      }

      client().auth.getSession()
        .then(async ({ data, error: sessionError }) => {
          if (sessionError) throw sessionError;
          if (!active) return;
          await refreshUser(data.session?.user || null);
        })
        .catch((err) => {
          if (active) setError(err.message || 'Could not load your session.');
        })
        .finally(() => {
          if (active) setPending(false);
        });

      const { data: listener } = client().auth.onAuthStateChange((_event, session) => {
        refreshUser(session?.user || null).catch((err) => {
          setError(err.message || 'Could not update your session.');
        });
      });

      return () => {
        active = false;
        listener.subscription.unsubscribe();
      };
    }, [refreshUser]);

    const signUp = async ({ email, password }) => {
      setError(null);
      if (!validateEmail(email)) { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }

      setPending(true);
      try {
        const { data, error: signUpError } = await client().auth.signUp({
          email,
          password,
          options: { emailRedirectTo: getEmailRedirectTo() },
        });
        if (signUpError) {
          setError(messageFromError(signUpError, 'Could not create your account.'));
          setPending(false);
          return false;
        }

        await refreshUser(data.user);
        setPending(false);
        return true;
      } catch (err) {
        setError(messageFromError(err, 'Could not create your account.'));
        setPending(false);
        return false;
      }
    };

    const signIn = async ({ email, password }) => {
      setError(null);
      if (!validateEmail(email)) { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }

      setPending(true);
      try {
        const { data, error: signInError } = await client().auth.signInWithPassword({ email, password });
        if (signInError) {
          setError(messageFromError(signInError, 'Could not sign in.'));
          setPending(false);
          return false;
        }

        await refreshUser(data.user);
        setPending(false);
        return true;
      } catch (err) {
        setError(messageFromError(err, 'Could not sign in.'));
        setPending(false);
        return false;
      }
    };

    const setName = async (name) => {
      if (!user) return false;
      setError(null);
      setPending(true);

      const { data, error: updateError } = await client()
        .from('profiles')
        .update({ display_name: name, onboarded_at: new Date().toISOString() })
        .eq('id', user.id)
        .select('id,email,display_name,units,timezone,onboarded_at')
        .single();

      if (updateError) {
        setError(updateError.message);
        setPending(false);
        return false;
      }

      setUser(toScreenUser({ id: user.id, email: user.email }, data));
      setPending(false);
      return true;
    };

    const signOut = async () => {
      setPending(true);
      await client().auth.signOut();
      setUser(null);
      setPending(false);
      if (window.resetTrainarData) window.resetTrainarData();
    };

    return { user, pending, error, signUp, signIn, setName, signOut };
  }

  function scorePassword(pw) {
    if (!pw) return 0;
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
    if (/[0-9]/.test(pw) || /[^A-Za-z0-9]/.test(pw)) score++;
    return Math.min(score, 4);
  }

  Object.assign(window, { useAuth, scorePassword });
})();
