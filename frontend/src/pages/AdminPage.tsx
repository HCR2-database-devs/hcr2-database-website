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
  backupDownloadUrl,
  createBackup,
  deleteAdminRecord,
  deleteAdminNews,
  deleteBackup,
  getAdminRecords,
  getMaintenanceStatus,
  getPendingSubmissions,
  listBackups as listAdminBackups,
  postAdminNews,
  rejectPendingSubmission,
  runIntegrityCheck,
  setMaintenance,
  setRecordQuestionable,
  submitAdminRecord,
  updateAdminNews
} from "../services/admin";
import { getNews, getPublicData } from "../services/publicData";
import type { AdminRecord, DataRow, IntegrityStatus, NewsItem } from "../types/api";

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
  const id = text(row, "idTuningSetup", "idtuningsetup");
  if (Array.isArray(rawParts)) {
    const parts = rawParts
      .map((part) =>
        typeof part === "object" && part !== null && "nameTuningPart" in part
          ? String((part as { nameTuningPart: unknown }).nameTuningPart)
          : String(part)
      )
      .join(", ");
    return `Setup ${id}: ${parts}`;
  }
  const parts = text(row, "parts");
  return parts ? `Setup ${id}: ${parts}` : `Setup ${id}`;
}

function recordLabel(record: AdminRecord) {
  return `${record.distance} - ${record.map_name ?? "Unknown"} - ${
    record.vehicle_name ?? "Unknown"
  } - ${record.player_name ?? "Unknown"}`;
}

function optionalIcon(form: HTMLFormElement) {
  const icon = new FormData(form).get("icon");
  return icon instanceof File && icon.size > 0 ? icon : null;
}

