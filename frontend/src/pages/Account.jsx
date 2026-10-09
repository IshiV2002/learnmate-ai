import { useEffect, useMemo, useState } from "react";

import Icon from "../components/ui/Icon.jsx";
import {
  getDocuments,
  getQuizAttempts,
  getStudentRecommendations,
  getStudentTutorSessions,
  listAllQuizzes,
} from "../services/api.js";
import {
  formatAccountDate,
  getAccountStats,
  getAccountSuggestions,
  getAttemptPercentage,
  getInitials,
} from "./account/accountUtils.js";
import "./Account.css";

function newestFirst(items, dateField = "created_at") {
  return [...items].sort(
    (firstItem, secondItem) =>
      (Date.parse(secondItem?.[dateField] || "") || 0) -
      (Date.parse(firstItem?.[dateField] || "") || 0),
  );
}

function Account({ onNavigate, onViewPlans, user }) {
  const [activity, setActivity] = useState({
    attempts: [],
    documents: [],
    quizzes: [],
    recommendations: [],
    tutorSessions: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [loadMessage, setLoadMessage] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function loadAccountActivity() {
      setIsLoading(true);
      setLoadMessage("");

      const results = await Promise.allSettled([
        getDocuments(),
        listAllQuizzes(),
        getQuizAttempts(),
        getStudentTutorSessions(user.user_id),
        getStudentRecommendations(user.user_id),
      ]);

      if (isCancelled) return;

      const valueOrEmptyList = (result) =>
        result.status === "fulfilled" && Array.isArray(result.value)
          ? result.value
          : [];

      setActivity({
        documents: valueOrEmptyList(results[0]),
        quizzes: valueOrEmptyList(results[1]),
        attempts: valueOrEmptyList(results[2]),
        tutorSessions: valueOrEmptyList(results[3]),
        recommendations: valueOrEmptyList(results[4]),
      });

      if (results.some((result) => result.status === "rejected")) {
        setLoadMessage(
          "Some recent activity could not be loaded. Your available account information is shown below.",
        );
      }

      setIsLoading(false);
    }

    loadAccountActivity();
    return () => {
      isCancelled = true;
    };
  }, [user.user_id]);

  const stats = useMemo(() => getAccountStats(activity), [activity]);
  const suggestions = useMemo(() => getAccountSuggestions(stats), [stats]);
  const recentMaterials = useMemo(
    () => newestFirst(activity.documents).slice(0, 4),
    [activity.documents],
  );
  const recentAttempts = useMemo(
    () => newestFirst(activity.attempts).slice(0, 4),
    [activity.attempts],
  );

  return (
    <div className="account-page">
      <header className="account-hero">
        <div className="account-profile">
          <span className="account-avatar" aria-hidden="true">
            {getInitials(user.full_name)}
          </span>
          <div>
            <p className="account-eyebrow">My account</p>
            <h1>{user.full_name}</h1>
            <p>{user.email}</p>
            <span className="account-member-date">
              Student workspace · Member since {formatAccountDate(user.created_at)}
            </span>
          </div>
        </div>

        <section className="account-plan-card" aria-labelledby="account-plan-heading">
          <div className="account-plan-heading">
            <div>
              <p className="account-eyebrow">Current plan</p>
              <h2 id="account-plan-heading">Free Student</h2>
            </div>
            <span>$0 / month</span>
          </div>
          <p>
            You are using the available university prototype. Proposed credit and usage limits are not currently charged or enforced.
          </p>
          <button onClick={onViewPlans} type="button">
            Compare plans <span aria-hidden="true">→</span>
          </button>
        </section>
      </header>

      {loadMessage && <p className="account-load-message" role="status">{loadMessage}</p>}

      <section className="account-overview" aria-labelledby="account-overview-heading">
        <div className="account-section-heading">
          <div>
            <p className="account-eyebrow">Study overview</p>
            <h2 id="account-overview-heading">Your LearnMate activity</h2>
          </div>
          {isLoading && <span className="account-loading-label">Updating…</span>}
        </div>

        <div className="account-stat-grid" aria-busy={isLoading}>
          <article>
            <span className="account-stat-icon account-stat-sage"><Icon name="materials" size={20} /></span>
            <strong>{isLoading ? "—" : stats.materials}</strong>
            <p>Uploaded materials</p>
            <small>{isLoading ? "Loading library" : `${stats.pages} pages available`}</small>
          </article>
          <article>
            <span className="account-stat-icon account-stat-peach"><Icon name="quiz" size={20} /></span>
            <strong>{isLoading ? "—" : stats.quizzesTaken}</strong>
            <p>Quizzes taken</p>
            <small>{isLoading ? "Loading results" : `${stats.generatedQuizzes} quizzes generated`}</small>
          </article>
          <article>
            <span className="account-stat-icon account-stat-blue"><Icon name="tutor" size={20} /></span>
            <strong>{isLoading ? "—" : stats.tutorSessions}</strong>
            <p>Tutor sessions</p>
            <small>Guided study conversations</small>
          </article>
          <article>
            <span className="account-stat-icon account-stat-lavender"><Icon name="recommendations" size={20} /></span>
            <strong>{isLoading ? "—" : stats.averageScore === null ? "—" : `${stats.averageScore}%`}</strong>
            <p>Average quiz score</p>
            <small>{stats.recommendations} saved recommendations</small>
          </article>
        </div>
      </section>

      <section className="account-activity-grid" aria-label="Recent account activity">
        <article className="account-activity-card">
          <div className="account-card-heading">
            <div>
              <p className="account-eyebrow">Recent results</p>
              <h2>Quizzes taken</h2>
            </div>
            <button onClick={() => onNavigate("quiz")} type="button">Open quizzes</button>
          </div>

          {isLoading ? (
            <p className="account-card-empty">Loading quiz history…</p>
          ) : recentAttempts.length === 0 ? (
            <div className="account-card-empty">
              <Icon name="quiz" size={24} />
              <strong>No completed quizzes yet</strong>
              <p>Take a quiz to begin building your results history.</p>
            </div>
          ) : (
            <ul className="account-result-list">
              {recentAttempts.map((attempt) => {
                const percentage = getAttemptPercentage(attempt);
                return (
                  <li key={attempt.attempt_id}>
                    <div>
                      <strong>{attempt.quiz_title || "Practice quiz"}</strong>
                      <small>{formatAccountDate(attempt.created_at)}</small>
                    </div>
                    <span>{percentage === null ? "—" : `${percentage}%`}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </article>

        <article className="account-activity-card">
          <div className="account-card-heading">
            <div>
              <p className="account-eyebrow">Course library</p>
              <h2>Recently uploaded</h2>
            </div>
            <button onClick={() => onNavigate("materials")} type="button">View library</button>
          </div>

          {isLoading ? (
            <p className="account-card-empty">Loading materials…</p>
          ) : recentMaterials.length === 0 ? (
            <div className="account-card-empty">
              <Icon name="materials" size={24} />
              <strong>No materials uploaded yet</strong>
              <p>Add lecture notes or a reading to start your library.</p>
            </div>
          ) : (
            <ul className="account-material-list">
              {recentMaterials.map((document) => (
                <li key={document.document_id}>
                  <span aria-hidden="true"><Icon name="materials" size={17} /></span>
                  <div>
                    <strong title={document.original_filename}>{document.original_filename}</strong>
                    <small>{document.page_count || 0} pages · Added {formatAccountDate(document.created_at)}</small>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="account-suggestions" aria-labelledby="account-suggestions-heading">
        <div className="account-section-heading">
          <div>
            <p className="account-eyebrow">Recommended features</p>
            <h2 id="account-suggestions-heading">Useful next steps for your account</h2>
          </div>
          <p>Suggestions are based on the activity currently saved in your workspace.</p>
        </div>

        <div className="account-suggestion-grid">
          {suggestions.map((suggestion) => (
            <button
              key={`${suggestion.destination}-${suggestion.title}`}
              onClick={() => onNavigate(suggestion.destination)}
              type="button"
            >
              <span className="account-suggestion-icon"><Icon name={suggestion.icon} size={21} /></span>
              <span className="account-suggestion-eyebrow">{suggestion.eyebrow}</span>
              <strong>{suggestion.title}</strong>
              <span className="account-suggestion-description">{suggestion.description}</span>
              <span className="account-suggestion-action">{suggestion.action} <span aria-hidden="true">→</span></span>
            </button>
          ))}
        </div>
      </section>

      <section className="account-details" aria-labelledby="account-details-heading">
        <div>
          <p className="account-eyebrow">Account details</p>
          <h2 id="account-details-heading">Your student workspace</h2>
        </div>
        <dl>
          <div><dt>Email address</dt><dd>{user.email}</dd></div>
          <div><dt>Account created</dt><dd>{formatAccountDate(user.created_at)}</dd></div>
          <div><dt>Workspace access</dt><dd>Free prototype</dd></div>
          <div><dt>Data access</dt><dd>Private to your signed-in account</dd></div>
        </dl>
      </section>
    </div>
  );
}

export default Account;
