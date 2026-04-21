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

export type AdminRecord = {
  idRecord: number;
  idMap: number;
  idVehicle: number;
  idPlayer?: number | null;
  idTuningSetup?: number | null;
  distance: number;
  current: number;
  questionable: number;
  questionable_reason?: string | null;
  map_name?: string | null;
  vehicle_name?: string | null;
  player_name?: string | null;
  player_country?: string | null;
  tuning_parts?: string | null;
};

export type PendingSubmission = {
  id: number;
  idMap?: number | null;
  idVehicle?: number | null;
  distance?: number | null;
  playerName?: string | null;
  playerCountry?: string | null;
  tuningParts?: string | null;
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
