import { useEffect, useRef, useState } from "react";


const GOOGLE_SCRIPT_ID = "google-identity-services";
const GOOGLE_SCRIPT_URL = "https://accounts.google.com/gsi/client";
const googleClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID || "").trim();

let scriptPromise = null;
let initializedClientId = null;
let activeCredentialHandler = null;

function loadGoogleIdentityServices() {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (scriptPromise) {
    return scriptPromise;
  }

  scriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.getElementById(GOOGLE_SCRIPT_ID);
    const script = existingScript || document.createElement("script");

    script.addEventListener("load", resolve, { once: true });
    script.addEventListener(
      "error",
      () => reject(new Error("Google sign-in could not be loaded.")),
      { once: true },
    );

    if (!existingScript) {
      script.id = GOOGLE_SCRIPT_ID;
      script.src = GOOGLE_SCRIPT_URL;
      script.async = true;
      document.head.appendChild(script);
    }
  });

  return scriptPromise;
}

function GoogleSignInButton({ disabled, mode, onCredential }) {
  const containerRef = useRef(null);
  const [loadError, setLoadError] = useState("");
  const isConfigured = Boolean(
    googleClientId && !googleClientId.startsWith("replace_with_"),
  );

  useEffect(() => {
    if (!isConfigured) {
      return undefined;
    }

    let cancelled = false;
    const credentialHandler = (response) => {
      if (!disabled && response?.credential) {
        onCredential(response.credential);
      }
    };
    activeCredentialHandler = credentialHandler;

    loadGoogleIdentityServices()
      .then(() => {
        if (cancelled || !containerRef.current) {
          return;
        }

        if (initializedClientId !== googleClientId) {
          window.google.accounts.id.initialize({
            auto_select: false,
            callback: (response) => activeCredentialHandler?.(response),
            client_id: googleClientId,
            ux_mode: "popup",
          });
          initializedClientId = googleClientId;
        }

        const availableWidth = Math.floor(
          containerRef.current.getBoundingClientRect().width,
        );
        containerRef.current.replaceChildren();
        window.google.accounts.id.renderButton(containerRef.current, {
          logo_alignment: "left",
          shape: "pill",
          size: "large",
          text: mode === "signup" ? "signup_with" : "signin_with",
          theme: "outline",
          type: "standard",
          width: Math.max(240, Math.min(availableWidth, 400)),
        });
      })
      .catch((error) => {
        if (!cancelled) {
          setLoadError(error.message);
        }
      });

    return () => {
      cancelled = true;
      if (activeCredentialHandler === credentialHandler) {
        activeCredentialHandler = null;
      }
    };
  }, [disabled, isConfigured, mode, onCredential]);

  if (!isConfigured) {
    return (
      <p className="auth-google-unavailable">
        Google sign-in will appear after the local client ID is configured.
      </p>
    );
  }

  if (loadError) {
    return <p className="auth-google-unavailable">{loadError}</p>;
  }

  return (
    <div
      aria-label="Google account access"
      className={disabled ? "auth-google-button is-busy" : "auth-google-button"}
      ref={containerRef}
    />
  );
}

export default GoogleSignInButton;
