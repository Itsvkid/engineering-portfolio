export default function Footer({ profile }) {
  const links = [
    { label: "GitHub", href: profile.github, external: true },
    { label: "LinkedIn", href: profile.linkedin, external: true },
    { label: profile.phone, href: `tel:${profile.phone.replace(/\s/g, "")}` },
    { label: "CV — PDF", href: profile.cv, external: true },
  ];

  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-[70rem] flex-col gap-4 px-6 py-10 md:flex-row md:items-start md:justify-between md:px-10">
        <div className="t-meta uppercase text-fg2">
          <p>
            © {new Date().getFullYear()} {profile.name}
          </p>
          <p className="mt-1">
            Aircraft Engine Design · Parametric CAD · Freelance Available
          </p>
        </div>

        <ul className="t-meta flex flex-wrap gap-x-6 gap-y-2 uppercase [overflow-wrap:anywhere] md:justify-end">
          {links.map((link) => (
            <li key={link.label}>
              <a
                href={link.href}
                target={link.external ? "_blank" : undefined}
                rel={link.external ? "noopener noreferrer" : undefined}
                className="link text-fg1"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
