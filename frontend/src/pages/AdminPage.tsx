import { FormEvent, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuthStatus } from "../hooks/useAuthStatus";
import {
  addMap,
  addTuningPart,
  addTuningSetup,
  addVehicle,
  approvePendingSubmission,
  assignTuningSetup,
  deleteAdminRecord,
  getAdminRecords,
  getMaintenanceStatus,
  getPendingSubmissions,
  postAdminNews,
  rejectPendingSubmission,
  runIntegrityCheck,
  setMaintenance,
  setRecordQuestionable,
  submitAdminRecord
} from "../services/admin";
import { getPublicData } from "../services/publicData";
import type { AdminRecord, DataRow, IntegrityStatus } from "../types/api";

type RecordFormState = {
  mapId: string;
  vehicleId: string;
  distance: string;
  tuningSetupId: string;
  playerId: string;
  newPlayerName: string;
  country: string;
  questionable: boolean;
  note: string;
};

const emptyRecordForm: RecordFormState = {
  mapId: "",
  vehicleId: "",
  distance: "",
  tuningSetupId: "",
  playerId: "",
  newPlayerName: "",
  country: "",
  questionable: false,
  note: ""
};

function text(row: DataRow, ...keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (value !== undefined && value !== null) {
      return String(value);
    }
  }
  return "";
}

function numberValue(row: DataRow, ...keys: string[]) {
  const value = text(row, ...keys);
  return value === "" ? 0 : Number(value);
}

function setupLabel(row: DataRow) {
  const rawParts = row.parts;
  if (Array.isArray(rawParts)) {
    return rawParts
      .map((part) =>
        typeof part === "object" && part !== null && "nameTuningPart" in part
          ? String((part as { nameTuningPart: unknown }).nameTuningPart)
          : String(part)
      )
      .join(", ");
  }
  return text(row, "parts", "idTuningSetup", "idtuningsetup");
}

function recordLabel(record: AdminRecord) {
  return `${record.distance}m | ${record.map_name ?? "Unknown"} | ${
    record.vehicle_name ?? "Unknown"
  } | ${record.player_name ?? "Unknown"}`;
}

