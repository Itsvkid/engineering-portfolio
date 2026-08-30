import ProductGallery from "./ProductGallery";
import CadViewer from "./CadViewer";

/**
 * Section 02's body. Both blocks are optional and each hides itself when it has
 * no data, so this composes them and supplies a placeholder for the case where
 * neither has anything yet — the section is always on the page, so it always
 * has to say something.
 *
 * Adding a single entry to `products` or `cadModels` retires the placeholder
 * automatically; there is no flag to remember to unset.
 */
export default function CadGallery({ products, models, cvHref }) {
  const empty = !products?.length && !models?.length;

  if (!empty) {
    return (
      <>
        <ProductGallery products={products} />
        <CadViewer models={models} />
      </>
    );
  }

  return (
    <div>
      {/* Sized to its content rather than the 16:10 a real model needs: three
          lines of text in a full-height frame read as a failed load, not as a
          section awaiting content. The viewer takes the full aspect once there
          is geometry to put in it. */}
      <div className="w-full rounded-md border border-line bg-bg1 px-6 py-14 text-center">
        <p className="t-label text-fg2">CAD viewer</p>
        <p className="t-h4 mt-3 text-fg0">Models in preparation</p>
        <p className="t-body-sm mx-auto mt-2 max-w-sm text-fg2">
          Native CATIA V5 and STEP geometry, rendered in the browser — no
          plugin, no download.
        </p>
      </div>

      {/* A placeholder that only apologises wastes the slot. This one sends the
          reader to the work that does exist. */}
      <p className="t-body-sm mt-4 text-fg2">
        The geometry and simulation work behind these models is written up in{" "}
        <a href="#projects" className="link text-fg1">
          Projects
        </a>
        {cvHref ? (
          <>
            , and the full toolchain is on the{" "}
            <a
              href={cvHref}
              target="_blank"
              rel="noopener noreferrer"
              className="link text-fg1"
            >
              CV
            </a>
          </>
        ) : null}
        .
      </p>
    </div>
  );
}
