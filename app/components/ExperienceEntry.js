export default function ExperienceEntry({ entry }) {
  return (
    <article>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
        <h3 className="t-h4 text-fg0">{entry.org}</h3>
        <span className="t-meta shrink-0 uppercase text-fg2">{entry.period}</span>
      </div>

      <div className="mt-1 flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
        <p className="t-body-sm font-medium text-fg1">{entry.role}</p>
        <span className="t-meta shrink-0 uppercase text-fg2">
          {entry.location}
        </span>
      </div>

      <p className="t-meta mt-2 text-fg2">{entry.sub}</p>

      <div className="mt-6 space-y-3">
        {entry.points.map((point) => (
          <p key={point} className="t-body text-fg1">
            {point}
          </p>
        ))}
      </div>
    </article>
  );
}
