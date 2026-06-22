import type { DataRow } from "../../types/api";

type DataTableProps = {
  rows: DataRow[];
};

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "object" && item !== null && "nameTuningPart" in item) {
          return String((item as { nameTuningPart: unknown }).nameTuningPart);
        }
        return String(item);
      })
      .join(", ");
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

export function DataTable({ rows }: DataTableProps) {
  if (rows.length === 0) {
    return <p>No data available.</p>;
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={String(
                row.idRecord ??
                  row.idrecord ??
                  row.idMap ??
                  row.idmap ??
                  row.idVehicle ??
                  row.idvehicle ??
                  row.idPlayer ??
                  row.idplayer ??
                  index
              )}
            >
              {columns.map((column) => (
                <td key={column}>{formatValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
