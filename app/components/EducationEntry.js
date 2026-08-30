function DefinitionRow({ term, children }) {
  return (
    <div className="flex flex-col gap-1 md:flex-row md:gap-6">
      <dt className="t-label shrink-0 text-fg2 md:w-22 md:pt-1">{term}</dt>
      <dd className="text-[0.8125rem] leading-[1.7] text-fg1">{children}</dd>
    </div>
  );
}

export default function EducationEntry({ entry }) {
  return (
    <article>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
        <h3 className="t-h4 text-fg0">{entry.school}</h3>
        <span className="t-meta flex shrink-0 items-center gap-2 uppercase text-fg2">
          {entry.period}
          {entry.current ? (
            <span
              aria-hidden="true"
              className="inline-block size-1.5 shrink-0 rounded-full bg-accent"
            />
          ) : null}
        </span>
      </div>

      <div className="mt-1 flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
        <p className="t-body-sm font-medium text-fg1">{entry.degree}</p>
        <span className="t-meta shrink-0 uppercase text-fg2">
          {entry.location}
        </span>
      </div>

      <dl className="mt-6 space-y-3">
        <DefinitionRow term="Modules">{entry.modules.join(" · ")}</DefinitionRow>
        {entry.note ? (
          <DefinitionRow term="Thesis">{entry.note}</DefinitionRow>
        ) : null}
      </dl>
    </article>
  );
}
