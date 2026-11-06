import { formatMillions, formatPounds } from "../utils/measures";

export const REGION_NAMES = {
  NORTH_EAST: "North East",
  NORTH_WEST: "North West",
  YORKSHIRE: "Yorkshire and the Humber",
  EAST_MIDLANDS: "East Midlands",
  WEST_MIDLANDS: "West Midlands",
  EAST_OF_ENGLAND: "East of England",
  LONDON: "London",
  SOUTH_EAST: "South East",
  SOUTH_WEST: "South West",
  WALES: "Wales",
  SCOTLAND: "Scotland",
  NORTHERN_IRELAND: "Northern Ireland",
};

const DEVOLUTION =
  "Universal Credit and National Insurance are reserved and apply across Great Britain (Northern Ireland runs a parallel system). Employment support, skills and the participation system are devolved, so measures on them apply in England only, and PIP measures in England and Wales.";

// Average change by ITL1 region and nation, for each measure. Present only
// once model mode has run; the coverage of each measure is on its card.
export default function RegionView({ measures }) {
  const withRegion = measures.filter((m) => m.region);
  return (
    <section className="panel mb-6">
      <h3 className="m-0 mb-1 text-lg font-semibold">By region and nation</h3>
      <p className="m-0 mb-4 text-sm text-slate-600">{DEVOLUTION}</p>
      {withRegion.length === 0 ? (
        <p className="m-0 text-sm text-slate-600" data-testid="region-pending">
          Figures by region and nation come from the full model on the day.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table compact">
            <thead>
              <tr>
                <th>Region or nation</th>
                {withRegion.map((m) => (
                  <th key={m.id}>{m.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(REGION_NAMES).map(([code, name]) => (
                <tr key={code}>
                  <td>{name}</td>
                  {withRegion.map((m) => {
                    const row = m.region.find((r) => r.region === code);
                    return (
                      <td key={m.id}>
                        {!row || row.avg_change_gbp === null ? "n/a" : `${formatPounds(row.avg_change_gbp)} a household (${formatMillions(row.total_change_m)})`}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
