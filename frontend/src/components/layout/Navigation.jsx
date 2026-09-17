import Icon from "../ui/Icon.jsx";
import { navigationItems } from "./navigation.js";

function Navigation({ currentPage, onNavigate }) {
  return (
    <nav aria-label="Main navigation" className="app-nav">
      {navigationItems.map((item) => {
        const isActive = currentPage === item.id;

        return (
          <button
            aria-current={isActive ? "page" : undefined}
            className={`app-nav-item ${isActive ? "app-nav-item-active" : ""}`}
            key={item.id}
            onClick={() => onNavigate(item.id)}
            type="button"
          >
            <span className="nav-icon-box">
              <Icon name={item.icon} size={19} />
            </span>
            <span className="nav-copy">
              <strong>{item.label}</strong>
              <small>{item.description}</small>
            </span>
            <span className="nav-current-dot" aria-hidden="true" />
          </button>
        );
      })}
    </nav>
  );
}

export default Navigation;
