import Badge from "../ui/Badge.jsx";
import Button from "../ui/Button.jsx";
import Icon from "../ui/Icon.jsx";
import { getNavigationItem } from "./navigation.js";

function TopBar({ currentPage, onLogout, onOpenMenu, user }) {
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
          <p className="topbar-kicker">Knowledge workspace</p>
          <p className="topbar-title">{page.title}</p>
        </div>
      </div>

      <div className="topbar-actions">
        <Badge tone="accent">
          <span className="system-dot" aria-hidden="true" />
          Multi-agent learning
        </Badge>
        <div className="topbar-user">
          <span className="topbar-avatar" aria-hidden="true">
            {user.full_name.charAt(0).toUpperCase()}
          </span>
          <span className="topbar-user-copy">
            <strong>{user.full_name}</strong>
            <small>Private workspace</small>
          </span>
        </div>
        <Button onClick={onLogout}>Sign out</Button>
      </div>
    </header>
  );
}

export default TopBar;