export function AdminPage() {
  const queryClient = useQueryClient();
  const { data: authStatus, isLoading: authLoading } = useAuthStatus();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [recordForm, setRecordForm] = useState<RecordFormState>(emptyRecordForm);
  const [tuningSetupFilter, setTuningSetupFilter] = useState("");
  const [playerFilter, setPlayerFilter] = useState("");
  const [deleteRecordId, setDeleteRecordId] = useState("");
  const [deleteFilter, setDeleteFilter] = useState("");
  const [statusRecordId, setStatusRecordId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [statusValue, setStatusValue] = useState("");
  const [statusNote, setStatusNote] = useState("");
  const [assignRecordId, setAssignRecordId] = useState("");
  const [assignRecordFilter, setAssignRecordFilter] = useState("");
  const [assignSetupId, setAssignSetupId] = useState("");
  const [assignSetupFilter, setAssignSetupFilter] = useState("");
  const [mapName, setMapName] = useState("");
  const [vehicleName, setVehicleName] = useState("");
  const [partName, setPartName] = useState("");
  const [selectedPartIds, setSelectedPartIds] = useState<number[]>([]);
  const [newsTitle, setNewsTitle] = useState("");
  const [newsContent, setNewsContent] = useState("");
  const [editingNewsId, setEditingNewsId] = useState<number | null>(null);
  const [editingNewsTitle, setEditingNewsTitle] = useState("");
  const [editingNewsContent, setEditingNewsContent] = useState("");
  const [integrity, setIntegrity] = useState<IntegrityStatus | null>(null);
  const [backupMessage, setBackupMessage] = useState("");
  const [backupError, setBackupError] = useState("");

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
  const newsQuery = useQuery({ queryKey: ["news", 20], queryFn: () => getNews(20) });
  const backupsQuery = useQuery({ queryKey: ["admin", "backups"], queryFn: listAdminBackups });
  const maintenanceQuery = useQuery({
    queryKey: ["admin", "maintenance"],
    queryFn: getMaintenanceStatus
  });

  const tuningSetups = setupsQuery.data ?? [];
  const filteredTuningSetups = useMemo(
    () =>
      tuningSetups.filter((row) => setupLabel(row).toLowerCase().includes(tuningSetupFilter.toLowerCase())),
    [tuningSetups, tuningSetupFilter]
  );
  const filteredAssignTuningSetups = useMemo(
    () =>
      tuningSetups.filter((row) => setupLabel(row).toLowerCase().includes(assignSetupFilter.toLowerCase())),
    [tuningSetups, assignSetupFilter]
  );
  const filteredPlayers = useMemo(
    () =>
      (playersQuery.data ?? []).filter((row) =>
        text(row, "namePlayer", "nameplayer").toLowerCase().includes(playerFilter.toLowerCase())
      ),
    [playersQuery.data, playerFilter]
  );
  const filterRecordOptions = (records: AdminRecord[], filter: string) =>
    records.filter((record) => recordLabel(record).toLowerCase().includes(filter.toLowerCase()));

  const deleteRecords = useMemo(
    () => filterRecordOptions(recordsQuery.data ?? [], deleteFilter),
    [recordsQuery.data, deleteFilter]
  );
  const statusRecords = useMemo(
    () => filterRecordOptions(recordsQuery.data ?? [], statusFilter),
    [recordsQuery.data, statusFilter]
  );
  const recordsWithoutSetup = useMemo(
    () => filterRecordOptions((recordsQuery.data ?? []).filter((record) => !record.idTuningSetup), assignRecordFilter),
    [recordsQuery.data, assignRecordFilter]
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

  async function runBackupAction(action: () => Promise<unknown>, successMessage: string) {
    setBackupMessage("");
    setBackupError("");
    try {
      await action();
      setBackupMessage(successMessage);
      await backupsQuery.refetch();
    } catch (err) {
      setBackupError(err instanceof Error ? err.message : "Request failed");
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
      setStatusValue("");
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
    const form = event.currentTarget;
    const icon = optionalIcon(form);
    await runAction(async () => {
      await addMap(mapName, icon);
      setMapName("");
      form.reset();
    }, "Map added.");
  }

  async function handleAddVehicle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const icon = optionalIcon(form);
    await runAction(async () => {
      await addVehicle(vehicleName, icon);
      setVehicleName("");
      form.reset();
    }, "Vehicle added.");
  }

  async function handleAddPart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const icon = optionalIcon(form);
    await runAction(async () => {
      await addTuningPart(partName, icon);
      setPartName("");
      form.reset();
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

  function startEditingNews(item: NewsItem) {
    setEditingNewsId(item.id);
    setEditingNewsTitle(item.title);
    setEditingNewsContent(item.content);
  }

  function cancelEditingNews() {
    setEditingNewsId(null);
    setEditingNewsTitle("");
    setEditingNewsContent("");
  }

  async function handleUpdateNews(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingNewsId === null) {
      return;
    }
    await runAction(async () => {
      await updateAdminNews(editingNewsId, editingNewsTitle, editingNewsContent);
      cancelEditingNews();
    }, "News updated.");
  }

  async function handleDeleteNews(newsId: number) {
    const confirmed = window.confirm("Delete this news item?");
    if (!confirmed) {
      return;
    }
    await runAction(async () => {
      await deleteAdminNews(newsId);
      if (editingNewsId === newsId) {
        cancelEditingNews();
      }
    }, "News deleted.");
  }

  function togglePart(partId: number) {
    setSelectedPartIds((current) =>
      current.includes(partId) ? current.filter((id) => id !== partId) : [...current, partId]
    );
  }

  async function handleCreateBackup() {
    await runBackupAction(async () => {
      await createBackup();
    }, "Backup created.");
  }

  async function handleDownloadDb() {
    setBackupMessage("");
    setBackupError("");
    try {
      const result = await createBackup();
      await backupsQuery.refetch();
      setBackupMessage(`Fresh backup created: ${result.filename}`);
      window.location.href = backupDownloadUrl(result.filename);
    } catch (err) {
      setBackupError(err instanceof Error ? err.message : "Request failed");
    }
  }

  async function handleDeleteBackup(filename: string) {
    const confirmed = window.confirm(`Delete backup ${filename}?`);
    if (!confirmed) {
      return;
    }
    await runBackupAction(async () => {
      await deleteBackup(filename);
    }, "Backup deleted.");
  }

  function showImportUnsupported() {
    setBackupMessage("");
    setBackupError("SQL import and restore are intentionally disabled in the React admin because they are destructive PostgreSQL operations.");
  }

  if (authLoading) {
    return (
      <div className="admin-page">
        <div className="form-container">
          <h2>Admin</h2>
          <p>Checking access...</p>
        </div>
      </div>
    );
  }

  if (!authStatus?.allowed) {
    if (authStatus?.logged) {
      return (
        <div className="admin-page">
          <h1>403 Forbidden</h1>
          <p>You are logged in as {authStatus.username ?? authStatus.id}, but you are not an admin.</p>
        </div>
      );
    }

    return (
      <div className="admin-page">
        <div className="form-container">
          <h2>Admin</h2>
          <p className="frontend-error">You must be signed in with an authorized Discord account.</p>
          <button type="button" onClick={() => (window.location.href = "https://auth.hcr2.xyz/login")}>
            Sign in with Discord
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="topbar">
        <h1>Admin Panel</h1>
        <div>
          <span>Logged in as {authStatus.username ?? authStatus.id}</span>
          &nbsp;|&nbsp;<a href="/auth/logout.php">Logout</a>
          &nbsp;|&nbsp;<a href="/">Back to Public</a>
        </div>
      </div>

      {notice && <p className="admin-notice">{notice}</p>}
      {error && <p className="frontend-error">{error}</p>}

      <div className="form-container">
        <h2>Submit a New Record</h2>
        <form id="record-form" onSubmit={handleSubmitRecord}>
          <label>
            Map
            <select id="map-select" required value={recordForm.mapId} onChange={(event) => updateRecordForm("mapId", event.target.value)}>
              <option value="">Select a Map</option>
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
              id="vehicle-select"
              required
              value={recordForm.vehicleId}
              onChange={(event) => updateRecordForm("vehicleId", event.target.value)}
            >
              <option value="">Select a Vehicle</option>
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
              id="distance-input"
              required
              type="number"
              min="1"
              value={recordForm.distance}
              onChange={(event) => updateRecordForm("distance", event.target.value)}
            />
          </label>
          <label>
            Tuning Setup (optional)
            <input
              id="tuning-setup-filter"
              type="text"
              placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:magnet')..."
              value={tuningSetupFilter}
              onChange={(event) => setTuningSetupFilter(event.target.value)}
              className="stacked-control"
            />
            <select
              id="tuning-setup-select"
              value={recordForm.tuningSetupId}
              onChange={(event) => updateRecordForm("tuningSetupId", event.target.value)}
            >
              <option value="">No tuning setup</option>
              {filteredTuningSetups.map((row) => (
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
            <input
              id="player-filter"
              type="text"
              placeholder="Filter players..."
              value={playerFilter}
              onChange={(event) => setPlayerFilter(event.target.value)}
            />
            <select id="player-select" value={recordForm.playerId} onChange={(event) => updateRecordForm("playerId", event.target.value)}>
              <option value="">Select existing player</option>
              {filteredPlayers.map((row) => (
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
              id="new-player-input"
              type="text"
              value={recordForm.newPlayerName}
              onChange={(event) => updateRecordForm("newPlayerName", event.target.value)}
            />
          </label>
          <label>
            Country
            <input
              id="country-input"
              type="text"
              value={recordForm.country}
              onChange={(event) => updateRecordForm("country", event.target.value)}
            />
          </label>
          <label className="admin-inline">
            <input
              id="questionable-input"
              type="checkbox"
              checked={recordForm.questionable}
              onChange={(event) => updateRecordForm("questionable", event.target.checked)}
            />
            Mark as Questionable (TAS or uncertain legitimacy)
          </label>
          <label>
            Note (optional)
            <textarea
              id="questionable-reason-submit"
              placeholder="add any notes for record (shows for everyone)"
              value={recordForm.note}
              onChange={(event) => updateRecordForm("note", event.target.value)}
            />
          </label>
          <button type="submit">Submit Record</button>
        </form>
        <p id="form-message" />
      </div>

      <div className="form-container">
        <h2>Delete a Record</h2>
        <form id="delete-form" onSubmit={handleDeleteRecord}>
          <label>Filter Record</label>
          <input
            type="text"
            id="delete-filter"
            placeholder="Filter by distance, map, vehicle, or player..."
            value={deleteFilter}
            onChange={(event) => setDeleteFilter(event.target.value)}
          />
          <label>Record</label>
          <select id="record-select" required value={deleteRecordId} onChange={(event) => setDeleteRecordId(event.target.value)}>
            <option value="">Select a record</option>
            {deleteRecords.map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <button type="submit">Delete Record</button>
        </form>
        <p id="delete-message" />
      </div>

      <div className="form-container">
        <h2>Mark Records as Questionable</h2>
        <form id="questionable-form" onSubmit={handleSetStatus}>
          <label>Filter Record</label>
          <input
            type="text"
            id="questionable-filter-input"
            placeholder="Filter by distance, map, vehicle, or player..."
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          />
          <label>Record</label>
          <select id="questionable-record-select" required value={statusRecordId} onChange={(event) => setStatusRecordId(event.target.value)}>
            <option value="">Select a record</option>
            {statusRecords.map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {record.questionable === 1 ? "Questionable" : "Verified"} - {recordLabel(record)}
              </option>
            ))}
          </select>
          <label>Status</label>
          <select id="questionable-status-select" required value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
            <option value="">Select status</option>
            <option value="0">Mark as Verified</option>
            <option value="1">Mark as Questionable</option>
          </select>
          <label>Note (optional)</label>
          <textarea
            id="questionable-reason-input"
            placeholder="add any notes for records"
            value={statusNote}
            onChange={(event) => setStatusNote(event.target.value)}
          />
          <button type="submit">Update Status</button>
        </form>
        <p id="questionable-message" />
      </div>

      <div className="form-container">
        <h2>Assign Tuning Setup to Existing Record</h2>
        <form id="assign-setup-form" onSubmit={handleAssignSetup}>
          <label>Filter Record (without tuning setup)</label>
          <input
            type="text"
            id="assign-filter"
            placeholder="Filter by distance, map, vehicle, or player..."
            value={assignRecordFilter}
            onChange={(event) => setAssignRecordFilter(event.target.value)}
          />
          <label>Record (without tuning setup)</label>
          <select id="assign-record-select" required value={assignRecordId} onChange={(event) => setAssignRecordId(event.target.value)}>
            <option value="">Select a record without setup</option>
            {recordsWithoutSetup.map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <label>Tuning Setup</label>
          <input
            type="text"
            id="assign-tuning-setup-filter"
            placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:magnet')..."
            value={assignSetupFilter}
            onChange={(event) => setAssignSetupFilter(event.target.value)}
            className="stacked-control"
          />
          <select id="assign-tuning-setup-select" required value={assignSetupId} onChange={(event) => setAssignSetupId(event.target.value)}>
            <option value="">Select a setup</option>
            {filteredAssignTuningSetups.map((row) => (
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
        <p id="assign-message" />
      </div>

      <div className="form-container">
        <h2>Add a Vehicle</h2>
        <form id="add-vehicle-form" onSubmit={handleAddVehicle} encType="multipart/form-data">
          <label>Vehicle Name</label>
          <input id="vehicle-name-input" type="text" required placeholder="e.g., Jeep" value={vehicleName} onChange={(event) => setVehicleName(event.target.value)} />
          <label>Icon (SVG - optional)</label>
          <input id="vehicle-icon-input" name="icon" type="file" accept=".svg,image/svg+xml" />
          <small className="form-hint">
            Upload a .svg icon file. Will be saved as: vehicle_name.svg
          </small>
          <button type="submit">Add Vehicle</button>
        </form>
        <p id="add-vehicle-message" />
      </div>

      <div className="form-container">
        <h2>Add a Map</h2>
        <form id="add-map-form" onSubmit={handleAddMap} encType="multipart/form-data">
          <label>Map Name</label>
          <input id="map-name-input" type="text" required placeholder="e.g., Forest Trials" value={mapName} onChange={(event) => setMapName(event.target.value)} />
          <label>Icon (SVG - optional)</label>
          <input id="map-icon-input" name="icon" type="file" accept=".svg,image/svg+xml" />
          <small className="form-hint">
            Upload a .svg icon file. Will be saved as: map_name.svg
          </small>
          <button type="submit">Add Map</button>
        </form>
        <p id="add-map-message" />
      </div>

      <div className="form-container">
        <h2>Add Tuning Part</h2>
        <form id="add-tuning-part-form" onSubmit={handleAddPart} encType="multipart/form-data">
          <label>Tuning Part Name</label>
          <input id="tuning-part-name-input" type="text" required placeholder="e.g., Turbo" value={partName} onChange={(event) => setPartName(event.target.value)} />
          <label>Icon (SVG - optional)</label>
          <input id="tuning-part-icon-input" name="icon" type="file" accept=".svg,image/svg+xml" />
          <small className="form-hint">
            Upload a .svg icon file. Will be saved as: part_name.svg
          </small>
          <button type="submit">Add Tuning Part</button>
        </form>
        <p id="add-tuning-part-message" />
      </div>

      <div className="form-container">
        <h2>Add Tuning Setup</h2>
        <form id="add-tuning-setup-form" onSubmit={handleAddSetup}>
          <label>Select Tuning Parts (3-4)</label>
          <div id="tuning-parts-checkboxes" className="admin-checkboxes">
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
        <p id="add-tuning-setup-message" />
      </div>

      <div className="form-container" id="pending-submissions-container">
        <h2>Pending Submissions (from users)</h2>
        {pendingQuery.isLoading && <p>Loading...</p>}
        {(pendingQuery.data?.pending ?? []).length === 0 && <p>No pending submissions.</p>}
        {(pendingQuery.data?.pending ?? []).length > 0 && (
          <div id="pending-list" className="table-scroll">
            <table className="admin-pending-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Map</th>
                  <th>Vehicle</th>
                  <th>Distance</th>
                  <th>Player</th>
                  <th>Country</th>
                  <th>Tuning Parts</th>
                  <th>IP</th>
                  <th>When</th>
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
                    <td>{submission.playerCountry}</td>
                    <td>{submission.tuningParts}</td>
                    <td>{submission.submitterIp ?? ""}</td>
                    <td>{submission.submitted_at}</td>
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
                        className="button-ghost"
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

      <div className="form-container">
        <h2>Site News (Admins)</h2>
        <form id="news-form" onSubmit={handlePostNews}>
          <label>Title</label>
          <input id="news-title-input" type="text" required value={newsTitle} onChange={(event) => setNewsTitle(event.target.value)} />
          <label>Content</label>
          <textarea id="news-content-input" required rows={6} value={newsContent} onChange={(event) => setNewsContent(event.target.value)} />
          <div className="admin-actions">
            <button type="submit">Post News</button>
            <button type="button" onClick={() => newsQuery.refetch()} className="button-ghost">
              Refresh
            </button>
          </div>
        </form>
        <p id="news-message" />
        {editingNewsId !== null && (
          <form id="news-edit-form" className="admin-block" onSubmit={handleUpdateNews}>
            <h3 className="admin-subtitle">Edit News</h3>
            <label>Title</label>
            <input
              id="news-edit-title-input"
              type="text"
              required
              value={editingNewsTitle}
              onChange={(event) => setEditingNewsTitle(event.target.value)}
            />
            <label>Content</label>
            <textarea
              id="news-edit-content-input"
              required
              rows={6}
              value={editingNewsContent}
              onChange={(event) => setEditingNewsContent(event.target.value)}
            />
            <div className="admin-actions">
              <button type="submit">Save News</button>
              <button type="button" onClick={cancelEditingNews} className="button-ghost">
                Cancel
              </button>
            </div>
          </form>
        )}
        <div id="admin-news-list">
          {newsQuery.isLoading && <p>Loading news...</p>}
          {newsQuery.data?.news.map((item) => (
            <div className="news-item" key={item.id}>
              <h3>{item.title}</h3>
              <div className="frontend-muted">{item.created_at} - {item.author ?? ""}</div>
              <div className="frontend-pre-wrap">{item.content}</div>
              <div className="admin-actions admin-actions--compact">
                <button type="button" onClick={() => startEditingNews(item)} className="button-ghost">
                  Edit
                </button>
                <button type="button" onClick={() => handleDeleteNews(item.id)} className="button-ghost">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-container">
        <h2>Database & Backups</h2>
        <div className="admin-actions">
          <button type="button" onClick={handleDownloadDb}>
            Download DB
          </button>
          <button type="button" onClick={handleCreateBackup}>
            Create Backup
          </button>
          <button type="button" onClick={() => backupsQuery.refetch()} className="button-ghost">
            List Backups
          </button>
          <button
            type="button"
            onClick={() =>
              runBackupAction(async () => {
                setIntegrity(await runIntegrityCheck());
              }, "Integrity check completed.")
            }
            className="button-primary"
          >
            Integrity Check
          </button>
        </div>
        {backupMessage && <p className="admin-notice">{backupMessage}</p>}
        {backupError && <p className="frontend-error">{backupError}</p>}
        <div id="backups-list" className="admin-block">
          {backupsQuery.isLoading && <p>Loading...</p>}
          {!backupsQuery.isLoading && (backupsQuery.data?.backups ?? []).length === 0 && <p>No backups found.</p>}
          {(backupsQuery.data?.backups ?? []).length > 0 && (
            <table>
              <tbody>
                <tr>
                  <th>Name</th>
                  <th>Size</th>
                  <th>Modified</th>
                  <th>Actions</th>
                </tr>
                {(backupsQuery.data?.backups ?? []).map((backup) => (
                  <tr key={backup.name}>
                    <td>{backup.name}</td>
                    <td>{backup.size}</td>
                    <td>{backup.mtime}</td>
                    <td className="admin-table-actions">
                      <a className="admin-button-link" href={backupDownloadUrl(backup.name)}>
                        Download
                      </a>
                      <button type="button" onClick={() => handleDeleteBackup(backup.name)} className="button-ghost">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {integrity && <pre className="frontend-pre-wrap">{JSON.stringify(integrity.counts, null, 2)}</pre>}
        </div>
        <h3 className="admin-subtitle">Import SQL</h3>
        <form id="import-form" onSubmit={(event) => { event.preventDefault(); showImportUnsupported(); }} encType="multipart/form-data">
          <p className="form-hint">
            SQL import and restore are disabled here. Use reviewed database tooling for destructive restores.
          </p>
          <input type="file" name="sqlfile" accept=".sql" disabled />
          <div className="admin-actions">
            <button type="submit" disabled>
              Import SQL
            </button>
          </div>
          <p id="import-message" />
        </form>
      </div>

      <div className="form-container" id="maintenance-container">
        <h2>Maintenance Mode</h2>
        <p id="maintenance-status">
          {maintenanceQuery.data?.maintenance ? "MAINTENANCE: ON (admins only)" : "MAINTENANCE: OFF"}
        </p>
        <div className="admin-actions">
          <button type="button" onClick={() => runAction(() => setMaintenance("enable"), "Maintenance updated.")} id="maintenance-enable">
            Enable
          </button>
          <button
            type="button"
            onClick={() => runAction(() => setMaintenance("disable"), "Maintenance updated.")}
            id="maintenance-disable"
            className="button-ghost"
          >
            Disable
          </button>
          <button type="button" onClick={() => maintenanceQuery.refetch()} className="button-ghost">
            Refresh
          </button>
        </div>
        <p id="maintenance-message" />
      </div>
    </div>
  );
}
