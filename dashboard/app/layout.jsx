import { PolicyEngineShell } from "@policyengine/ui-kit/layout";
import "@policyengine/ui-kit/styles.css";
import localFont from "next/font/local";
import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import { SITE_HEADER_STYLES, SITE_NAV_ITEMS } from "../src/utils/siteNav";

import "./globals.css";
import "./siteHeader.css";

// Inter, committed with the page (fonts/, SIL Open Font License), as on the
// AB2026 dashboard: the build fetches nothing from a third party.
const inter = localFont({
  src: "./fonts/inter-latin-variable.woff2",
  weight: "100 900",
  style: "normal",
  display: "swap",
  variable: "--font-inter",
  adjustFontFallback: "Arial",
});

// noindex until the figures are final and signed off: here, and as an
// X-Robots-Tag header (next.config.mjs). CI checks the built HTML.
export const metadata = {
  title: "Young people and work review: costs and who would benefit | PolicyEngine",
  description:
    "Pre-release template. What the proposals of the independent review of young people and work would cost and who would benefit, from PolicyEngine UK microsimulation.",
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
};

export const viewport = { width: "device-width", initialScale: 1.0 };

export default function RootLayout({ children }) {
  return (
    <html lang="en-GB" className={inter.variable}>
      <body>
        {/* The PolicyEngine site header with policyengine.org's menu, which
            folds into a menu button on a phone (ui-kit PolicyEngineShell). */}
        <PolicyEngineShell country="uk" showFooter={false} headerProps={{ navItems: SITE_NAV_ITEMS, styles: SITE_HEADER_STYLES }}>
          {children}
          <PolicyEngineFooter />
        </PolicyEngineShell>
      </body>
    </html>
  );
}
