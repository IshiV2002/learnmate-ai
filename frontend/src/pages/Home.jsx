import Icon from "../components/ui/Icon.jsx";
import "./Home.css";

const studyActions = [
  {
    id: "materials",
    eyebrow: "Start here",
    title: "Add study materials",
    description: "Upload your PDF notes or an image, then keep every source in one tidy library.",
    action: "Open materials",
    artwork: "/images/headers/materials-books.png",
    icon: "materials",
    tone: "sage",
  },
  {
    id: "tutor",
    eyebrow: "Understand",
    title: "Talk through a topic",
    description: "Use guided questions and source citations to work through anything that feels unclear.",
    action: "Open tutor",
    artwork: "/images/headers/tutor-portrait.png",
    icon: "tutor",
    tone: "blue",
  },
  {
    id: "quiz",
    eyebrow: "Practise",
    title: "Check what you remember",
    description: "Create a quiz from your own material and turn reading into active recall.",
    action: "Create a quiz",
    artwork: "/images/headers/quiz-graduation-books.png",
    icon: "quiz",
    tone: "peach",
  },
  {
    id: "recommendations",
    eyebrow: "Review",
    title: "Plan your next step",
    description: "See which topics need more attention after a quiz and choose what to revise next.",
    action: "View recommendations",
    artwork: "/images/headers/study-summary.png",
    icon: "recommendations",
    tone: "lavender",
  },
];

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function Home({ onNavigate, user }) {
  const firstName = user?.full_name?.trim().split(/\s+/)[0] || "there";

  return (
    <div className="home-page">
      <section className="home-hero" aria-labelledby="home-heading">
        <div className="home-hero-copy">
          <p className="home-eyebrow">{getGreeting()}, {firstName}</p>
          <h1 id="home-heading">What would you like to study today?</h1>
          <p>
            Keep your notes, explanations, practice and revision plan in one calm workspace.
            Pick a starting point below and move at your own pace.
          </p>
          <button className="home-primary-action" onClick={() => onNavigate("materials")} type="button">
            <Icon name="materials" size={19} />
            Add study material
          </button>
        </div>

        <div className="home-hero-visual">
          <div className="home-book-scene" aria-hidden="true">
            <span className="home-doodle home-doodle-spark">✦</span>
            <span className="home-doodle home-doodle-star">✧</span>
            <span className="home-pencil"><i /><b /></span>
            <div className="home-book">
              <span className="home-book-cover" />
              <span className="home-book-page home-book-left-page">
                <i className="home-page-title" />
                <i /><i /><i />
                <b className="home-page-leaf">⌁</b>
              </span>
              <span className="home-book-page home-book-right-page">
                <i className="home-page-title" />
                <i /><i /><i />
                <b className="home-page-check">✓</b>
              </span>
              <span className="home-book-turning-page">
                <span className="home-turning-front"><i /><i /><i /></span>
                <span className="home-turning-back"><i /><i /><i /></span>
              </span>
              <span className="home-book-spine" />
            </div>
          </div>

          <div className="home-study-note" aria-label="Simple study routine">
            <div className="home-note-heading">
              <span className="home-note-icon" aria-hidden="true">✓</span>
              <div>
                <p>Simple study routine</p>
                <strong>Learn in three small steps</strong>
              </div>
            </div>
            <ol>
              <li><span>1</span><div><strong>Choose a source</strong><small>Add the notes you want to study.</small></div></li>
              <li><span>2</span><div><strong>Build understanding</strong><small>Ask questions and review cited answers.</small></div></li>
              <li><span>3</span><div><strong>Practise and reflect</strong><small>Take a quiz and revisit weaker topics.</small></div></li>
            </ol>
          </div>
        </div>
      </section>

      <section className="home-actions" aria-labelledby="home-actions-heading">
        <div className="home-section-heading">
          <div>
            <p className="home-eyebrow">Your workspace</p>
            <h2 id="home-actions-heading">Choose where to begin</h2>
          </div>
          <p>Each tool works with the study materials you add.</p>
        </div>

        <div className="home-action-grid">
          {studyActions.map((item, index) => (
            <button
              className={`home-action-card home-action-${item.tone}`}
              key={item.id}
              onClick={() => onNavigate(item.id)}
              style={{
                "--card-artwork": `url("${item.artwork}")`,
                "--card-index": index,
              }}
              type="button"
            >
              <span className="home-card-icon"><Icon name={item.icon} size={23} /></span>
              <span className="home-card-eyebrow">{item.eyebrow}</span>
              <strong>{item.title}</strong>
              <span className="home-card-description">{item.description}</span>
              <span className="home-card-link">{item.action}<span aria-hidden="true">→</span></span>
            </button>
          ))}
        </div>
      </section>

      <section className="home-kind-reminder" aria-label="Study reminder">
        <span className="home-reminder-mark" aria-hidden="true">☼</span>
        <div>
          <p className="home-eyebrow">A gentle reminder</p>
          <h2>Small, focused sessions still count.</h2>
          <p>Choose one topic, study it carefully, and check your understanding before moving on.</p>
        </div>
      </section>
    </div>
  );
}

export default Home;
