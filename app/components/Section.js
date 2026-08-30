import Reveal from "./Reveal";

/**
 * The shell every numbered section shares: a sticky label column (index +
 * title) beside the content column. Rules and whitespace do the separating —
 * there are no cards anywhere below this component.
 *
 * The top rule draws itself in from the left as the section enters view, and
 * the content column's direct children cascade rather than arriving together.
 * Both are CSS-only, keyed off the `is-visible` class Reveal sets.
 */
export default function Section({ index, title, id, children }) {
  const headingId = `${id}-heading`;

  return (
    <section id={id} aria-labelledby={headingId}>
      <Reveal>
        <span aria-hidden="true" className="rule" />
      </Reveal>

      <div className="mx-auto max-w-[70rem] px-6 py-16 md:px-10 lg:py-24">
        <div className="lg:grid lg:grid-cols-12 lg:gap-8">
          <div className="lg:col-span-4">
            <div className="lg:sticky lg:top-24">
              <Reveal delay={60}>
                <div className="flex items-baseline gap-3 lg:block">
                  <span className="t-label text-accent">{index}</span>
                  <span aria-hidden="true" className="t-label text-fg2 lg:hidden">
                    /
                  </span>
                  <h2 id={headingId} className="t-h2 text-fg0 lg:mt-2">
                    {title}
                  </h2>
                </div>
              </Reveal>
            </div>
          </div>

          <div className="mt-8 lg:col-span-8 lg:mt-0">
            <Reveal>
              <div className="stagger">{children}</div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
