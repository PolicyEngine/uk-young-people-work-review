import { toCsv } from "../utils/measures";

// Downloads for one chart: the rows behind it as CSV (measure names as
// headers), and the drawn chart as SVG or PNG, as on the AB2026 dashboard.
function save(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function chartSvg(container) {
  const svg = container?.querySelector("svg.recharts-surface");
  if (!svg) return null;
  const copy = svg.cloneNode(true);
  copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  return new XMLSerializer().serializeToString(copy);
}

export default function ChartDownloadMenu({ rows, filename, labels, chartRef }) {
  const csv = () => save(new Blob([toCsv(rows, labels)], { type: "text/csv" }), `${filename}.csv`);
  const svg = () => {
    const text = chartSvg(chartRef?.current);
    if (text) save(new Blob([text], { type: "image/svg+xml" }), `${filename}.svg`);
  };
  const png = () => {
    const text = chartSvg(chartRef?.current);
    const svgElement = chartRef?.current?.querySelector("svg.recharts-surface");
    if (!text || !svgElement) return;
    const { width, height } = svgElement.getBoundingClientRect();
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width * 2;
      canvas.height = height * 2;
      const context = canvas.getContext("2d");
      context.fillStyle = getComputedStyle(document.body).backgroundColor || "white";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.scale(2, 2);
      context.drawImage(image, 0, 0, width, height);
      canvas.toBlob((blob) => blob && save(blob, `${filename}.png`));
    };
    image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}`;
  };
  const disabled = !rows?.length;
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Download">
      <button type="button" className="toggle-button" onClick={csv} disabled={disabled}>
        CSV
      </button>
      {chartRef && (
        <>
          <button type="button" className="toggle-button" onClick={svg} disabled={disabled}>
            SVG
          </button>
          <button type="button" className="toggle-button" onClick={png} disabled={disabled}>
            PNG
          </button>
        </>
      )}
    </div>
  );
}
