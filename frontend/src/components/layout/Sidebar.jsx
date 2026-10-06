import Icon from "../ui/Icon.jsx";
import Brand from "./Brand.jsx";
import Navigation from "./Navigation.jsx";

function Sidebar({ currentPage, onNavigate }) {
  return (
    <aside className="app-sidebar">
      <Brand onNavigate={onNavigate} />
      <p className="sidebar-context">My study space</p>
      <Navigation currentPage={currentPage} onNavigate={onNavigate} />

      <div className="sidebar-footer">
        <div className="sidebar-footer-label">
          <span className="system-dot" aria-hidden="true" />
          Ready when you are
        </div>
        <p>Keep your materials, practice and next study steps together.</p>
        <Icon name="network" size={18} />
      </div>
    </aside>
  );
}

export default Sidebar;
