function AmbientBackground() {
  return (
    <div className="ambient-layer" aria-hidden="true">
      <div className="ambient-grid" />
      <div className="ambient-aurora ambient-aurora-one" />
      <div className="ambient-aurora ambient-aurora-two" />
      <span className="network-line network-line-one" />
      <span className="network-line network-line-two" />
      <span className="network-node network-node-one" />
      <span className="network-node network-node-two" />
      <span className="network-node network-node-three" />
    </div>
  );
}

export default AmbientBackground;
