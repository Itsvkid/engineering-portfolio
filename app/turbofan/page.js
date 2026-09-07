import TurbofanAtlas from "./TurbofanAtlas";

const title = "Turbofan Atlas — a high-bypass turbofan, part by part";
const description =
  "Interactive 3D anatomy of a high-bypass turbofan: gas generator, fuel, control, air, oil, ignition, variable geometry, anti-icing, fire detection, vibration monitoring, exhaust and structure, built to the NASA/GE E³ published dimensions with every number sourced.";

export const metadata = {
  title,
  description,
  alternates: { canonical: "/turbofan" },
  openGraph: { title, description, type: "website", url: "/turbofan", images: [{ url: "/turbofan-og.png", width: 1200, height: 630, alt: "Cutaway of the turbofan atlas" }] },
  twitter: { card: "summary_large_image", title, description, images: ["/turbofan-og.png"] },
};

export default function TurbofanPage() {
  return <TurbofanAtlas />;
}
