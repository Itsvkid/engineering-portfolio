import ContactForm from "./ContactForm";

export default function ContactSection({ profile }) {
  return (
    <div>
      <p className="t-h3 max-w-[30rem] text-fg0">
        Hiring for aircraft engine design, or need freelance CAD/CFD support?
        I reply within a day.
      </p>

      <a
        href={`mailto:${profile.email}`}
        className="link mt-8 inline-block break-words font-mono text-xl text-accent hover:text-accent-hover"
      >
        {profile.email}
      </a>

      <hr className="mt-10 border-t border-line" />

      <div className="mt-10">
        <ContactForm email={profile.email} cv={profile.cv} />
      </div>
    </div>
  );
}
