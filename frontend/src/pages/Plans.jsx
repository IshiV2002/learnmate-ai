const plans = [
  {
    name: "Free Student",
    badge: "Prototype plan",
    price: "Free",
    audience: "For students trying LearnMate or studying occasionally.",
    description: "Use the complete learning cycle with your own course material.",
    features: [
      ["Learning material uploads", "available"],
      ["Retrieval, Tutor, Quiz, and Recommendation Agents", "available"],
      ["Basic learning history", "available"],
      ["Secure personal account", "available"],
      ["Limited monthly usage", "planned"],
    ],
    action: "start",
  },
  {
    name: "Student Pro",
    badge: "Coming soon",
    price: "Proposed monthly plan",
    audience: "For students who expect to use LearnMate regularly.",
    description: "More room to learn, practise, and build a longer learning journey.",
    features: [
      ["Everything in Free Student", "available"],
      ["Higher material and AI usage", "planned"],
      ["Advanced personalized recommendations", "planned"],
      ["Extended learning history and insights", "planned"],
      ["Future multilingual learning support", "planned"],
    ],
    action: "planned",
  },
  {
    name: "University / Institutional",
    badge: "Planned institutional plan",
    price: "Custom institutional plan",
    audience: "For universities, departments, and online learning organizations.",
    description: "Bring LearnMate to courses and student communities at a larger scale.",
    features: [
      ["Institution-wide student access", "planned"],
      ["Course-level learning spaces", "planned"],
      ["Approved course material libraries", "planned"],
      ["Access management and institution branding", "planned"],
      ["Future LMS integration and analytics", "planned"],
    ],
    action: "institution",
  },
];

const comparisonRows = [
  ["Material uploads", "Included", "Higher limits — Planned", "Course libraries — Planned"],
  ["Retrieval Agent", "Included", "Higher usage — Planned", "Institution access — Planned"],
  ["Tutor Agent", "Included", "Higher usage — Planned", "Institution access — Planned"],
  ["Quiz Agent", "Included", "Higher usage — Planned", "Course settings — Planned"],
  ["Recommendation Agent", "Included", "Advanced — Planned", "Institution options — Planned"],
  ["Learning history", "Basic", "Extended — Planned", "Reporting — Planned"],
  ["Multilingual support", "Not included", "Planned", "Planned"],
  ["Institution management", "Not included", "Not included", "Planned"],
  ["LMS integration", "Not included", "Not included", "Planned"],
  ["Privacy and security", "Included", "Included", "Included"],
];

const faqs = [
  [
    "Can I use LearnMate for free?",
    "Yes. The current university prototype provides access to the learning workflow without payment. Future Free-plan usage limits are proposed and are not yet enforced.",
  ],
  [
    "What happens to my uploaded learning materials?",
    "LearnMate processes them into searchable sections and preserves page references for grounded learning activities. Your account can access only its own documents.",
  ],
  [
    "Are Student Pro and institutional plans available now?",
    "Not yet. They are planned offerings, and LearnMate currently has no checkout or subscription system.",
  ],
  [
    "What would Student Pro add?",
    "The proposed Pro plan focuses on higher usage, more materials, longer history, and advanced personalization—not stronger basic privacy or security.",
  ],
  [
    "Can a university use LearnMate?",
    "The current prototype demonstrates the student learning experience. Course spaces, centralized management, LMS integration, and institutional analytics are planned future capabilities.",
  ],
  [
    "Can AI responses be wrong?",
    "Yes. LearnMate uses selected source sections to ground responses, but AI output can still be imperfect. Important information should be checked against the provided page references.",
  ],
];

function FeatureStatus({ status }) {
  return (
    <span className={`plans-feature-status plans-feature-status-${status}`}>
      {status === "available" ? "Available now" : "Planned"}
    </span>
  );
}

function ComparisonStatus({ children }) {
  const text = String(children);
  const tone = text.includes("Planned")
    ? "planned"
    : text === "Not included"
      ? "muted"
      : "current";

  return <span className={`plans-status plans-status-${tone}`}>{children}</span>;
}

