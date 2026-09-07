import {
  profile,
  skills,
  projects,
  products,
  cadModels,
  experience,
  education,
  certifications,
} from "./data";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Section from "./components/Section";
import ProjectEntry from "./components/ProjectEntry";
import CadGallery from "./components/CadGallery";
import ExperienceEntry from "./components/ExperienceEntry";
import EducationEntry from "./components/EducationEntry";
import ToolchainList from "./components/ToolchainList";
import ContactSection from "./components/ContactSection";
import Footer from "./components/Footer";

const NAV = [
  { href: "#projects", label: "Projects" },
  { href: "#cad", label: "CAD" },
  { href: "#experience", label: "Experience" },
  { href: "#education", label: "Education" },
  { href: "#toolchain", label: "Toolchain" },
  { href: "#contact", label: "Contact" },
  { href: "/turbofan", label: "Turbofan atlas" },
];

// Sections are numbered by position rather than hardcoded, so reordering or
// inserting one cannot leave the sequence with a hole in it.
const order = [
  "projects",
  "cad",
  "experience",
  "education",
  "toolchain",
  "contact",
];
const num = (id) => String(order.indexOf(id) + 1).padStart(2, "0");

export default function Home() {
  return (
    <>
      <a
        href="#top"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-60 focus:rounded-sm focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-bg0"
      >
        Skip to content
      </a>

      <Nav items={NAV} cvHref={profile.cv} wordmark="Vinaykumar V." />

      <main id="top">
        <Hero profile={profile} />

        <Section index={num("projects")} title="Projects" id="projects">
          {projects.map((project, i) => (
            <div
              key={project.title}
              className="rounded-md border border-line bg-bg1 p-6 not-first:mt-6 sm:p-8"
            >
              <ProjectEntry
                project={project}
                index={`${num("projects")}·${String.fromCharCode(65 + i)}`}
                defaultOpen={i === 0}
              />
            </div>
          ))}
        </Section>

        <Section index={num("cad")} title="CAD Gallery" id="cad">
          <CadGallery
            products={products}
            models={cadModels}
            cvHref={profile.cv}
          />
        </Section>

        <Section index={num("experience")} title="Experience" id="experience">
          {experience.map((entry) => (
            <div
              key={entry.org}
              className="rounded-md border border-line bg-bg1 p-6 not-first:mt-6 sm:p-8"
            >
              <ExperienceEntry entry={entry} />
            </div>
          ))}
        </Section>

        <Section index={num("education")} title="Education" id="education">
          {education.map((entry) => (
            <div
              key={entry.school}
              className="rounded-md border border-line bg-bg1 p-6 not-first:mt-6 sm:p-8"
            >
              <EducationEntry entry={entry} />
            </div>
          ))}
        </Section>

        <Section index={num("toolchain")} title="Toolchain" id="toolchain">
          <ToolchainList skills={skills} certifications={certifications} />
        </Section>

        <Section index={num("contact")} title="Contact" id="contact">
          <ContactSection profile={profile} />
        </Section>
      </main>

      <Footer profile={profile} />
    </>
  );
}
