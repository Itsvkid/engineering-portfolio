# CAD viewer

> **Autodesk Viewer cannot be embedded.** Verified from its response headers:
> `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'self'
> *.autodesk.com`. A browser will refuse to frame it anywhere but Autodesk's
> own domain, and no iframe attribute changes a policy set by the other origin.
>
> The site therefore renders a **self-hosted `.glb`** through `ModelViewer`, and
> links out to Autodesk where a model is also hosted there. Upload to Autodesk
> if you want the native-CAD view as a link — the sections below still apply to
> getting that link — but the in-page viewer comes from `public/models/`.

## Original notes — Autodesk Viewer setup

The CAD gallery's viewer embeds [viewer.autodesk.com](https://viewer.autodesk.com/designviews).
Nothing is stored in this repo: you upload the model to Autodesk, share it, and
paste two URLs into `app/data.js`.

## Why this and not a `.glb`

The site already has a `.glb` viewer (`ModelViewer`, used inside a project entry
— see `public/models/README.md`). The two are for different things:

| | `ModelViewer` (.glb) | `CadViewer` (Autodesk) |
|---|---|---|
| Input | Mesh, tessellated from B-rep | **Native CAD** — CATPart, STEP, IPT, SLDPRT, … |
| Fidelity | Silhouette approximated by triangles | Exact geometry as designed |
| Hosting | This repo, counts against the deploy | Autodesk's, costs the repo nothing |
| Works offline | Yes | No |
| Model tree / units | Lost in export | Preserved |

For a CAD portfolio the Autodesk route is usually the honest one: a reviewer
sees the real part, not a mesh you approximated for the web. Use the `.glb`
viewer when you want the geometry inline in a project narrative and you are
happy to tessellate it.

## Getting the URLs

1. Go to <https://viewer.autodesk.com> and sign in — a free Autodesk account is
   enough. There is no cost for this viewer.
2. Upload your CAD file. Autodesk translates it server-side; large assemblies
   can take a few minutes.
3. Share it **publicly**. An unshared model will not load for visitors, and an
   embed of it shows a sign-in wall instead of the part.
4. Take the two URLs from the share and embed options:
   - the **embed** snippet is an `<iframe>` — copy the value of its `src`
     attribute only, not the whole tag → this is `embedUrl`
   - the plain **share link** → this is `href`, used for the "Open full viewer"
     fallback

Autodesk revises this UI periodically, so the exact button labels may differ
from the above; the two artefacts you need are always a share link and an embed
snippet.

## Wiring it up

```js
// app/data.js
export const cadModels = [
  {
    title: "Nacelle assembly",
    format: "CATIA V5 · .CATPart",
    embedUrl: "https://viewer.autodesk.com/embed/<id>",
    href: "https://viewer.autodesk.com/<id>",
    description: "Parametric nacelle assembly, fan cowl driven by the iCST section definition.",
  },
];
```

With more than one entry the viewer grows a model switcher above the frame; the
frame itself stays single. Order them strongest first.

## How it behaves

- **Click to load.** The iframe is not requested until a visitor presses "Load
  3D viewer". Autodesk ships several MB and sets its own cookies, so nobody pays
  for the viewer unless they ask for it — the same bargain `ModelViewer` strikes
  with three.js, made explicit because this request leaves our origin.
- **Switching models** remounts the iframe rather than swapping the document
  under a live session.
- **Not keyboard-operable.** The canvas belongs to Autodesk, so the caption
  below carries the description and the "Open full viewer" escape hatch. That
  link is the accessible equivalent, not decoration — keep the description
  meaningful.

## Things that will bite you

- **A model that stops being shared stops rendering.** The frame will show
  Autodesk's own error, not ours. If you clean up your Autodesk files, check
  the site.
- **Free-tier share links are not a permanent archive.** Treat the URLs in
  `data.js` as something to re-verify occasionally, and keep the source CAD.
- **No Content-Security-Policy is set on this site today.** If one is ever
  added, it needs a `frame-src` entry for `viewer.autodesk.com` or the viewer
  will silently fail to frame.
