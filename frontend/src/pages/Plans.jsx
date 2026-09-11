const audiences = [
  {
    number: "01",
    title: "University students",
    description:
      "Turn selected course materials into one space for grounded tutoring, practice, and clearer next steps.",
    value: "Less tool switching. More structured revision.",
  },
  {
    number: "02",
    title: "Universities",
    description:
      "Extend approved course material into AI-assisted learning support without manually building every interaction.",
    value: "A consistent learning workflow that can scale across courses.",
  },
  {
    number: "03",
    title: "Learning providers",
    description:
      "Add a guided learning layer around existing training content and support learners between formal sessions.",
    value: "More value from material providers already maintain.",
  },
];

const plans = [
  {
    name: "Free Student",
    audience: "Proposed entry plan",
    price: "Free",
    description: "A low-barrier way to experience the complete learning cycle.",
    features: [
      "Limited monthly usage",
      "Learning material workspace",
      "Basic Tutor and Quiz access",
      "Basic study recommendations",
      "Standard learning history where supported",
    ],
    action: "start",
  },
  {
    name: "Student Premium",
    audience: "Future commercial offering",
    price: "Proposed monthly or annual subscription",
    description: "For students who want greater capacity and continuity.",
    features: [
      "Higher planned usage limits",
      "More learning materials",
      "Extended Tutor usage",
      "Advanced recommendation features",
      "Deeper history and future multilingual support",
    ],
    action: "planned",
  },
  {
    name: "University / Institutional",
    audience: "Planned for production",
    price: "Custom institutional pricing",
    description: "A licensed learning layer for courses, departments, or providers.",
    features: [
      "Multiple student accounts",
      "Course-level integrations",
      "Institutional privacy controls",
      "Future administration and usage reporting",
      "Future branding and LMS integration",
    ],
    action: "institution",
  },
];

const comparisonRows = [
  ["Learning material upload", "Current prototype", "Higher allowance — Planned", "Course libraries — Planned"],
  ["Tutor Agent", "Basic access — Proposed", "Extended access — Planned", "Course-wide access — Planned"],
  ["Quiz Agent", "Basic access — Proposed", "Higher usage — Planned", "Course configuration — Planned"],
  ["Recommendation Agent", "Basic guidance — Proposed", "Advanced guidance — Planned", "Institution options — Planned"],
  ["Learning history", "Standard history", "Deeper history — Planned", "Usage reporting — Planned"],
  ["Administrative capabilities", "Not included", "Not included", "Planned"],
  ["LMS integration", "Not included", "Not included", "Planned"],
  ["Safety and privacy safeguards", "Included", "Included", "Included"],
];

const learningSteps = ["Upload", "Learn", "Practice", "Evaluate", "Improve"];

const roadmap = [
  ["Student pilot", "Invite a small university student group to test usability and the complete learning workflow."],
  ["Freemium release", "Use a free tier to lower adoption barriers, with an optional Premium plan proposed for greater usage."],
  ["University pilots", "Partner with lecturers or departments to evaluate course-specific use in a controlled setting."],
  ["Institutional licensing", "Offer annual licensing after production infrastructure, administration, and LMS integration are ready."],
  ["Broader market", "Expand carefully to online learning providers, more higher-education settings, and multilingual learning."],
];

function StatusText({ children }) {
  const isPlanned = String(children).includes("Planned");
  const isUnavailable = children === "Not included";

  return (
    <span
      className={`plans-status ${
        isPlanned ? "plans-status-planned" : isUnavailable ? "plans-status-muted" : "plans-status-current"
      }`}
    >
      {children}
    </span>
  );
}