function Plans({ isAuthenticated, onGetStarted }) {
  return (
    <main className="plans-page">
      <a className="skip-link" href="#plans-main">Skip to plans</a>

      <header className="plans-nav" aria-label="Plans navigation">
        <button className="plans-brand" onClick={onGetStarted} type="button">
          <span className="app-brand-mark" aria-hidden="true">LM</span>
          <span>
            <strong>LearnMate AI</strong>
            <small>Learning plans</small>
          </span>
        </button>
        <nav aria-label="Plans page sections">
          <a href="#plans">Plans</a>
          <a href="#compare">Compare</a>
          <a href="#institutions">Universities</a>
          <a href="#faq">FAQ</a>
        </nav>
        <button className="plans-nav-action" onClick={onGetStarted} type="button">
          {isAuthenticated ? "Return to workspace" : "Sign in or get started"}
        </button>
      </header>

      <div id="plans-main">
        <section className="plans-hero" aria-labelledby="plans-heading">
          <div className="plans-hero-copy">
            <p className="plans-eyebrow">LearnMate plans</p>
            <h1 id="plans-heading">Choose how you want to learn.</h1>
            <p className="plans-hero-intro">
              Start with LearnMate for free. Planned upgrades will give regular
              learners more materials, more AI support, and deeper personalized
              learning.
            </p>
            <div className="plans-hero-actions">
              <a className="plans-button plans-button-primary" href="#plans">Compare plans</a>
              <button className="plans-button plans-button-secondary" onClick={onGetStarted} type="button">
                {isAuthenticated ? "Open my workspace" : "Start free"}
              </button>
            </div>
            <p className="plans-prototype-note">
              Student Pro and institutional plans are planned offerings. No payments are accepted in this prototype.
            </p>
          </div>

          <div className="plans-hero-preview" aria-label="Summary of LearnMate plans">
            <div className="plans-preview-glow" aria-hidden="true" />
            <p>Your learning path</p>
            <div className="plans-preview-plan plans-preview-plan-active">
              <span>Available prototype</span>
              <strong>Free Student</strong>
              <small>Upload · Learn · Practise · Improve</small>
            </div>
            <div className="plans-preview-plan">
              <span>Coming soon</span>
              <strong>Student Pro</strong>
              <small>More materials and deeper support</small>
            </div>
            <div className="plans-preview-plan">
              <span>Planned</span>
              <strong>University</strong>
              <small>Learning support across courses</small>
            </div>
          </div>
        </section>

        <section className="plans-section" id="plans" aria-labelledby="pricing-heading">
          <div className="plans-section-heading plans-section-heading-centered">
            <p className="plans-eyebrow">Plans for every learning stage</p>
            <h2 id="pricing-heading">Start free. Grow when you need more.</h2>
            <p>See what you can use in the current prototype and what is planned for future LearnMate plans.</p>
          </div>

          <div className="plans-pricing-grid">
            {plans.map((plan) => (
              <article className="plans-pricing-card" key={plan.name}>
                <p className="plans-plan-label">{plan.badge}</p>
                <h3>{plan.name}</h3>
                <p className="plans-price">{plan.price}</p>
                <p className="plans-plan-audience">{plan.audience}</p>
                <p className="plans-plan-description">{plan.description}</p>
                <ul>
                  {plan.features.map(([feature, status]) => (
                    <li key={feature}>
                      <span>{feature}</span>
                      <FeatureStatus status={status} />
                    </li>
                  ))}
                </ul>
                {plan.action === "start" && (
                  <button className="plans-card-action" onClick={onGetStarted} type="button">
                    {isAuthenticated ? "Current workspace" : "Start free"}
                  </button>
                )}
                {plan.action === "planned" && (
                  <span className="plans-card-action plans-card-action-muted">Planned Pro</span>
                )}
                {plan.action === "institution" && (
                  <a className="plans-card-action plans-card-action-secondary" href="#institutions">
                    Learn about institutional plans
                  </a>
                )}
              </article>
            ))}
          </div>

          <div className="plans-comparison" id="compare" aria-labelledby="comparison-heading">
            <div className="plans-comparison-heading">
              <div>
                <p className="plans-eyebrow">Feature comparison</p>
                <h3 id="comparison-heading">Find the right level of support.</h3>
              </div>
              <p>Labels distinguish current prototype capabilities from planned plan features.</p>
            </div>
            <div className="plans-table-scroll" tabIndex="0" aria-label="Scrollable plan feature comparison">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Feature</th>
                    <th scope="col">Free Student</th>
                    <th scope="col">Student Pro</th>
                    <th scope="col">University</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map(([feature, ...values]) => (
                    <tr key={feature}>
                      <th scope="row">{feature}</th>
                      {values.map((value, index) => (
                        <td key={`${feature}-${index}`}><ComparisonStatus>{value}</ComparisonStatus></td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="plans-benefits" aria-labelledby="benefits-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Why choose more support?</p>
            <h2 id="benefits-heading">A plan that can grow with your learning.</h2>
          </div>
          <div className="plans-benefit-grid">
            <article>
              <span className="plans-card-number">For regular learners</span>
              <h3>Spend more time learning, not managing limits.</h3>
              <ul>
                <li>Work with more learning materials</li>
                <li>Use the Tutor and Quiz Agents more often</li>
                <li>Build a longer learning history</li>
                <li>Receive deeper personalized guidance</li>
              </ul>
              <small>These Student Pro benefits are planned and not currently enforced.</small>
            </article>
            <article>
              <span className="plans-card-number">For universities</span>
              <h3>Extend trusted course material into guided support.</h3>
              <ul>
                <li>Create future course-level learning spaces</li>
                <li>Support students around approved materials</li>
                <li>Connect with existing learning systems later</li>
                <li>Manage access through planned institution tools</li>
              </ul>
              <small>Institutional capabilities remain planned future features.</small>
            </article>
          </div>
        </section>

        <section className="plans-institution" id="institutions" aria-labelledby="institution-heading">
          <div className="plans-institution-copy">
            <p className="plans-eyebrow">LearnMate for universities</p>
            <h2 id="institution-heading">Personalized learning around the material you already trust.</h2>
            <p>
              A future institutional plan could help universities, faculties,
              departments, and learning providers offer AI-assisted tutoring,
              practice, and next-step guidance around approved course material.
            </p>
            <ul>
              <li>Planned course-level learning spaces</li>
              <li>Planned centralized access management</li>
              <li>Planned institutional branding and analytics</li>
              <li>Future LMS integration</li>
            </ul>
            <a className="plans-button plans-button-primary" href="#faq">Explore institutional questions</a>
            <p className="plans-institution-note">Informational only — no contact or purchasing system is active.</p>
          </div>
          <div className="plans-institution-visual" aria-hidden="true">
            <div className="plans-campus-core">LearnMate</div>
            <span>Courses</span>
            <span>Students</span>
            <span>Materials</span>
            <span>Learning support</span>
          </div>
        </section>

        <section className="plans-trust" aria-labelledby="trust-heading">
          <div>
            <p className="plans-eyebrow">Included for everyone</p>
            <h2 id="trust-heading">Privacy and safety are not upgrades.</h2>
            <p>
              Every LearnMate plan should include secure account access,
              authorization, document privacy, source transparency, and Responsible
              AI safeguards. Future paid plans add capacity and convenience—not
              stronger basic protection.
            </p>
          </div>
          <ul>
            <li>Secure personal account access</li>
            <li>User-specific documents and learning data</li>
            <li>Source references where supported</li>
            <li>Clear reminders that AI can be imperfect</li>
          </ul>
        </section>

        <section className="plans-faq plans-section" id="faq" aria-labelledby="faq-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Frequently asked questions</p>
            <h2 id="faq-heading">A few helpful answers before you begin.</h2>
          </div>
          <div className="plans-faq-list">
            {faqs.map(([question, answer]) => (
              <details key={question}>
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="plans-final-cta" aria-labelledby="plans-final-heading">
          <p className="plans-eyebrow">Ready when you are</p>
          <h2 id="plans-final-heading">Turn your course material into a connected learning space.</h2>
          <button className="plans-button plans-button-primary" onClick={onGetStarted} type="button">
            {isAuthenticated ? "Return to your workspace" : "Start free with the prototype"}
          </button>
          <p>No checkout or paid subscription is available in this university prototype.</p>
        </section>
      </div>
    </main>
  );
}

export default Plans;
