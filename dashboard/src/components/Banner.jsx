// Shown on every view while the results file is a placeholder or a mock,
// and on every view of a drill build (NEXT_PUBLIC_MOCK=1), whatever the
// results file or the measure flags say. The page also carries noindex
// (app/layout.jsx and the X-Robots-Tag header in next.config.mjs).
export const MOCK_BUILD = process.env.NEXT_PUBLIC_MOCK === "1";
export const MOCK_TEXT = "MOCK: drill figures from an invented report, not PolicyEngine estimates";

export function bannerFor(data, mockBuild = MOCK_BUILD) {
  if (mockBuild || data.status === "mock") {
    return { kind: "mock", text: data.status === "mock" && data.banner ? data.banner : MOCK_TEXT };
  }
  if (data.status === "placeholder") return { kind: "placeholder", text: data.banner };
  return null;
}

export default function Banner({ banner }) {
  if (!banner) return null;
  return (
    <div role="alert" className={`placeholder-banner ${banner.kind}`} data-testid={`${banner.kind}-banner`}>
      <strong>{banner.text}</strong>
    </div>
  );
}
