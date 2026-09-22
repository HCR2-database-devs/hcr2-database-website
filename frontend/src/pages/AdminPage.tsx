import { FormEvent, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ActivityLogPanel } from "../components/ActivityLogPanel";
import { CommunityAdminPanel } from "../components/CommunityAdminPanel";
import { FormattedText } from "../components/FormattedText";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { formatDate, MapWithIcon, TuningPartWithIcon, VehicleWithIcon } from "../lib/legacyDisplay";
import {
  addMap,
  addTuningPart,
  addTuningSetup,
  addVehicle,
  approvePendingSubmission,
  assignTuningSetup,
  backupDownloadUrl,
  createBackup,
  createBan,
  deleteAdminRecord,
  deleteAdminChangelog,
  deleteAdminNews,
  deleteBackup,
  getAdminRecords,
  getAdminLongestRecord,
  getMaintenanceStatus,
  getPendingSubmissions,
  listBans,
  listBackups as listAdminBackups,
  postAdminChangelog,
  postAdminNews,
  rejectPendingSubmission,
  runIntegrityCheck,
  setLongestRecord as setLongestRecordAdmin,
  clearLongestRecord as clearLongestRecordAdmin,
  setMaintenance,
  setRecordQuestionable,
  submitAdminRecord,
  unbanPlayer,
  updateAdminChangelog,
  updateAdminNews
} from "../services/admin";
import { getChangelog, getNews, getPublicData } from "../services/publicData";
import type {
  AdminRecord,
  BanEntry,
  ChangelogItem,
  DataRow,
  IntegrityStatus,
  NewsItem
} from "../types/api";

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  const digits = value >= 100 || index === 0 ? 0 : 1;
  return `${value.toFixed(digits)} ${units[index]}`;
}

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

const ECHO_PART_ID = 26;
const ECHO_EXCLUDED_PART_IDS = new Set([26, 2, 14, 13, 7, 18, 16, 17, 25]);

type AdminTab = "records" | "catalog" | "submissions" | "content" | "community" | "system";

const ADMIN_TABS: { id: AdminTab; label: string }[] = [
  { id: "records", label: "Records" },
  { id: "catalog", label: "Catalog" },
  { id: "submissions", label: "Submissions" },
  { id: "content", label: "Content" },
  { id: "community", label: "Community" },
  { id: "system", label: "System" }
];

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

function setupPartNames(row: DataRow): string[] {
  const rawParts = row.parts;
  if (Array.isArray(rawParts)) {
    return rawParts
      .map((part) =>
        typeof part === "object" && part !== null && "nameTuningPart" in part
          ? String((part as { nameTuningPart: unknown }).nameTuningPart)
          : String(part)
      )
      .map((name) => name.toLowerCase());
  }
  return String(row.parts ?? "")
    .split(",")
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);
}

function parsePartTerms(rest: string): string[] {
  return rest
    .split(",")
    .map((term) => term.trim().toLowerCase())
    .filter(Boolean);
}

function matchesPartTerms(names: string[], terms: string[]): boolean {
  return terms.every((term) => names.some((name) => name.includes(term)));
}

function matchesSetupFilter(row: DataRow, filter: string): boolean {
  const query = filter.trim().toLowerCase();
  if (!query) return true;
  if (query.startsWith("part:")) {
    const terms = parsePartTerms(query.slice(5));
    if (terms.length === 0) return true;
    return matchesPartTerms(setupPartNames(row), terms);
  }
  return setupLabel(row).toLowerCase().includes(query);
}

function recordLabel(record: AdminRecord) {
  const mythicTag = record.mythic ? " [M]" : "";
  return `${record.distance}${mythicTag} - ${record.map_name ?? "Unknown"} - ${
    record.vehicle_name ?? "Unknown"
  } - ${record.player_name ?? "Unknown"}`;
}

function optionalIcon(form: HTMLFormElement) {
  const icon = new FormData(form).get("icon");
  return icon instanceof File && icon.size > 0 ? icon : null;
}

