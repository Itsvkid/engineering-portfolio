import Image from "next/image";

/**
 * Above-the-fold content rises on load rather than on scroll — a viewport
 * observer would fire immediately anyway. Each block carries its own
 * `--rise-delay` so the eye lands on the kicker, then the name, then the
 * supporting copy, in reading order. See globals.css §Motion 4.
 *
 * The turbine background lives at the layout level (fixed, behind the whole
 * page), not here — see app/layout.js.
 */
export default function Hero({ profile }) {
  const nameLines = profile.name.split(" ");

  return (
    <section className="mx-auto max-w-[70rem] px-6 pt-32 pb-18 md:px-10 lg:pt-48 lg:pb-28">
      {/* On mobile this is one ordered flex column (portrait first); at lg the
          `contents` wrappers become real grid columns. */}
      <div className="flex flex-col lg:grid lg:grid-cols-12 lg:gap-8">
        {/* Mobile drafting-sheet furniture, in normal flow rather than the
            fixed background layer — see the comment on DraftingMotion's own
            mobile tier for why: viewport-relative offsets broke on a short
            screen, real layout doesn't. `lg:hidden` because CadOverlay's
            equivalent title block takes over from `lg` up. */}
        <p
          aria-hidden="true"
          className="order-0 mb-2 text-center font-mono text-[8px] tracking-[0.08em] text-fg2 uppercase opacity-40 lg:hidden"
        >
          DWG — VK·TF001 · CORE SECTION
        </p>

        <div className="contents lg:col-span-8 lg:col-start-1 lg:row-start-1 lg:block">
          <div className="order-2 mt-6 lg:mt-0">
            <p className="rise t-label text-accent">{profile.kicker}</p>

            {/* break-words only engages below ~375px, where "Venkateshkumar"
                at the clamp floor is wider than the content box. */}
            <h1
              className="rise t-display mt-3 break-words text-fg0"
              style={{ "--rise-delay": "90ms" }}
            >
              {nameLines.map((line, i) => (
                <span key={i} className="block">
                  {line}
                </span>
              ))}
            </h1>

            <p
              className="rise mt-5 max-w-[34rem] text-[1.0625rem] leading-[1.6] text-fg1"
              style={{ "--rise-delay": "180ms" }}
            >
              {profile.tagline}
            </p>

            <p
              className="rise t-meta mt-6 uppercase text-fg2"
              style={{ "--rise-delay": "260ms" }}
            >
              {profile.location} · {profile.workAuth}
            </p>
          </div>

          <div
            className="rise order-4 mt-10 flex flex-wrap items-center gap-x-8 gap-y-4"
            style={{ "--rise-delay": "340ms" }}
          >
            <a
              href="#projects"
              className="cta rounded-sm bg-accent px-5 py-3 text-sm font-medium text-bg0 transition-colors duration-[var(--dur-fast)] hover:bg-accent-hover active:bg-accent-active"
            >
              View projects{" "}
              <span aria-hidden="true" className="arrow">
                →
              </span>
            </a>
            <a
              href={`mailto:${profile.email}`}
              className="link font-mono text-sm text-fg0"
            >
              {profile.email}
            </a>
          </div>
        </div>

        <div className="contents lg:col-span-3 lg:col-start-10 lg:row-start-1 lg:block">
          <div className="rise order-1" style={{ "--rise-delay": "60ms" }}>
            <Image
              src="/headshot.jpg"
              alt={`${profile.name}, black-and-white studio portrait`}
              width={640}
              height={640}
              priority
              sizes="(min-width: 64rem) 240px, 80px"
              className="size-20 rounded-md border border-line object-cover grayscale lg:size-60"
            />
          </div>

          {/* On mobile this reads as a continuation of the status line above
              it; at lg it becomes its own block under the portrait. */}
          <div
            className="rise order-3 mt-1.5 lg:mt-8"
            style={{ "--rise-delay": "300ms" }}
          >
            <p className="t-label flex items-center gap-2 text-accent">
              <span aria-hidden="true" className="inline-block size-1.5 rounded-full bg-accent" />
              {profile.availability}
            </p>
            <p className="t-label mt-2 text-fg2">{profile.seeking}</p>
          </div>
        </div>

        <p
          aria-hidden="true"
          className="order-5 mt-10 text-center font-mono text-[8px] tracking-[0.06em] text-fg2 uppercase opacity-30 lg:hidden"
        >
          STA 0 FAN · STA 30 COMB · STA 50 NOZ
        </p>
      </div>
    </section>
  );
}
