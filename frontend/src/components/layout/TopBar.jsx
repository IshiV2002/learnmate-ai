import Button from "../ui/Button.jsx";
import Icon from "../ui/Icon.jsx";
import { getNavigationItem } from "./navigation.js";

function TopBar({ currentPage, onLogout, onNavigate, onOpenMenu, onToggleTheme, onViewPlans, theme, user }) {
  const page = getNavigationItem(currentPage);

  return (
    <header className="app-topbar">
      <div className="topbar-main">
        <Button
          aria-label="Open navigation menu"
          className="mobile-menu-button"
          icon={<Icon name="menu" />}
          onClick={onOpenMenu}
        />
        <div className="topbar-copy">
          <p className="topbar-kicker">Your study space</p>
          <p className="topbar-title">{page.title}</p>
        </div>
      </div>

      <div className="topbar-actions">
        <Button className="topbar-plans-button" onClick={onViewPlans}>Plans</Button>
        <Button
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          className="theme-toggle"
          icon={<Icon name={theme === "light" ? "moon" : "sun"} size={18} />}
          onClick={onToggleTheme}
          title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? "Dark" : "Light"}
        </Button>
        <button
          aria-label="Open my account"
          className="topbar-user"
          onClick={() => onNavigate("account")}
          type="button"
        >
          <span className="topbar-avatar" aria-hidden="true">
            {user.full_name.charAt(0).toUpperCase()}
          </span>
          <span className="topbar-user-copy">
            <strong>{user.full_name}</strong>
            <small>Student workspace</small>
          </span>
        </button>
        <Button onClick={onLogout}>Sign out</Button>
      </div>
    </header>
  );
}

export default TopBar;
