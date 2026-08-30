import "./globals.css";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import EngineeringBackground from "./components/EngineeringBackground";
import CadOverlay from "./components/CadOverlay";

const geist = Geist({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-geist-mono",
  display: "swap",
});

const title =
  "Vinaykumar Venkateshkumar — Aeronautical Engineer, Aircraft Engine Design";
const description =
  "Portfolio of Vinaykumar Venkateshkumar — an aeronautical engineer working toward aircraft engine design, fluent in CAD, Python, parametric geometry and CFD analysis, and open to freelance parametric-CAD and simulation work.";
const socialDescription =
  "Aeronautical engineer, aircraft engine design — fluent in CAD, Python, parametric geometry and CFD analysis. Open to freelance CAD/CFD work.";

export const metadata = {
  metadataBase: new URL("https://vinaykumar.is-a.dev"),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    title,
    description: socialDescription,
    type: "website",
    url: "/",
    siteName: "Vinaykumar Venkateshkumar",
    images: ["/headshot.jpg"],
  },
  twitter: {
    card: "summary",
    title,
    description: socialDescription,
    images: ["/headshot.jpg"],
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <head>
        {/* Arms the reveal animation's initial hidden state before first paint,
            and applies a stored manual theme override before paint so a
            returning visitor never sees a flash of the system-default scheme.
            Without JS the class/attribute are never set and the page falls
            back to prefers-color-scheme, which still renders correctly. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "document.documentElement.classList.add('js');" +
              "try{var t=localStorage.getItem('theme');" +
              "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);" +
              "}catch(e){}",
          }}
        />
      </head>
      <body className="bg-bg0 font-sans text-fg1 antialiased">
        <CadOverlay />
        <EngineeringBackground />
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
