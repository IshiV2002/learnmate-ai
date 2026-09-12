import Icon from "../ui/Icon.jsx";
import Brand from "./Brand.jsx";
import Navigation from "./Navigation.jsx";

function Sidebar({ currentPage, onNavigate }) {
  return (
    <aside className="app-sidebar">
      <Brand onNavigate={onNavigate} />
      <p className="sidebar-context">Learning workspace</p>
      <Navigation currentPage={currentPage} onNavigate={onNavigate} />

      <div className="sidebar-footer">
        <div className="sidebar-footer-label">
          <span className="system-dot" aria-hidden="true" />
          Shared agent workspace
        </div>
        <p>Retrieval, tutoring, assessment, and study guidance in one connected space.</p>
        <Icon name="network" size={18} />
      </div>
    </aside>
  );
}

export default Sidebar;
