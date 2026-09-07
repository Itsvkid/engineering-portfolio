"use client";

import dynamic from "next/dynamic";

/**
 * three.js, R3F, drei and the BVH land in this chunk. `ssr: false` because
 * there is no WebGL on the server, and it has to be requested from a Client
 * Component (Next 16 rejects it in a Server Component).
 */
const Atlas = dynamic(() => import("./atlas/Atlas"), {
  ssr: false,
  loading: () => (
    <div className="fixed inset-0 grid place-items-center bg-bg0">
      <p className="t-label text-fg2">Loading the atlas…</p>
    </div>
  ),
});

export default function TurbofanAtlas() {
  return <Atlas />;
}
