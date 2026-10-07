import { useEffect } from "react";

const TRANSITION_DURATION_MS = 920;

function BookOpeningTransition({ onComplete }) {
  useEffect(() => {
    const timeoutId = window.setTimeout(onComplete, TRANSITION_DURATION_MS);
    return () => window.clearTimeout(timeoutId);
  }, [onComplete]);

  return (
    <div aria-hidden="true" className="auth-book-transition">
      <div className="auth-book-backdrop" />
      <div className="auth-opening-book">
        <div className="auth-opening-pages">
          <span><i /><i /><i /></span>
          <span><i /><i /><i /></span>
        </div>
        <div className="auth-opening-cover">
          <span className="auth-opening-cover-mark">LM</span>
          <span className="auth-opening-cover-line" />
        </div>
        <span className="auth-opening-spine" />
      </div>
      <p>Welcome to your study space</p>
    </div>
  );
}

export default BookOpeningTransition;
