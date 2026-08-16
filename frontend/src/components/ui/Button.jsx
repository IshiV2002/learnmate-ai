function Button({ children, className = "", icon, variant = "ghost", ...props }) {
  const iconOnly = !children;

  return (
    <button
      className={`ui-button ui-button-${variant} ${iconOnly ? "ui-button-icon" : ""} ${className}`.trim()}
      type="button"
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}

export default Button;
