import Link from "next/link";
import FigureImage from "./FigureImage";
import Reveal from "./Reveal";

/**
 * The atlas, directly under the hero: one poster, one claim, one button.
 * It is the strongest thing on the site and it lives on its own route, so
 * without this a visitor scanning the home page would never see it. The
 * poster is a still from the atlas itself (rendered with ?ui=0), shipped
 * in both schemes like every other figure on the page.
 */

const poster = {
  src: "/figures/turbofan-atlas-cutaway-dark.png",
  srcLight: "/figures/turbofan-atlas-cutaway.png",
  alt: "Cutaway of a high-bypass turbofan seen from the front quarter: fan, booster, ten-stage compressor, double-annular combustor, two-stage HP and five-stage LP turbine, with fuel, oil, air, control, ignition and fire-detection hardware drawn around the core in colour.",
};

// Provenance, not effort. An earlier version led with part and triangle
// counts, which read as a web-development statistic on a design portfolio.
const stats = [
  { value: "12", label: "engine systems, 142 parts" },
  { value: "67", label: "published stations, to scale" },
  { value: "0", label: "numbers without a source" },
];

export default function FeaturedAtlas() {
  return (
    <section aria-labelledby="atlas-heading" className="mx-auto max-w-[70rem] px-6 pb-16 md:px-10 lg:pb-24">
      <Reveal>
        <div className="overflow-hidden rounded-md border border-line bg-bg1">
          <Link href="/turbofan" className="group relative block aspect-[16/10] sm:aspect-[2/1]" aria-label="Open the Turbofan Atlas">
            <FigureImage figure={poster} sizes="(min-width: 1120px) 1120px, 100vw" className="object-cover transition-transform duration-[var(--dur-slow)] group-hover:scale-[1.015]" priority />
            <span aria-hidden="true" className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-bg1 to-transparent" />
            <span className="t-label absolute left-6 top-5 rounded-sm bg-bg0/80 px-2 py-1 text-accent backdrop-blur-sm sm:left-8">
              Featured · interactive
            </span>
          </Link>

          <div className="grid gap-6 p-6 sm:p-8 md:grid-cols-12 md:gap-8">
            <div className="md:col-span-7">
              <h2 id="atlas-heading" className="t-h3 text-fg0">
                Turbofan Atlas
              </h2>
              <p className="t-body mt-3 text-fg1">
                A high-bypass turbofan, part by part, reconstructed from the NASA/GE E³ design reports. The flowpath is drawn to the
                dimensions those reports publish, the compressor and turbine blades are lofted from their own printed section tables,
                and all twelve systems are there: fuel, control, air, oil, ignition, variable geometry, anti-icing, fire detection,
                vibration monitoring, exhaust and structure. Every number carries the page it came from, or is flagged as assumed.
                The engine is NASA&rsquo;s, not mine. Reading it accurately is the work.
              </p>
              <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2">
                <Link href="/turbofan" className="rounded-sm bg-accent px-4 py-2 font-mono text-[0.75rem] font-medium uppercase tracking-[0.06em] text-bg0 transition-colors duration-[var(--dur-fast)] hover:bg-accent-hover active:bg-accent-active">
                  Open the atlas
                </Link>
                <Link href="/turbofan?tour=air" className="cta t-label text-accent transition-colors duration-[var(--dur-fast)] hover:text-accent-hover">
                  Follow the air{" "}
                  <span aria-hidden="true" className="arrow">
                    →
                  </span>
                </Link>
                <Link href="/turbofan?tour=fuel" className="cta t-label text-accent transition-colors duration-[var(--dur-fast)] hover:text-accent-hover">
                  Follow the fuel{" "}
                  <span aria-hidden="true" className="arrow">
                    →
                  </span>
                </Link>
              </div>
            </div>
            <dl className="flex flex-col gap-3 md:col-span-5 md:flex-row md:flex-wrap md:gap-x-8 md:gap-y-4">
              {stats.map((s) => (
                <div key={s.label} className="flex flex-col-reverse">
                  <dt className="t-meta text-fg2">{s.label}</dt>
                  <dd className="font-mono text-2xl text-fg0">{s.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
