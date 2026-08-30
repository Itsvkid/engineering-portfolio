import Image from "next/image";

/**
 * A figure image that may carry a second file for light mode.
 *
 * A PNG cannot recolour itself, so a plot generated on a dark ground glares on
 * a light page and vice versa. Where `srcLight` is present both renders ship
 * and CSS shows one; the swap is defined in globals.css against the same media
 * query the palette uses. Only the visible one is described — the alternate is
 * `aria-hidden`, so a screen reader hears the figure once rather than twice.
 */
export default function FigureImage({ figure, sizes, className = "", priority }) {
  if (!figure.srcLight) {
    return (
      <Image
        src={figure.src}
        alt={figure.alt}
        fill
        sizes={sizes}
        className={className}
        priority={priority}
      />
    );
  }

  return (
    <>
      <Image
        src={figure.src}
        alt={figure.alt}
        fill
        sizes={sizes}
        className={`fig-dark ${className}`}
        priority={priority}
      />
      <Image
        src={figure.srcLight}
        alt=""
        aria-hidden="true"
        fill
        sizes={sizes}
        className={`fig-light ${className}`}
        priority={priority}
      />
    </>
  );
}
