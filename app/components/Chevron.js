/**
 * Disclosure indicator — points down when collapsed, flips to point up
 * (rotate 180°) when open. `currentColor` so callers set state via text color.
 */
export default function Chevron({ open, className = "" }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      width="16"
      height="16"
      className={`shrink-0 transition-transform duration-[var(--dur-base)] ${
        open ? "rotate-180" : ""
      } ${className}`}
    >
      <path
        d="M4 6l4 4 4-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