function applyMarkup(
  textarea: HTMLTextAreaElement | null,
  setValue: (value: string) => void,
  prefix: string,
  suffix: string
) {
  if (!textarea) return;
  const { selectionStart, selectionEnd, value } = textarea;
  const selected = value.slice(selectionStart, selectionEnd);
  const next = `${value.slice(0, selectionStart)}${prefix}${selected}${suffix}${value.slice(selectionEnd)}`;
  setValue(next);
  const innerStart = selectionStart + prefix.length;
  const innerEnd = selectionEnd + prefix.length;
  requestAnimationFrame(() => {
    textarea.focus();
    textarea.setSelectionRange(innerStart, innerEnd);
  });
}

function applyLinkMarkup(textarea: HTMLTextAreaElement | null, setValue: (value: string) => void) {
  if (!textarea) return;
  const { selectionStart, selectionEnd, value } = textarea;
  const selected = value.slice(selectionStart, selectionEnd);
  const label = selected || "text";
  const placeholder = "https://";
  const next = `${value.slice(0, selectionStart)}[${label}](${placeholder})${value.slice(selectionEnd)}`;
  setValue(next);
  const urlStart = selectionStart + label.length + 3;
  requestAnimationFrame(() => {
    textarea.focus();
    textarea.setSelectionRange(urlStart, urlStart + placeholder.length);
  });
}

function applyLinePrefix(textarea: HTMLTextAreaElement | null, setValue: (value: string) => void, prefix: string) {
  if (!textarea) return;
  const value = textarea.value;
  const { selectionStart } = textarea;
  const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
  const next = `${value.slice(0, lineStart)}${prefix}${value.slice(lineStart)}`;
  setValue(next);
  requestAnimationFrame(() => {
    textarea.focus();
    textarea.setSelectionRange(lineStart + prefix.length, lineStart + prefix.length);
  });
}

type NewsFormatToolbarProps = {
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  setValue: (value: string) => void;
  previewVisible: boolean;
  onTogglePreview: () => void;
};