function Plans({ isAuthenticated, onGetStarted }) {
  return (
    <main className="plans-page">
      <a className="skip-link" href="#plans-main">Skip to plans</a>

      <header className="plans-nav" aria-label="Commercialization navigation">
        <button className="plans-brand" onClick={onGetStarted} type="button">
          <span className="app-brand-mark" aria-hidden="true">LM</span>
          <span>
            <strong>LearnMate AI</strong>
            <small>Commercialization vision</small>
          </span>
        </button>
        <nav aria-label="Plans page sections">
          <a href="#audiences">Who it serves</a>
          <a href="#plans">Proposed plans</a>
          <a href="#institutions">Institutions</a>
        </nav>
        <button className="plans-nav-action" onClick={onGetStarted} type="button">
          {isAuthenticated ? "Return to workspace" : "Sign in or get started"}
        </button>
      </header>

      <div id="plans-main">
        <section className="plans-hero" aria-labelledby="plans-heading">
          <div className="plans-hero-copy">
            <p className="plans-eyebrow">Proposed commercialization model</p>
            <h1 id="plans-heading">Learning that grows with you.</h1>
            <p className="plans-hero-intro">
              Start with one student and their course material. Scale toward a
              university-wide learning layer when personalized AI support becomes
              part of the institution.
            </p>
            <div className="plans-hero-actions">
              <a className="plans-button plans-button-primary" href="#plans">Explore proposed plans</a>
              <a className="plans-button plans-button-secondary" href="#institutions">LearnMate for universities</a>
            </div>
            <p className="plans-prototype-note">
              Commercial concept only — LearnMate does not currently process payments or enforce subscriptions.
            </p>
          </div>

          <div className="plans-loop-card" aria-label="LearnMate coordinated learning cycle">
            <div className="plans-loop-orbit" aria-hidden="true" />
            <div className="plans-loop-core">
              <span>4</span>
              <strong>specialized agents</strong>
              <small>one coordinated journey</small>
            </div>
            <ol>
              {learningSteps.map((step, index) => (
                <li key={step}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="plans-section" id="audiences" aria-labelledby="audiences-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Target market</p>
            <h2 id="audiences-heading">Built for learners. Designed to scale with educators.</h2>
            <p>Three customer groups share one need: more useful learning support around material they already trust.</p>
          </div>
          <div className="plans-audience-grid">
            {audiences.map((audience) => (
              <article className="plans-audience-card" key={audience.title}>
                <span className="plans-card-number">{audience.number}</span>
                <h3>{audience.title}</h3>
                <p>{audience.description}</p>
                <strong>{audience.value}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="plans-section" id="plans" aria-labelledby="pricing-heading">
          <div className="plans-section-heading plans-section-heading-centered">
            <p className="plans-eyebrow">Proposed plans</p>
            <h2 id="pricing-heading">A credible path from access to sustainable growth.</h2>
            <p>Plan names and benefits describe a future business model. No paid service is currently being offered.</p>
          </div>
          <div className="plans-pricing-grid">
            {plans.map((plan) => (
              <article className="plans-pricing-card" key={plan.name}>
                <p className="plans-plan-label">{plan.audience}</p>
                <h3>{plan.name}</h3>
                <p className="plans-price">{plan.price}</p>
                <p className="plans-plan-description">{plan.description}</p>
                <ul>
                  {plan.features.map((feature) => <li key={feature}>{feature}</li>)}
                </ul>
                {plan.action === "start" && (
                  <button className="plans-card-action" onClick={onGetStarted} type="button">Get started</button>
                )}
                {plan.action === "planned" && (
                  <span className="plans-card-action plans-card-action-muted">Planned Premium</span>
                )}
                {plan.action === "institution" && (
                  <a className="plans-card-action plans-card-action-secondary" href="#institutions">Learn more</a>
                )}
              </article>
            ))}
          </div>

          <div className="plans-comparison" aria-labelledby="comparison-heading">
            <div className="plans-comparison-heading">
              <div>
                <p className="plans-eyebrow">Capability view</p>
                <h3 id="comparison-heading">What is available and what is planned</h3>
              </div>
              <p>“Planned” means the commercial capability is not implemented in the current prototype.</p>
            </div>
            <div className="plans-table-scroll" tabIndex="0" aria-label="Scrollable plan feature comparison">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Capability</th>
                    <th scope="col">Free Student</th>
                    <th scope="col">Student Premium</th>
                    <th scope="col">Institution</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map(([feature, ...values]) => (
                    <tr key={feature}>
                      <th scope="row">{feature}</th>
                      {values.map((value, index) => <td key={`${feature}-${index}`}><StatusText>{value}</StatusText></td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="plans-value-section" aria-labelledby="value-flow-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Why customers would pay</p>
            <h2 id="value-flow-heading">Value comes from the connected workflow.</h2>
            <p>LearnMate brings course-grounded learning activities together instead of selling access to a single isolated tool.</p>
          </div>
          <div className="plans-value-grid">
            <article>
              <span>Student value flow</span>
              <div className="plans-flow" aria-label="Student value flow">
                {["Lecture material", "Grounded Tutor", "Practice Quiz", "Performance review", "Next steps"].map((item, index) => (
                  <div key={item}><strong>{item}</strong>{index < 4 && <i aria-hidden="true">→</i>}</div>
                ))}
              </div>
              <p>Potential value: less tool switching, structured revision, and personalized support based on selected material.</p>
            </article>
            <article>
              <span>Institution value flow</span>
              <div className="plans-flow plans-flow-short" aria-label="Institution value flow">
                {["Existing course material", "LearnMate", "Student support at scale"].map((item, index) => (
                  <div key={item}><strong>{item}</strong>{index < 2 && <i aria-hidden="true">→</i>}</div>
                ))}
              </div>
              <p>Potential value: reuse approved content and extend consistent learning support without manually creating every interaction.</p>
            </article>
          </div>
        </section>

        <section className="plans-difference plans-section" aria-labelledby="difference-heading">
          <div>
            <p className="plans-eyebrow">Product positioning</p>
            <h2 id="difference-heading">Why not only use a general-purpose chatbot?</h2>
            <p>
              General-purpose AI is useful for broad conversation. LearnMate is
              organized around a student’s selected course material and a repeatable
              learning workflow, with different agents responsible for retrieval,
              tutoring, assessment, and next-step guidance.
            </p>
            <strong>LearnMate combines specialized learning agents into one coordinated learning journey.</strong>
          </div>
          <div className="plans-cycle" aria-label="LearnMate differentiating cycle">
            {learningSteps.map((step, index) => (
              <div key={step}>
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="plans-institution" id="institutions" aria-labelledby="institution-heading">
          <div className="plans-institution-copy">
            <p className="plans-eyebrow">LearnMate for universities</p>
            <h2 id="institution-heading">Build personalized support around approved course material.</h2>
            <p>
              A future institutional version could be introduced course by course,
              then expanded after responsible pilot evaluation. Administration,
              reporting, institutional branding, and LMS connections remain planned
              production capabilities—not features of this prototype.
            </p>
            <ul>
              <li>AI-assisted tutoring grounded in course sources</li>
              <li>Self-assessment quizzes and personalized recommendations</li>
              <li>Future institutional privacy and administration controls</li>
              <li>Future LMS integration for established course workflows</li>
            </ul>
            <a className="plans-button plans-button-primary" href="#deployment">Explore the production plan</a>
          </div>
          <div className="plans-institution-visual" aria-hidden="true">
            <div className="plans-campus-core">LearnMate</div>
            <span>Course A</span>
            <span>Course B</span>
            <span>Course C</span>
            <span>Students</span>
          </div>
        </section>

        <section className="plans-section" id="deployment" aria-labelledby="deployment-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Deployment strategy</p>
            <h2 id="deployment-heading">From academic prototype to production service.</h2>
            <p>This is an architectural roadmap only. The current local stack has not been presented as a production deployment.</p>
          </div>
          <div className="plans-deployment-grid">
            <article>
              <span className="plans-stage-label">Current prototype</span>
              <h3>Local application architecture</h3>
              <ul>
                <li>React and Vite frontend</li>
                <li>FastAPI backend</li>
                <li>SQLite relational metadata</li>
                <li>Local ChromaDB and file storage</li>
                <li>Gemini API integration</li>
              </ul>
            </article>
            <div className="plans-deployment-arrow" aria-hidden="true">→</div>
            <article>
              <span className="plans-stage-label plans-stage-label-future">Production plan</span>
              <h3>Managed cloud architecture</h3>
              <ul>
                <li>Cloud-hosted frontend and FastAPI service</li>
                <li>Managed PostgreSQL</li>
                <li>Production vector storage</li>
                <li>Cloud object storage for documents</li>
                <li>HTTPS, secret management, rate limits, and monitoring</li>
              </ul>
            </article>
          </div>
        </section>

        <section className="plans-section" aria-labelledby="roadmap-heading">
          <div className="plans-section-heading">
            <p className="plans-eyebrow">Proposed go-to-market roadmap</p>
            <h2 id="roadmap-heading">Pilot carefully. Learn. Then scale.</h2>
          </div>
          <ol className="plans-roadmap">
            {roadmap.map(([title, description], index) => (
              <li key={title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div><h3>{title}</h3><p>{description}</p></div>
              </li>
            ))}
          </ol>
        </section>

        <section className="plans-trust" aria-labelledby="trust-heading">
          <div>
            <p className="plans-eyebrow">Responsible commercialization</p>
            <h2 id="trust-heading">Trust is not a premium feature.</h2>
            <p>
              Paid tiers may change usage limits, convenience, and advanced
              capabilities. They should never make essential safety, privacy, source
              transparency, or authorization protections exclusive to paying users.
            </p>
          </div>
          <ul>
            <li>Secure authentication for every user</li>
            <li>Document ownership and access controls</li>
            <li>Responsible AI safeguards and source transparency</li>
            <li>Accessible experiences across proposed plans</li>
          </ul>
        </section>

        <section className="plans-final-cta" aria-labelledby="plans-final-heading">
          <p className="plans-eyebrow">The LearnMate opportunity</p>
          <h2 id="plans-final-heading">One learning cycle. A path from individual value to institutional scale.</h2>
          <button className="plans-button plans-button-primary" onClick={onGetStarted} type="button">
            {isAuthenticated ? "Return to your workspace" : "Get started with the prototype"}
          </button>
          <p>No checkout or paid subscription is available in this academic prototype.</p>
        </section>
      </div>
    </main>
  );
}

export default Plans;
