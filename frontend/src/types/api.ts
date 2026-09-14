export type DataRow = Record<string, unknown>;

export type CommunityAccount = {
  id: number;
  discord_id: string;
  discord_username: string;
  discord_avatar?: string | null;
  username?: string | null;
  last_username_change_at?: string | null;
  created_at: string;
  updated_at: string;
  bio: string;
  country?: string | null;
  favorite_vehicle_id?: number | null;
  favorite_vehicle_name?: string | null;
  favorite_map_id?: number | null;
  favorite_map_name?: string | null;
  profile_public: boolean;
  show_country: boolean;
  show_bio: boolean;
  show_favorite_vehicle: boolean;
  show_favorite_map: boolean;
  show_discord_username: boolean;
  show_discord_avatar: boolean;
  admin_disabled: boolean;
  banner_updated_at?: string | null;
  is_owner?: boolean;
};

export type CommunityProfileUpdate = {
  bio?: string;
  country?: string | null;
  favorite_vehicle_id?: number | null;
  favorite_map_id?: number | null;
  profile_public?: boolean;
  show_country?: boolean;
  show_bio?: boolean;
  show_favorite_vehicle?: boolean;
  show_favorite_map?: boolean;
  show_discord_username?: boolean;
  show_discord_avatar?: boolean;
};

export type UsernameUpdate = {
  username: string;
};

export type CommunityMember = {
  id: number;
  username?: string | null;
  discord_username?: string | null;
  discord_avatar?: string | null;
  created_at: string;
  updated_at: string;
  bio?: string | null;
  country?: string | null;
  favorite_vehicle_id?: number | null;
  favorite_vehicle_name?: string | null;
  favorite_map_id?: number | null;
  favorite_map_name?: string | null;
  banner_updated_at?: string | null;
};

export type CommunityMemberListResponse = {
  members: CommunityMember[];
  count: number;
  limit: number;
  offset: number;
  search?: string | null;
  sort: string;
  country?: string | null;
};

export type ReportCategory =
  | "spam"
  | "inappropriate_banner"
  | "inappropriate_bio"
  | "impersonation"
  | "harassment"
  | "other";

export type CommunityReportResult = {
  id: number;
  community_user_id: number;
  category: string;
  status: string;
  created_at: string;
};

export type AdminCommunityProfile = {
  id: number;
  discord_username: string;
  discord_avatar?: string | null;
  created_at: string;
  updated_at: string;
  profile_public: boolean;
  admin_disabled: boolean;
  open_reports: number;
};

export type AdminCommunityProfileListResponse = {
  profiles: AdminCommunityProfile[];
  count: number;
  limit: number;
  offset: number;
  search?: string | null;
};

export type AdminCommunityReport = {
  id: number;
  community_user_id: number;
  target_name: string;
  reporter_community_user_id: number;
  reporter_name: string;
  category: string;
  reason: string;
  status: string;
  created_at: string;
  resolved_by?: string | null;
  resolved_at?: string | null;
  resolution_note?: string | null;
};

export type AdminCommunityReportListResponse = {
  reports: AdminCommunityReport[];
  count: number;
  limit: number;
  offset: number;
  status?: string | null;
};

export type AdminProfileDetail = CommunityAccount & {
  open_reports: number;
  username_history?: UsernameHistoryEntry[];
};

export type UsernameHistoryEntry = {
  id: number;
  community_user_id: number;
  username: string;
  changed_by_admin: string;
  changed_at: string;
};

export type FeatureName =
  | "discord_accounts"
  | "community_profiles"
  | "profile_customization"
  | "community_members"
  | "profile_reporting";

export type FeatureState = "DISABLED" | "BETA" | "ENABLED";

export type AuthStatus = {
  logged: boolean;
  allowed: boolean;
  beta?: boolean;
  id?: string;
  username?: string | null;
  avatar?: string | null;
  community?: CommunityAccount | null;
  features?: Partial<Record<FeatureName, FeatureState>>;
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
  note?: string | null;
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