function NewsFormatToolbar({ textareaRef, setValue, previewVisible, onTogglePreview }: NewsFormatToolbarProps) {
  const target = () => textareaRef.current;
  return (
    <>
      <div className="news-toolbar" role="toolbar" aria-label="Formatting options">
        <button
          type="button"
          title="Bold (**text**)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyMarkup(target(), setValue, "**", "**")}
        >
          <strong>B</strong>
        </button>
        <button
          type="button"
          title="Italic (*text*)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyMarkup(target(), setValue, "*", "*")}
        >
          <em>I</em>
        </button>
        <button
          type="button"
          title="Strikethrough (~~text~~)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyMarkup(target(), setValue, "~~", "~~")}
        >
          <del>S</del>
        </button>
        <button
          type="button"
          title="Inline code (`text`)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyMarkup(target(), setValue, "`", "`")}
        >
          {"</>"}
        </button>
        <button
          type="button"
          title="Link ([text](url))"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyLinkMarkup(target(), setValue)}
        >
          Link
        </button>
        <button
          type="button"
          title="Bullet list (- item)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyLinePrefix(target(), setValue, "- ")}
        >
          {"\u2022"} List
        </button>
        <button
          type="button"
          title="Heading (## text)"
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => applyLinePrefix(target(), setValue, "## ")}
        >
          H
        </button>
        <span className="news-toolbar-spacer" />
        <button type="button" className="button-ghost" onClick={onTogglePreview}>
          {previewVisible ? "Hide Preview" : "Preview"}
        </button>
      </div>
      <p className="frontend-muted news-format-hint">
        Markup: <strong>**bold**</strong>, <em>*italic*</em>, <del>~~strikethrough~~</del>, <code>`code`</code>,
        [text](/records) links, and {"{{ Stats }}"} mentions.
      </p>
    </>
  );
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
  const [longestRecordId, setLongestRecordId] = useState("");
  const [mapName, setMapName] = useState("");
  const [mapSpecial, setMapSpecial] = useState(false);
  const [vehicleName, setVehicleName] = useState("");
  const [partName, setPartName] = useState("");
  const [selectedPartIds, setSelectedPartIds] = useState<number[]>([]);
  const [setupEchoAffectedPartId, setSetupEchoAffectedPartId] = useState<number | null>(null);
  const [newsTitle, setNewsTitle] = useState("");
  const [newsContent, setNewsContent] = useState("");
  const [editingNewsId, setEditingNewsId] = useState<number | null>(null);
  const [editingNewsTitle, setEditingNewsTitle] = useState("");
  const [editingNewsContent, setEditingNewsContent] = useState("");
  const [changelogVersion, setChangelogVersion] = useState("");
  const [changelogTitle, setChangelogTitle] = useState("");
  const [changelogAdded, setChangelogAdded] = useState("");
  const [changelogChanged, setChangelogChanged] = useState("");
  const [changelogFixed, setChangelogFixed] = useState("");
  const [editingChangelogId, setEditingChangelogId] = useState<number | null>(null);
  const [editingChangelogVersion, setEditingChangelogVersion] = useState("");
  const [editingChangelogTitle, setEditingChangelogTitle] = useState("");
  const [editingChangelogAdded, setEditingChangelogAdded] = useState("");
  const [editingChangelogChanged, setEditingChangelogChanged] = useState("");
  const [editingChangelogFixed, setEditingChangelogFixed] = useState("");
  const [integrity, setIntegrity] = useState<IntegrityStatus | null>(null);
  const [backupMessage, setBackupMessage] = useState("");
  const [backupError, setBackupError] = useState("");
  const [activityLogOpen, setActivityLogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<AdminTab>("records");
  const [banIp, setBanIp] = useState("");
  const [banReason, setBanReason] = useState("");
  const [banExpiresAt, setBanExpiresAt] = useState("");
  const newsContentRef = useRef<HTMLTextAreaElement | null>(null);
  const newsEditContentRef = useRef<HTMLTextAreaElement | null>(null);
  const [newsPreviewVisible, setNewsPreviewVisible] = useState(false);
  const [newsEditPreviewVisible, setNewsEditPreviewVisible] = useState(false);

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
  const longestRecordQuery = useQuery({
    queryKey: ["admin", "longest-record"],
    queryFn: getAdminLongestRecord
  });
  const pendingQuery = useQuery({ queryKey: ["admin", "pending"], queryFn: getPendingSubmissions });
  const newsQuery = useQuery({ queryKey: ["news", 20], queryFn: () => getNews(20) });
  const changelogQuery = useQuery({ queryKey: ["changelog"], queryFn: () => getChangelog(200) });
  const backupsQuery = useQuery({ queryKey: ["admin", "backups"], queryFn: listAdminBackups });
  const maintenanceQuery = useQuery({
    queryKey: ["admin", "maintenance"],
    queryFn: getMaintenanceStatus
  });
  const bansQuery = useQuery({ queryKey: ["admin", "bans"], queryFn: listBans });

  const tuningSetups = setupsQuery.data ?? [];
  const filteredTuningSetups = useMemo(
    () => tuningSetups.filter((row) => matchesSetupFilter(row, tuningSetupFilter)),
    [tuningSetups, tuningSetupFilter]
  );
  const filteredAssignTuningSetups = useMemo(
    () => tuningSetups.filter((row) => matchesSetupFilter(row, assignSetupFilter)),
    [tuningSetups, assignSetupFilter]
  );
  const filteredPlayers = useMemo(
    () =>
      (playersQuery.data ?? []).filter((row) =>
        text(row, "namePlayer", "nameplayer").toLowerCase().includes(playerFilter.toLowerCase())
      ),
    [playersQuery.data, playerFilter]
  );

  useEffect(() => {
    if (!recordForm.playerId || !playersQuery.data) return;
    const player = playersQuery.data.find(
      (row) => String(numberValue(row, "idPlayer", "idplayer")) === recordForm.playerId
    );
    if (player) {
      const country = text(player, "country");
      if (country) {
        setRecordForm((current) => ({ ...current, country }));
      }
    }
  }, [recordForm.playerId, playersQuery.data]);
  useEffect(() => {
    const selected = longestRecordQuery.data;
    if (selected?.set && selected.recordId != null) {
      setLongestRecordId(String(selected.recordId));
    } else if (!selected?.set) {
      setLongestRecordId("");
    }
  }, [longestRecordQuery.data]);

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
      queryClient.invalidateQueries({ queryKey: ["news"] }),
      queryClient.invalidateQueries({ queryKey: ["changelog"] })
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
    const mapId = Number(recordForm.mapId);
    const vehicleId = Number(recordForm.vehicleId);
    const distance = Number(recordForm.distance);
    if (Number.isFinite(distance)) {
      const existing = (recordsQuery.data ?? []).find(
        (record) => record.current === 1 && record.idMap === mapId && record.idVehicle === vehicleId
      );
      if (existing && distance <= existing.distance) {
        const proceed = window.confirm(
          `The new distance (${distance}) is not higher than the current record (${existing.distance}) for this map and vehicle. Submit anyway?`
        );
        if (!proceed) {
          return;
        }
      }
    }
    await runAction(async () => {
      await submitAdminRecord({
        mapId,
        vehicleId,
        distance,
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

  async function handleSetLongestRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const recordId = Number(longestRecordId);
    if (!recordId) {
      return;
    }
    await runAction(async () => {
      await setLongestRecordAdmin(recordId);
    }, "Longest standing record set.");
  }

  async function handleClearLongestRecord() {
    const confirmed = window.confirm(
      "Clear the longest standing record? The stats page will fall back to the automatic pick until a new one is set."
    );
    if (!confirmed) {
      return;
    }
    await runAction(async () => {
      await clearLongestRecordAdmin();
      setLongestRecordId("");
    }, "Longest standing record cleared.");
  }

  async function handleAddMap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const icon = optionalIcon(form);
    await runAction(async () => {
      await addMap(mapName, icon, mapSpecial);
      setMapName("");
      setMapSpecial(false);
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
      await addTuningSetup(selectedPartIds, setupEchoAffectedPartId);
      setSelectedPartIds([]);
      setSetupEchoAffectedPartId(null);
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

  function splitBullets(value: string): string[] {
    return value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  async function handlePostChangelog(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await postAdminChangelog({
        version: changelogVersion,
        title: changelogTitle || null,
        added: splitBullets(changelogAdded),
        changed: splitBullets(changelogChanged),
        fixed: splitBullets(changelogFixed)
      });
      setChangelogVersion("");
      setChangelogTitle("");
      setChangelogAdded("");
      setChangelogChanged("");
      setChangelogFixed("");
    }, "Changelog entry posted.");
  }

  function startEditingChangelog(item: ChangelogItem) {
    setEditingChangelogId(item.id);
    setEditingChangelogVersion(item.version);
    setEditingChangelogTitle(item.title ?? "");
    setEditingChangelogAdded(item.added.join("\n"));
    setEditingChangelogChanged(item.changed.join("\n"));
    setEditingChangelogFixed(item.fixed.join("\n"));
  }

  function cancelEditingChangelog() {
    setEditingChangelogId(null);
    setEditingChangelogVersion("");
    setEditingChangelogTitle("");
    setEditingChangelogAdded("");
    setEditingChangelogChanged("");
    setEditingChangelogFixed("");
  }

  async function handleUpdateChangelog(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingChangelogId === null) {
      return;
    }
    await runAction(async () => {
      await updateAdminChangelog(editingChangelogId, {
        version: editingChangelogVersion,
        title: editingChangelogTitle || null,
        added: splitBullets(editingChangelogAdded),
        changed: splitBullets(editingChangelogChanged),
        fixed: splitBullets(editingChangelogFixed)
      });
      cancelEditingChangelog();
    }, "Changelog entry updated.");
  }

  async function handleDeleteChangelog(changelogId: number) {
    const confirmed = window.confirm("Delete this changelog entry?");
    if (!confirmed) {
      return;
    }
    await runAction(async () => {
      await deleteAdminChangelog(changelogId);
      if (editingChangelogId === changelogId) {
        cancelEditingChangelog();
      }
    }, "Changelog entry deleted.");
  }

  function togglePart(partId: number) {
    setSelectedPartIds((current) => {
      const next = current.includes(partId) ? current.filter((id) => id !== partId) : [...current, partId];
      if (partId === ECHO_PART_ID && !next.includes(ECHO_PART_ID)) {
        setSetupEchoAffectedPartId(null);
      }
      return next;
    });
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

  async function handleCreateBan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      await createBan({
        ip: banIp,
        reason: banReason,
        expiresAt: banExpiresAt || null
      });
      setBanIp("");
      setBanReason("");
      setBanExpiresAt("");
    }, "IP address banned.");
  }

  async function handleUnban(ban: BanEntry) {
    const confirmed = window.confirm(`Unban IP ${ban.bannedIp}?`);
    if (!confirmed) {
      return;
    }
    await runAction(async () => {
      await unbanPlayer(ban.id);
    }, "IP address unbanned.");
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

      <nav className="admin-tabs" aria-label="Admin sections">
        {ADMIN_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`admin-tab${activeTab === tab.id ? " admin-tab--active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "records" && (
        <>
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
              placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:wings,nitro')..."
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
          <select
            id="questionable-record-select"
            required
            value={statusRecordId}
            onChange={(event) => {
              const id = event.target.value;
              setStatusRecordId(id);
              const record = (recordsQuery.data ?? []).find((r) => String(r.idRecord) === id);
              if (record) {
                setStatusValue(String(record.questionable));
                setStatusNote(record.questionable_reason ?? "");
              } else {
                setStatusValue("");
                setStatusNote("");
              }
            }}
          >
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
            placeholder="Filter by part name or use part: prefix (e.g., 'magnet' or 'part:wings,nitro')..."
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
        <h2>Longest Standing Record</h2>
        <form id="longest-record-form" onSubmit={handleSetLongestRecord}>
          <label>Current setting</label>
          <p className="frontend-muted">
            {longestRecordQuery.isLoading
              ? "Loading..."
              : longestRecordQuery.data?.set
                ? `${longestRecordQuery.data.distance ?? 0} - ${longestRecordQuery.data.mapName ?? "?"} - ${
                    longestRecordQuery.data.vehicleName ?? "?"
                  } - ${longestRecordQuery.data.playerName ?? "?"} — set by ${longestRecordQuery.data.setBy || "?"}`
                : "None set. The stats page shows the automatic pick until one is set."}
          </p>
          <label>Record (current records only)</label>
          <select
            id="longest-record-select"
            required
            value={longestRecordId}
            onChange={(event) => setLongestRecordId(event.target.value)}
          >
            <option value="">Select a record</option>
            {(recordsQuery.data ?? []).map((record) => (
              <option key={record.idRecord} value={record.idRecord}>
                {recordLabel(record)}
              </option>
            ))}
          </select>
          <div className="admin-actions">
            <button type="submit">Set as Longest Standing Record</button>
            <button
              type="button"
              onClick={handleClearLongestRecord}
              className="button-ghost"
              disabled={!longestRecordQuery.data?.set}
            >
              Clear
            </button>
          </div>
        </form>
        <p id="longest-record-message" />
      </div>
        </>
      )}

      {activeTab === "catalog" && (
        <>
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
          <label className="admin-inline">
            <input
              id="map-special-input"
              type="checkbox"
              checked={mapSpecial}
              onChange={(event) => setMapSpecial(event.target.checked)}
            />
            Special Map
          </label>
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
                  <TuningPartWithIcon name={text(row, "nameTuningPart", "nametuningpart")} />
                </label>
              );
            })}
          </div>
          {selectedPartIds.includes(ECHO_PART_ID) && (
            <div style={{ marginTop: 12 }}>
              <label>Echo Affected Part</label>
              <select
                value={setupEchoAffectedPartId ?? ""}
                onChange={(e) => setSetupEchoAffectedPartId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">-- Select a part --</option>
                {(partsQuery.data ?? [])
                  .filter((row) => {
                    const id = numberValue(row, "idTuningPart", "idtuningpart");
                    return selectedPartIds.includes(id) && !ECHO_EXCLUDED_PART_IDS.has(id);
                  })
                  .map((row) => {
                    const id = numberValue(row, "idTuningPart", "idtuningpart");
                    return (
                      <option key={id} value={id}>
                        {text(row, "nameTuningPart", "nametuningpart")}
                      </option>
                    );
                  })}
              </select>
            </div>
          )}
          <button type="submit">Add Tuning Setup</button>
        </form>
        <p id="add-tuning-setup-message" />
      </div>
        </>
      )}

      {activeTab === "submissions" && (
        <>
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
                  <th>Echo Part</th>
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
                    <td>{(submission as Record<string, unknown>).echoAffectedPartName as string ?? ""}</td>
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
        <h2>Banned IP Addresses</h2>
        <form id="ban-form" onSubmit={handleCreateBan}>
          <label>IP Address</label>
          <input
            id="ban-ip-input"
            type="text"
            required
            placeholder="e.g., 123.45.67.89"
            value={banIp}
            onChange={(event) => setBanIp(event.target.value)}
          />
          <label>Reason</label>
          <textarea
            id="ban-reason-input"
            required
            placeholder="Why is this IP banned?"
            value={banReason}
            onChange={(event) => setBanReason(event.target.value)}
          />
          <label>
            Expires (optional)
            <input
              id="ban-expiry-input"
              type="date"
              value={banExpiresAt}
              onChange={(event) => setBanExpiresAt(event.target.value)}
            />
          </label>
          <small className="form-hint">Leave empty for a permanent ban. Expired bans are lifted automatically.</small>
          <button type="submit">Ban IP</button>
        </form>
        <p id="ban-message" />
        <div id="bans-list" className="admin-block">
          {bansQuery.isLoading && <p>Loading...</p>}
          {!bansQuery.isLoading && (bansQuery.data?.bans ?? []).length === 0 && <p>No IP bans.</p>}
          {!bansQuery.isLoading && (bansQuery.data?.bans ?? []).length > 0 && (
            <div className="table-scroll">
              <table className="admin-pending-table">
                <thead>
                  <tr>
                    <th>IP Address</th>
                    <th>Reason</th>
                    <th>Banned By</th>
                    <th>When</th>
                    <th>Expires</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bansQuery.data?.bans.map((ban) => (
                    <tr key={ban.id}>
                      <td>{ban.bannedIp}</td>
                      <td>{ban.reason}</td>
                      <td>{ban.bannedBy}</td>
                      <td>{formatDate(ban.created_at)}</td>
                      <td>{ban.expiresAt ? formatDate(ban.expiresAt) : "Permanent"}</td>
                      <td>{ban.expired ? "Expired" : ban.active ? "Active" : "Unbanned"}</td>
                      <td className="admin-table-actions">
                        {ban.active && !ban.expired && (
                          <button type="button" onClick={() => handleUnban(ban)} className="button-ghost">
                            Unban
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
        </>
      )}

      {activeTab === "content" && (
        <>
      <div className="form-container">
        <h2>Site News (Admins)</h2>
        <form id="news-form" onSubmit={handlePostNews}>
          <label>Title</label>
          <input id="news-title-input" type="text" required value={newsTitle} onChange={(event) => setNewsTitle(event.target.value)} />
          <label>Content</label>
          <NewsFormatToolbar
            textareaRef={newsContentRef}
            setValue={setNewsContent}
            previewVisible={newsPreviewVisible}
            onTogglePreview={() => setNewsPreviewVisible((visible) => !visible)}
          />
          <textarea
            id="news-content-input"
            required
            rows={6}
            ref={newsContentRef}
            value={newsContent}
            onChange={(event) => setNewsContent(event.target.value)}
          />
          {newsPreviewVisible && newsContent.trim() !== "" && (
            <div className="formatted-preview" aria-label="News preview">
              <FormattedText text={newsContent} />
            </div>
          )}
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
            <NewsFormatToolbar
              textareaRef={newsEditContentRef}
              setValue={setEditingNewsContent}
              previewVisible={newsEditPreviewVisible}
              onTogglePreview={() => setNewsEditPreviewVisible((visible) => !visible)}
            />
            <textarea
              id="news-edit-content-input"
              required
              rows={6}
              ref={newsEditContentRef}
              value={editingNewsContent}
              onChange={(event) => setEditingNewsContent(event.target.value)}
            />
            {newsEditPreviewVisible && editingNewsContent.trim() !== "" && (
              <div className="formatted-preview" aria-label="News edit preview">
                <FormattedText text={editingNewsContent} />
              </div>
            )}
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
              <div className="frontend-muted">{formatDate(item.created_at)} - {item.author ?? ""}</div>
              <FormattedText text={item.content} />
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
        <h2>Changelog (Releases)</h2>
        <form id="changelog-form" onSubmit={handlePostChangelog}>
          <label>Version</label>
          <input
            id="changelog-version-input"
            type="text"
            required
            placeholder="e.g., 0.2.0"
            value={changelogVersion}
            onChange={(event) => setChangelogVersion(event.target.value)}
          />
          <label>Title (optional)</label>
          <input
            id="changelog-title-input"
            type="text"
            placeholder="e.g., Site update"
            value={changelogTitle}
            onChange={(event) => setChangelogTitle(event.target.value)}
          />
          <label>Added (one entry per line)</label>
          <textarea
            id="changelog-added-input"
            rows={5}
            value={changelogAdded}
            onChange={(event) => setChangelogAdded(event.target.value)}
          />
          <label>Changed (one entry per line)</label>
          <textarea
            id="changelog-changed-input"
            rows={5}
            value={changelogChanged}
            onChange={(event) => setChangelogChanged(event.target.value)}
          />
          <label>Fixed (one entry per line)</label>
          <textarea
            id="changelog-fixed-input"
            rows={5}
            value={changelogFixed}
            onChange={(event) => setChangelogFixed(event.target.value)}
          />
          <div className="admin-actions">
            <button type="submit">Post Changelog</button>
            <button type="button" onClick={() => changelogQuery.refetch()} className="button-ghost">
              Refresh
            </button>
          </div>
        </form>
        <p id="changelog-message" />
        {editingChangelogId !== null && (
          <form id="changelog-edit-form" className="admin-block" onSubmit={handleUpdateChangelog}>
            <h3 className="admin-subtitle">Edit Changelog Entry</h3>
            <label>Version</label>
            <input
              id="changelog-edit-version-input"
              type="text"
              required
              value={editingChangelogVersion}
              onChange={(event) => setEditingChangelogVersion(event.target.value)}
            />
            <label>Title (optional)</label>
            <input
              id="changelog-edit-title-input"
              type="text"
              value={editingChangelogTitle}
              onChange={(event) => setEditingChangelogTitle(event.target.value)}
            />
            <label>Added (one entry per line)</label>
            <textarea
              id="changelog-edit-added-input"
              rows={5}
              value={editingChangelogAdded}
              onChange={(event) => setEditingChangelogAdded(event.target.value)}
            />
            <label>Changed (one entry per line)</label>
            <textarea
              id="changelog-edit-changed-input"
              rows={5}
              value={editingChangelogChanged}
              onChange={(event) => setEditingChangelogChanged(event.target.value)}
            />
            <label>Fixed (one entry per line)</label>
            <textarea
              id="changelog-edit-fixed-input"
              rows={5}
              value={editingChangelogFixed}
              onChange={(event) => setEditingChangelogFixed(event.target.value)}
            />
            <div className="admin-actions">
              <button type="submit">Save Changelog</button>
              <button type="button" onClick={cancelEditingChangelog} className="button-ghost">
                Cancel
              </button>
            </div>
          </form>
        )}
        <div id="admin-changelog-list">
          {changelogQuery.isLoading && <p>Loading changelog...</p>}
          {changelogQuery.data?.changelog.map((item) => (
            <div className="news-item" key={item.id}>
              <h3>v{item.version}{item.title ? ` - ${item.title}` : ""}</h3>
              <div className="frontend-muted">{formatDate(item.created_at)} - {item.author ?? ""}</div>
              {item.added.length > 0 && (
                <div className="admin-changelog-category">
                  <strong>Added:</strong>
                  <ul>
                    {item.added.map((bullet, index) => (
                      <li key={`added-${index}`}>
                        <FormattedText text={bullet} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {item.changed.length > 0 && (
                <div className="admin-changelog-category">
                  <strong>Changed:</strong>
                  <ul>
                    {item.changed.map((bullet, index) => (
                      <li key={`changed-${index}`}>
                        <FormattedText text={bullet} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {item.fixed.length > 0 && (
                <div className="admin-changelog-category">
                  <strong>Fixed:</strong>
                  <ul>
                    {item.fixed.map((bullet, index) => (
                      <li key={`fixed-${index}`}>
                        <FormattedText text={bullet} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="admin-actions admin-actions--compact">
                <button type="button" onClick={() => startEditingChangelog(item)} className="button-ghost">
                  Edit
                </button>
                <button type="button" onClick={() => handleDeleteChangelog(item.id)} className="button-ghost">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
        </>
      )}

      {activeTab === "community" && <CommunityAdminPanel />}

      {activeTab === "system" && (
        <>
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
                    <td>{formatBytes(backup.size)}</td>
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

      <button
        type="button"
        className="activity-log-toggle"
        onClick={() => setActivityLogOpen(true)}
      >
        Activity Log
      </button>
        </>
      )}

      <ActivityLogPanel isOpen={activityLogOpen} onClose={() => setActivityLogOpen(false)} />
    </div>
  );
}
