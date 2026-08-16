function LibrarySkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading knowledge sources" aria-live="polite" className="vault-skeleton-grid" role="status">
      {[0, 1, 2].map((item) => (
        <div className="vault-source-skeleton" key={item}>
          <span className="skeleton-block skeleton-icon" />
          <div className="skeleton-copy">
            <span className="skeleton-block skeleton-kicker" />
            <span className="skeleton-block skeleton-title" />
            <span className="skeleton-block skeleton-detail" />
          </div>
          <div className="skeleton-metadata">
            <span className="skeleton-block" />
            <span className="skeleton-block" />
            <span className="skeleton-block" />
          </div>
        </div>
      ))}
      <span className="visually-hidden">Loading your materials.</span>
    </div>
  );
}

export default LibrarySkeleton;
