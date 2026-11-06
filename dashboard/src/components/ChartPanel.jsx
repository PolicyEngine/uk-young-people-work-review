import { useRef } from "react";
import ChartDownloadMenu from "./ChartDownloadMenu";

export default function ChartPanel({ title, subtitle, rows, filename, labels, children, moreInfo, controls }) {
  const chartRef = useRef(null);
  return (
    <section className="panel mb-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="m-0 text-lg font-semibold text-slate-800">{title}</h3>
          {subtitle && <p className="m-0 mt-1 text-sm text-slate-500">{subtitle}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {controls}
          {rows && <ChartDownloadMenu rows={rows} filename={filename} labels={labels} chartRef={chartRef} />}
        </div>
      </div>
      <div ref={chartRef}>{children}</div>
      {moreInfo && (
        <details className="mt-4 text-sm text-slate-600">
          <summary className="cursor-pointer">More on this chart</summary>
          <p className="mt-2">{moreInfo}</p>
        </details>
      )}
    </section>
  );
}
