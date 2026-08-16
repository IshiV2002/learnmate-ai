function Badge({ children, className = "", tone = "neutral" }) {
  return <span className={`ui-badge ui-badge-${tone} ${className}`.trim()}>{children}</span>;
}

export default Badge;
