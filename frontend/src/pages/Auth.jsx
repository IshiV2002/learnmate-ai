import { useCallback, useState } from "react";

import GoogleSignInButton from "../components/auth/GoogleSignInButton.jsx";
import Icon from "../components/ui/Icon.jsx";
import { login, loginWithGoogle, signup } from "../services/api.js";
import { validateEmail, validateSignupForm } from "../auth/authUtils.js";


const initialValues = {
  fullName: "",
  email: "",
  password: "",
  confirmPassword: "",
};

function Auth({ onAuthenticated, onToggleTheme, onViewPlans, theme }) {
  const [mode, setMode] = useState("login");
  const [values, setValues] = useState(initialValues);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);

  const isSignup = mode === "signup";

  function updateField(event) {
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
    setError("");
  }

  function changeMode(nextMode) {
    setMode(nextMode);
    setValues(initialValues);
    setError("");
    setShowPassword(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const validationMessage = isSignup
      ? validateSignupForm(values)
      : !validateEmail(values.email) || !values.password
        ? "Enter your email address and password."
        : "";

    if (validationMessage) {
      setError(validationMessage);
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      const authentication = isSignup
        ? await signup({
            full_name: values.fullName.trim(),
            email: values.email.trim(),
            password: values.password,
          })
        : await login({
            email: values.email.trim(),
            password: values.password,
          });
      onAuthenticated(authentication, isSignup ? "signup" : "login");
    } catch (requestError) {
      setError(requestError.message || "Authentication could not be completed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const handleGoogleCredential = useCallback(async (credential) => {
    setIsGoogleSubmitting(true);
    setError("");
    try {
      const authentication = await loginWithGoogle(credential);
      onAuthenticated(authentication, "login");
    } catch (requestError) {
      setError(requestError.message || "Google sign-in could not be completed.");
    } finally {
      setIsGoogleSubmitting(false);
    }
  }, [onAuthenticated]);

  return (
    <main className="auth-page">
      <div className="auth-library-arches" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>

      <section className="auth-story" aria-labelledby="auth-heading">
        <div className="auth-brand-row">
          <div className="auth-brand">
            <span className="app-brand-mark" aria-hidden="true">LM</span>
            <div>
              <strong>LearnMate</strong>
              <span>Personal study workspace</span>
            </div>
          </div>
          <button
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="auth-theme-toggle"
            onClick={onToggleTheme}
            type="button"
          >
            <Icon name={theme === "dark" ? "sun" : "moon"} size={17} />
            <span>{theme === "dark" ? "Light" : "Dark"}</span>
          </button>
        </div>
        <p className="auth-eyebrow">A calmer way to study</p>
        <h1 id="auth-heading">Bring your notes. Build a better study routine.</h1>
        <p className="auth-introduction">
          Keep your course material, guided explanations, practice and next
          steps together in one focused workspace.
        </p>

        <div className="auth-photo-stage">
          <div className="auth-stage-orbit" aria-hidden="true" />
          <div className="auth-stage-copy">
            <span>Study at your own pace</span>
            <strong>Your notes, your questions, your next step.</strong>
            <small>One workspace from first read to final review.</small>
          </div>
          <figure className="auth-photo-frame">
            <img
              alt="Three university students studying together with a laptop and notebooks"
              decoding="async"
              fetchPriority="high"
              src="/images/students-collaborating.jpg"
            />
            <figcaption className="auth-photo-credit">
              <a
                href="https://www.pexels.com/photo/group-of-people-studying-together-6609388/"
                rel="noreferrer"
                target="_blank"
              >Photo: Antoni Shkraba / Pexels</a>
            </figcaption>
          </figure>
          <div className="auth-floating-note auth-note-sources">
            <span>01</span>
            <div>
              <strong>Start with your sources</strong>
              <small>Upload notes and keep page references close.</small>
            </div>
          </div>
          <div className="auth-floating-note auth-note-practice">
            <span>02 → 04</span>
            <strong>Understand · Practise · Review</strong>
          </div>
          <span className="auth-stage-bookmark" aria-hidden="true">LM</span>
        </div>

        <div className="auth-story-actions">
          <button onClick={onViewPlans} type="button">Explore plans</button>
          <span>No payment or subscription is required in this prototype.</span>
        </div>
        <p className="auth-transparency">
          LearnMate keeps source references visible so you can check important
          information against the original material.
        </p>
      </section>

      <section className="auth-panel" aria-labelledby="auth-form-title">
        <div className="auth-panel-header">
          <p>{isSignup ? "Create your workspace" : "Welcome back"}</p>
          <h2 id="auth-form-title">
            {isSignup ? "Start learning with your own sources" : "Continue your learning journey"}
          </h2>
        </div>

        <div className="auth-tabs" role="tablist" aria-label="Account access">
          <button
            aria-selected={!isSignup}
            className={!isSignup ? "active" : ""}
            onClick={() => changeMode("login")}
            role="tab"
            type="button"
          >Sign in</button>
          <button
            aria-selected={isSignup}
            className={isSignup ? "active" : ""}
            onClick={() => changeMode("signup")}
            role="tab"
            type="button"
          >Create account</button>
        </div>

        <GoogleSignInButton
          disabled={isSubmitting || isGoogleSubmitting}
          mode={mode}
          onCredential={handleGoogleCredential}
        />

        <div className="auth-divider"><span>or use email and password</span></div>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {isSignup && (
            <label>
              <span>Full name</span>
              <input
                autoComplete="name"
                autoFocus
                name="fullName"
                onChange={updateField}
                placeholder="Your name"
                value={values.fullName}
              />
            </label>
          )}
          <label>
            <span>Email address</span>
            <input
              autoComplete="email"
              autoFocus={!isSignup}
              inputMode="email"
              name="email"
              onChange={updateField}
              placeholder="student@example.com"
              type="email"
              value={values.email}
            />
          </label>
          <label>
            <span>Password</span>
            <div className="auth-password-field">
              <input
                autoComplete={isSignup ? "new-password" : "current-password"}
                name="password"
                onChange={updateField}
                placeholder={isSignup ? "8+ characters" : "Your password"}
                type={showPassword ? "text" : "password"}
                value={values.password}
              />
              <button
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((visible) => !visible)}
                type="button"
              >{showPassword ? "Hide" : "Show"}</button>
            </div>
          </label>
          {isSignup && (
            <>
              <p className="auth-password-help">
                Use uppercase, lowercase, a number, and at least 8 characters.
              </p>
              <label>
                <span>Confirm password</span>
                <input
                  autoComplete="new-password"
                  name="confirmPassword"
                  onChange={updateField}
                  type={showPassword ? "text" : "password"}
                  value={values.confirmPassword}
                />
              </label>
            </>
          )}

          <button
            className="auth-submit"
            disabled={isSubmitting || isGoogleSubmitting}
            type="submit"
          >
            {isSubmitting || isGoogleSubmitting
              ? "Securing your session…"
              : isSignup
                ? "Create secure workspace"
                : "Sign in to LearnMate"}
          </button>
        </form>

        <div className="auth-security-note">
          <span aria-hidden="true">✓</span>
          Passwords are one-way hashed, Google credentials are verified by the
          backend, and LearnMate sessions expire automatically.
        </div>
      </section>
    </main>
  );
}

export default Auth;
