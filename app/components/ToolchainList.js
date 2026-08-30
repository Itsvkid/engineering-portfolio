function Row({ term, children, className = "" }) {
  return (
    <div
      className={`flex flex-col gap-2 border-b border-line py-5 first:pt-0 last:border-b-0 last:pb-0 md:flex-row md:gap-8 ${className}`}
    >
      <dt className="t-label shrink-0 text-fg2 md:w-44 md:pt-1">{term}</dt>
      <dd className="t-body-sm w-full text-fg1">{children}</dd>
    </div>
  );
}

export default function ToolchainList({ skills, certifications }) {
  return (
    <dl className="stagger">
      {skills.map((group) => (
        <Row key={group.group} term={group.group}>
          {group.items.join(" · ")}
        </Row>
      ))}

      {/* credentials are a sub-group, not another toolchain row — 48px clearance */}
      <Row term="Credentials" className="pt-12">
        <ul className="space-y-2">
          {certifications.map((cert) => (
            <li
              key={cert.title}
              className="flex flex-col gap-x-6 gap-y-0.5 sm:flex-row sm:items-baseline sm:justify-between"
            >
              <span>
                {cert.title} — {cert.detail}
              </span>
              <span className="t-meta shrink-0 text-fg2">{cert.year}</span>
            </li>
          ))}
        </ul>
      </Row>
    </dl>
  );
}