export function AdminPage() {
  const queryClient = useQueryClient();
  const { data: authStatus, isLoading: authLoading } = useAuthStatus();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [recordForm, setRecordForm] = useState<RecordFormState>(emptyRecordForm);
  const [deleteRecordId, setDeleteRecordId] = useState("");
  const [statusRecordId, setStatusRecordId] = useState("");
  const [statusValue, setStatusValue] = useState("0");
  const [statusNote, setStatusNote] = useState("");
  const [assignRecordId, setAssignRecordId] = useState("");
  const [assignSetupId, setAssignSetupId] = useState("");
  const [mapName, setMapName] = useState("");
  const [vehicleName, setVehicleName] = useState("");
  const [partName, setPartName] = useState("");
  const [selectedPartIds, setSelectedPartIds] = useState<number[]>([]);
  const [newsTitle, setNewsTitle] = useState("");
  const [newsContent, setNewsContent] = useState("");
  const [integrity, setIntegrity] = useState<IntegrityStatus | null>(null);

  const mapsQuery = useQuery({ queryKey: ["public-data", "maps"], queryFn: () => getPublicData("maps") });
  const vehiclesQuery = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles")
  });
  const playersQuery = useQuery({
    queryKey: ["public-data", "players"],
    queryFn: () => getPublicData("players")
  });
  const partsQuery = useQuery({
    queryKey: ["public-data", "tuning-parts"],
    queryFn: () => getPublicData("tuning-parts")
  });
  const setupsQuery = useQuery({
    queryKey: ["public-data", "tuning-setups"],
    queryFn: () => getPublicData("tuning-setups")
  });
  const recordsQuery = useQuery({ queryKey: ["admin", "records"], queryFn: getAdminRecords });
  const pendingQuery = useQuery({ queryKey: ["admin", "pending"], queryFn: getPendingSubmissions });
  const maintenanceQuery = useQuery({
    queryKey: ["admin", "maintenance"],
    queryFn: getMaintenanceStatus
  });

  const recordsWithoutSetup = useMemo(
    () => (recordsQuery.data ?? []).filter((record) => !record.idTuningSetup),
    [recordsQuery.data]
  );

  async function refreshAdminData() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin"] }),
      queryClient.invalidateQueries({ queryKey: ["public-data"] }),
      queryClient.invalidateQueries({ queryKey: ["news"] })
    ]);
  }

  async function runAction(action: () => Promise<unknown>, successMessage: string) {
    setNotice("");
    setError("");
    try {
      await action();
      setNotice(successMessage);
      await refreshAdminData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }

  function updateRecordForm<K extends keyof RecordFormState>(key: K, value: RecordFormState[K]) {
    setRecordForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmitRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await submitAdminRecord({
        mapId: Number(recordForm.mapId),
        vehicleId: Number(recordForm.vehicleId),
        distance: Number(recordForm.distance),
        tuningSetupId: recordForm.tuningSetupId ? Number(recordForm.tuningSetupId) : null,
        playerId: recordForm.playerId ? Number(recordForm.playerId) : null,
        newPlayerName: recordForm.newPlayerName || null,
        country: recordForm.country || null,
        questionable: recordForm.questionable ? 1 : 0,
        questionableReason: recordForm.note || null
      });
      setRecordForm(emptyRecordForm);
    }, "Record submitted.");
  }

  async function handleDeleteRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await deleteAdminRecord(Number(deleteRecordId));
      setDeleteRecordId("");
    }, "Record deleted.");
  }

  async function handleSetStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await setRecordQuestionable({
        recordId: Number(statusRecordId),
        questionable: Number(statusValue),
        note: statusNote || null
      });
      setStatusRecordId("");
      setStatusNote("");
    }, "Record status updated.");
  }

  async function handleAssignSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await assignTuningSetup({
        recordId: Number(assignRecordId),
        tuningSetupId: Number(assignSetupId)
      });
      setAssignRecordId("");
      setAssignSetupId("");
    }, "Tuning setup assigned.");
  }

  async function handleAddMap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await addMap(mapName);
      setMapName("");
    }, "Map added.");
  }

  async function handleAddVehicle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await addVehicle(vehicleName);
      setVehicleName("");
    }, "Vehicle added.");
  }

  async function handleAddPart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await addTuningPart(partName);
      setPartName("");
    }, "Tuning part added.");
  }

  async function handleAddSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await addTuningSetup(selectedPartIds);
      setSelectedPartIds([]);
    }, "Tuning setup added.");
  }

  async function handlePostNews(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await postAdminNews(newsTitle, newsContent);
      setNewsTitle("");
      setNewsContent("");
    }, "News posted.");
  }

  function togglePart(partId: number) {
    setSelectedPartIds((current) =>
      current.includes(partId) ? current.filter((id) => id !== partId) : [...current, partId]
    );
  }

  if (authLoading) {
    return (
      <section className="form-container admin-page">
        <h2>Admin</h2>
        <p>Checking access...</p>
      </section>
    );
  }

  if (!authStatus?.allowed) {
    return (
      <section className="form-container admin-page">
        <h2>Admin</h2>
        <p className="frontend-error">You must be signed in with an authorized Discord account.</p>
        <button type="button" onClick={() => (window.location.href = "https://auth.hcr2.xyz/login")}>
          Sign in with Discord
        </button>
      </section>
    );
  }

  return (
    <section className="admin-page">
      <h2>Admin</h2>
      {notice && <p className="admin-notice">{notice}</p>}
      {error && <p className="frontend-error">{error}</p>}

      <div className="admin-grid">
        <form className="form-container" onSubmit={handleSubmitRecord}>
          <h3>Submit or Replace Record</h3>
          <label>
            Map
            <select required value={recordForm.mapId} onChange={(event) => updateRecordForm("mapId", event.target.value)}>
              <option value="">Select a map</option>
              {(mapsQuery.data ?? []).map((row) => (
                <option key={numberValue(row, "idMap", "idmap")} value={numberValue(row, "idMap", "idmap")}>
                  {text(row, "nameMap", "namemap")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Vehicle
            <select
              required
              value={recordForm.vehicleId}
              onChange={(event) => updateRecordForm("vehicleId", event.target.value)}
            >
              <option value="">Select a vehicle</option>
              {(vehiclesQuery.data ?? []).map((row) => (
                <option
                  key={numberValue(row, "idVehicle", "idvehicle")}
                  value={numberValue(row, "idVehicle", "idvehicle")}
                >
                  {text(row, "nameVehicle", "namevehicle")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Distance
            <input
              required
              type="number"
              min="1"
              value={recordForm.distance}
              onChange={(event) => updateRecordForm("distance", event.target.value)}
            />
          </label>
          <label>
            Tuning Setup
            <select
              value={recordForm.tuningSetupId}
              onChange={(event) => updateRecordForm("tuningSetupId", event.target.value)}
            >
              <option value="">No setup</option>
              {(setupsQuery.data ?? []).map((row) => (
                <option
                  key={numberValue(row, "idTuningSetup", "idtuningsetup")}
                  value={numberValue(row, "idTuningSetup", "idtuningsetup")}
                >
                  {setupLabel(row)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Existing Player
            <select value={recordForm.playerId} onChange={(event) => updateRecordForm("playerId", event.target.value)}>
              <option value="">Select existing player</option>
              {(playersQuery.data ?? []).map((row) => (
                <option
                  key={numberValue(row, "idPlayer", "idplayer")}
                  value={numberValue(row, "idPlayer", "idplayer")}
                >
                  {text(row, "namePlayer", "nameplayer")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Or Add New Player
            <input
              type="text"
              value={recordForm.newPlayerName}
              onChange={(event) => updateRecordForm("newPlayerName", event.target.value)}
            />
          </label>
          <label>
            Country
            <input
              type="text"
              value={recordForm.country}
              onChange={(event) => updateRecordForm("country", event.target.value)}
            />
          </label>
          <label className="admin-inline">
            <input
              type="checkbox"
              checked={recordForm.questionable}
              onChange={(event) => updateRecordForm("questionable", event.target.checked)}
            />
            Mark as Questionable
          </label>
          <label>
            Note
            <textarea value={recordForm.note} onChange={(event) => updateRecordForm("note", event.target.value)} />
          </label>
          <button type="submit">Submit Record</button>
        </form>

        <form className="form-container" onSubmit={handleDeleteRecord}>
          <h3>Delete Record</h3>
          <select required value={deleteRecordId} onChange={(event) => setDeleteRecordId(event.target.value)}>
            <option value="">Select a record</option>
            {(recordsQuery.data ?? []).map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <button type="submit">Delete Record</button>
        </form>

        <form className="form-container" onSubmit={handleSetStatus}>
          <h3>Record Status</h3>
          <select required value={statusRecordId} onChange={(event) => setStatusRecordId(event.target.value)}>
            <option value="">Select a record</option>
            {(recordsQuery.data ?? []).map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
            <option value="0">Mark as Verified</option>
            <option value="1">Mark as Questionable</option>
          </select>
          <textarea value={statusNote} onChange={(event) => setStatusNote(event.target.value)} />
          <button type="submit">Update Status</button>
        </form>

        <form className="form-container" onSubmit={handleAssignSetup}>
          <h3>Assign Tuning Setup</h3>
          <select required value={assignRecordId} onChange={(event) => setAssignRecordId(event.target.value)}>
            <option value="">Select a record without setup</option>
            {recordsWithoutSetup.map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <select required value={assignSetupId} onChange={(event) => setAssignSetupId(event.target.value)}>
            <option value="">Select a setup</option>
            {(setupsQuery.data ?? []).map((row) => (
              <option
                key={numberValue(row, "idTuningSetup", "idtuningsetup")}
                value={numberValue(row, "idTuningSetup", "idtuningsetup")}
              >
                {setupLabel(row)}
              </option>
            ))}
          </select>
          <button type="submit">Assign Setup</button>
        </form>

        <form className="form-container" onSubmit={handleAddVehicle}>
          <h3>Add Vehicle</h3>
          <input required value={vehicleName} onChange={(event) => setVehicleName(event.target.value)} />
          <button type="submit">Add Vehicle</button>
        </form>

        <form className="form-container" onSubmit={handleAddMap}>
          <h3>Add Map</h3>
          <input required value={mapName} onChange={(event) => setMapName(event.target.value)} />
          <button type="submit">Add Map</button>
        </form>

        <form className="form-container" onSubmit={handleAddPart}>
          <h3>Add Tuning Part</h3>
          <input required value={partName} onChange={(event) => setPartName(event.target.value)} />
          <button type="submit">Add Tuning Part</button>
        </form>

        <form className="form-container" onSubmit={handleAddSetup}>
          <h3>Add Tuning Setup</h3>
          <div className="admin-checkboxes">
            {(partsQuery.data ?? []).map((row) => {
              const partId = numberValue(row, "idTuningPart", "idtuningpart");
              return (
                <label key={partId}>
                  <input
                    type="checkbox"
                    checked={selectedPartIds.includes(partId)}
                    onChange={() => togglePart(partId)}
                  />
                  {text(row, "nameTuningPart", "nametuningpart")}
                </label>
              );
            })}
          </div>
          <button type="submit">Add Tuning Setup</button>
        </form>
      </div>

      <div className="form-container">
        <h3>Pending Submissions</h3>
        {pendingQuery.isLoading && <p>Loading...</p>}
        {(pendingQuery.data?.pending ?? []).length === 0 && <p>No pending submissions.</p>}
        {(pendingQuery.data?.pending ?? []).length > 0 && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Map</th>
                  <th>Vehicle</th>
                  <th>Distance</th>
                  <th>Player</th>
                  <th>Tuning Parts</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {(pendingQuery.data?.pending ?? []).map((submission) => (
                  <tr key={submission.id}>
                    <td>{submission.id}</td>
                    <td>{submission.mapName}</td>
                    <td>{submission.vehicleName}</td>
                    <td>{submission.distance}</td>
                    <td>{submission.playerName}</td>
                    <td>{submission.tuningParts}</td>
                    <td className="admin-table-actions">
                      <button
                        type="button"
                        onClick={() =>
                          runAction(() => approvePendingSubmission(submission.id), "Submission approved.")
                        }
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          runAction(() => rejectPendingSubmission(submission.id), "Submission rejected.")
                        }
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="admin-grid">
        <form className="form-container" onSubmit={handlePostNews}>
          <h3>Site News</h3>
          <input required value={newsTitle} onChange={(event) => setNewsTitle(event.target.value)} />
          <textarea required rows={6} value={newsContent} onChange={(event) => setNewsContent(event.target.value)} />
          <button type="submit">Post News</button>
        </form>

        <div className="form-container">
          <h3>Maintenance Mode</h3>
          <p>{maintenanceQuery.data?.maintenance ? "MAINTENANCE: ON" : "MAINTENANCE: OFF"}</p>
          <div className="admin-actions">
            <button type="button" onClick={() => runAction(() => setMaintenance("enable"), "Maintenance enabled.")}>
              Enable
            </button>
            <button type="button" onClick={() => runAction(() => setMaintenance("disable"), "Maintenance disabled.")}>
              Disable
            </button>
          </div>
        </div>

        <div className="form-container">
          <h3>Database Integrity</h3>
          <button
            type="button"
            onClick={() =>
              runAction(async () => {
                setIntegrity(await runIntegrityCheck());
              }, "Integrity check completed.")
            }
          >
            Run Integrity Check
          </button>
          {integrity && (
            <pre className="frontend-pre-wrap">{JSON.stringify(integrity.counts, null, 2)}</pre>
          )}
        </div>
      </div>
    </section>
  );
}
