export type DataRow = Record<string, unknown>;

export type AuthStatus = {
  logged: boolean;
  allowed: boolean;
  id?: string;
  username?: string | null;
};

export type PublicDataView =
  | "maps"
  | "vehicles"
  | "players"
  | "tuning-parts"
  | "tuning-setups"
  | "records";

export type NewsItem = {
  id: number;
  title: string;
  content: string;
  author?: string | null;
  created_at: string;
};

export type ChangelogItem = {
  id: number;
  version: string;
  title?: string | null;
  added: string[];
  changed: string[];
  fixed: string[];
  author?: string | null;
  created_at: string;
};

export type AdminRecord = {
  idRecord: number;
  idMap: number;
  idVehicle: number;
  idPlayer?: number | null;
  idTuningSetup?: number | null;
  distance: number;
  current: number;
  questionable: number;
  mythic?: boolean;
  questionable_reason?: string | null;
  map_name?: string | null;
  vehicle_name?: string | null;
  player_name?: string | null;
  player_country?: string | null;
  tuning_parts?: string | null;
  echoAffectedPart?: string | null;
};

export type PendingSubmission = {
  id: number;
  idMap?: number | null;
  idVehicle?: number | null;
  distance?: number | null;
  playerName?: string | null;
  playerCountry?: string | null;
  tuningParts?: string | null;
  submitterIp?: string | null;
  status: string;
  submitted_at: string;
  mapName?: string | null;
  vehicleName?: string | null;
};

export type MaintenanceStatus = {
  maintenance: boolean;
  allowed: boolean;
};

export type IntegrityStatus = {
  ok: boolean;
  result: number;
  counts: Record<string, number>;
};

export type BackupItem = {
  name: string;
  size: number;
  mtime: string;
};

export type RecordFilters = {
  search: string;
  maps: string[];
  vehicles: string[];
  tuningParts: string[];
  distanceOp: "" | "gte" | "lte";
  distance: string;
  questionableOnly: boolean;
  verifiedOnly: boolean;
  sort: string;
  mythic?: boolean;
};

export const emptyRecordFilters: RecordFilters = {
  search: "",
  maps: [],
  vehicles: [],
  tuningParts: [],
  distanceOp: "",
  distance: "",
  questionableOnly: false,
  verifiedOnly: false,
  sort: "default",
  mythic: undefined
};

export type PaginatedRecordsResponse = {
  records: DataRow[];
  total: number;
  limit: number;
  offset: number;
};

export type ActivityLogEntry = {
  id: number;
  admin_username: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  entity_name: string | null;
  created_at: string;
};

export type ActivityLogResponse = {
  entries: ActivityLogEntry[];
  total: number;
};

export type BanEntry = {
  id: number;
  bannedIp: string;
  reason: string;
  bannedBy: string;
  created_at: string;
  expiresAt: string | null;
  active: boolean;
  expired?: boolean;
};

export type RecordHistoryEntry = {
  idRecord: number;
  distance: number;
  current: number;
  isMythic: boolean;
  questionable: number;
  questionable_reason?: string | null;
  playerName?: string | null;
  playerCountry?: string | null;
  tuningParts?: string | null;
  created_at: string;
};

export type RecordHistoryResponse = {
  map: string;
  vehicle: string;
  entries: RecordHistoryEntry[];
};

export type SubmissionVolumeEntry = {
  weekStart: string;
  pending: number;
  approved: number;
  rejected: number;
  total: number;
};

export type SubmissionVolumeResponse = {
  weeks: SubmissionVolumeEntry[];
};
