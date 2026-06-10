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
  const BASE_PROFILE_SELECT = 'id,email,display_name,units,timezone,onboarded_at';
  const TRAINING_PROFILE_SELECT = `${BASE_PROFILE_SELECT},training_goal,training_experience,workout_days_per_week,workout_session_minutes,available_equipment,coach_style,evidence_preference,movement_constraints,training_onboarded_at`;
  const isMissingTrainingColumnError = (error) => {
    const message = String(error?.message || error?.details || '');
    return /profiles\.(training_goal|training_experience|workout_days_per_week|workout_session_minutes|available_equipment|coach_style|evidence_preference|movement_constraints|training_onboarded_at).*does not exist/i.test(message)
      || /Could not find .*training_/i.test(message);
  };

  const toScreenUser = (authUser, profile) => {
    if (!authUser) return null;
    const trainingProfile = profile ? {
      trainingGoal: profile.training_goal || null,
      trainingExperience: profile.training_experience || null,
      workoutDaysPerWeek: profile.workout_days_per_week || null,
      workoutSessionMinutes: profile.workout_session_minutes || null,
      availableEquipment: profile.available_equipment || [],
      coachStyle: profile.coach_style || 'direct',
      evidencePreference: profile.evidence_preference || 'concise',
      movementConstraints: profile.movement_constraints || '',
      trainingOnboardedAt: profile.training_onboarded_at || null,
    } : null;
    window.TRAINAR_TRAINING_PROFILE = trainingProfile;
    return {
      id: authUser.id,
      email: authUser.email || profile?.email || '',
      name: profile?.display_name || null,
      units: profile?.units || 'imperial',
      timezone: profile?.timezone || 'America/Los_Angeles',
      trainingProfile,
      trainingProfileComplete: Boolean(profile?.training_onboarded_at),
    };
  };

  async function fetchProfile(userId) {
    if (!client() || !userId) return null;
    const { data, error } = await client()
      .from('profiles')
      .select(TRAINING_PROFILE_SELECT)
      .eq('id', userId)
      .maybeSingle();

    if (error && isMissingTrainingColumnError(error)) {
      const fallback = await client()
        .from('profiles')
        .select(BASE_PROFILE_SELECT)
        .eq('id', userId)
        .maybeSingle();
      if (fallback.error) throw fallback.error;
      return fallback.data;
    }
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
      .select(TRAINING_PROFILE_SELECT)
      .single();

    if (error && isMissingTrainingColumnError(error)) {
      const fallback = await client()
        .from('profiles')
        .upsert({ id: authUser.id, email: authUser.email || null }, { onConflict: 'id' })
        .select(BASE_PROFILE_SELECT)
        .single();
      if (fallback.error) throw fallback.error;
      return fallback.data;
    }
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
      const normalizedEmail = String(email || '').trim().toLowerCase();
      if (!validateEmail(normalizedEmail)) { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }

      setPending(true);
      try {
        const { data, error: signUpError } = await client().auth.signUp({
          email: normalizedEmail,
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
      const normalizedEmail = String(email || '').trim().toLowerCase();
      if (!validateEmail(normalizedEmail)) { setError('Enter a valid email.'); return false; }
      if (!validatePassword(password)) { setError('Password must be at least 8 characters.'); return false; }

      setPending(true);
      try {
        const { data, error: signInError } = await client().auth.signInWithPassword({
          email: normalizedEmail,
          password,
        });
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
        .update({ display_name: name })
        .eq('id', user.id)
        .select(TRAINING_PROFILE_SELECT)
        .single();

      if (updateError && isMissingTrainingColumnError(updateError)) {
        const fallback = await client()
          .from('profiles')
          .update({ display_name: name })
          .eq('id', user.id)
          .select(BASE_PROFILE_SELECT)
          .single();
        if (fallback.error) {
          setError(fallback.error.message);
          setPending(false);
          return false;
        }
        setUser(toScreenUser({ id: user.id, email: user.email }, fallback.data));
        setPending(false);
        return true;
      }
      if (updateError) {
        setError(updateError.message);
        setPending(false);
        return false;
      }

      setUser(toScreenUser({ id: user.id, email: user.email }, data));
      setPending(false);
      return true;
    };

    const setTrainingProfile = async (profile) => {
      if (!user) return false;
      setError(null);
      setPending(true);

      const row = {
        training_goal: profile.trainingGoal,
        training_experience: profile.trainingExperience,
        workout_days_per_week: Number(profile.workoutDaysPerWeek),
        workout_session_minutes: Number(profile.workoutSessionMinutes),
        available_equipment: profile.availableEquipment || [],
        coach_style: profile.coachStyle || 'direct',
        evidence_preference: profile.evidencePreference || 'concise',
        movement_constraints: profile.movementConstraints || null,
        training_onboarded_at: new Date().toISOString(),
        onboarded_at: new Date().toISOString(),
      };

      const { data, error: updateError } = await client()
        .from('profiles')
        .update(row)
        .eq('id', user.id)
        .select(TRAINING_PROFILE_SELECT)
        .single();

      if (updateError) {
        setError(isMissingTrainingColumnError(updateError)
          ? 'Training profile fields are not in Supabase yet. Run the latest migration, then try again.'
          : updateError.message);
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
      window.TRAINAR_TRAINING_PROFILE = null;
      setPending(false);
      if (window.resetTrainarData) window.resetTrainarData();
    };

    return { user, pending, error, signUp, signIn, setName, setTrainingProfile, signOut };
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
