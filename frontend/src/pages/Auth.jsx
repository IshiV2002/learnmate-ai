import { useState } from "react";

import { login, signup } from "../services/api.js";
import { validateEmail, validateSignupForm } from "../auth/authUtils.js";


const initialValues = {
  fullName: "",
  email: "",
  password: "",
  confirmPassword: "",
};

function Auth({ onAuthenticated, onViewPlans }) {
  const [mode, setMode] = useState("login");
  const [values, setValues] = useState(initialValues);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      onAuthenticated(authentication);
    } catch (requestError) {
      setError(requestError.message || "Authentication could not be completed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-orbit auth-orbit-one" aria-hidden="true" />
      <div className="auth-orbit auth-orbit-two" aria-hidden="true" />

      <section className="auth-story" aria-labelledby="auth-heading">
        <div className="auth-brand">
          <span className="app-brand-mark" aria-hidden="true">LM</span>
          <div>
            <strong>LearnMate AI</strong>
            <span>Personal knowledge workspace</span>
          </div>
        </div>
        <p className="auth-eyebrow">Four agents. One learning journey.</p>
        <h1 id="auth-heading">Your course material becomes a connected learning space.</h1>
        <p className="auth-introduction">
          Upload trusted material, learn with grounded tutoring, test your
          understanding, and receive transparent study guidance.
        </p>
        <div className="auth-story-actions">
          <button onClick={onViewPlans} type="button">Explore proposed plans</button>
          <span>No payment or subscription is required in this prototype.</span>
        </div>
        <div className="auth-agent-map" aria-label="LearnMate agent capabilities">
          {[
            ["01", "Retrieval", "Finds relevant sections with page references"],
            ["02", "Tutor", "Builds explanations from your indexed material"],
            ["03", "Quiz", "Creates grounded knowledge checks"],
            ["04", "Recommend", "Turns results into next study actions"],
          ].map(([number, name, description]) => (
            <article key={name}>
              <span>{number}</span>
              <div><strong>{name}</strong><small>{description}</small></div>
            </article>
          ))}
        </div>
        <p className="auth-transparency">
          AI responses can be imperfect. LearnMate preserves source references so
          you can verify important information against your material.
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

          {error && <div className="auth-error" role="alert">{error}</div>}

          <button className="auth-submit" disabled={isSubmitting} type="submit">
            {isSubmitting
              ? "Securing your session…"
              : isSignup
                ? "Create secure workspace"
                : "Sign in to LearnMate"}
          </button>
        </form>

        <div className="auth-security-note">
          <span aria-hidden="true">✓</span>
          Passwords are one-way hashed. Your login token expires automatically.
        </div>
      </section>
    </main>
  );
}

export default Auth;
