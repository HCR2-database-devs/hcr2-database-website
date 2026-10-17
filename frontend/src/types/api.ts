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
  show_hcr2_player_name: boolean;
  admin_disabled: boolean;
  banner_updated_at?: string | null;
  is_owner?: boolean;
  hcr2_player_name?: string | null;
  hcr2_link_verified_at?: string | null;
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
  show_hcr2_player_name?: boolean;
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
  username?: string | null;
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

export type CommunityNotification = {
  id: number;
  community_user_id: number;
  type: string;
  message: string;
  created_at: string;
  read_at?: string | null;
};

export type CommunityNotificationListResponse = {
  notifications: CommunityNotification[];
  count: number;
  unread: number;
  limit: number;
  offset: number;
};

export type NotificationReadResult = {
  updated: number;
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
  | "profile_reporting"
  | "community_notifications"
  | "hcr2_account_linking";

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

// Phase 4: HCR2 player account linking. Verification is always reviewed by a
// human; nothing in these payloads claims an automatic check happened.

export type Hcr2LinkMethod = "team" | "discord_screen_share" | "playhcr_challenge";

export type Hcr2LinkRequestStatus =
  | "draft"
  | "in_progress"
  | "submitted"
  | "approved"
  | "rejected"
  | "expired"
  | "cancelled";

export type Hcr2LinkTeamConfig = {
  available: boolean;
  team_name: string;
  team_password: string;
  details: string;
  requires_leaving_current_team: boolean;
  supports_chinese_version: boolean;
  review: string;
};

export type Hcr2LinkDiscordConfig = {
  available: boolean;
  invite_url: string;
  owner_handles: string[];
  requires_leaving_current_team: boolean;
  requires_microphone: boolean;
  requires_speaking: boolean;
  review: string;
};

export type Hcr2LinkChallengeConfig = {
  available: boolean;
  instructions: string;
  min_distance_m: number;
  max_distance_m: number;
  link_prefix: string;
  requires_leaving_current_team: boolean;
  review: string;
};

export type Hcr2LinkConfig = {
  team: Hcr2LinkTeamConfig;
  discord: Hcr2LinkDiscordConfig;
  challenge: Hcr2LinkChallengeConfig;
  code_ttl_seconds: number;
  code_reroll_cooldown_seconds: number;
  request_ttl_days: number;
  automatic_verification: boolean;
};

export type Hcr2LinkPlayerOption = {
  id_player: number;
  name_player: string;
  record_count: number;
};

export type Hcr2LinkPlayerSearchResponse = {
  players: Hcr2LinkPlayerOption[];
  count: number;
  limit: number;
  offset: number;
  search?: string | null;
};

export type Hcr2LinkRequest = {
  id: number;
  player_name: string;
  player_name_norm: string;
  verification_method: Hcr2LinkMethod;
  status: Hcr2LinkRequestStatus;
  step: string;
  attempt_count: number;
  is_resubmission: boolean;
  supersedes_request_id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  expires_at?: string | null;
  submitted_at?: string | null;
  team_joined_claimed: boolean;
  code?: string | null;
  code_expires_at?: string | null;
  code_last_generated_at?: string | null;
  code_roll_count: number;
  code_sent_claimed: boolean;
  discord_joined_claimed: boolean;
  contacted_owner_claimed: boolean;
  /** Distance in metres the server assigned for the jeep challenge. */
  challenge_distance_m?: number | null;
  challenge_url?: string | null;
  challenge_id?: string | null;
  challenge_link_claimed: boolean;
  appointment_status?: string | null;
  appointment_at?: string | null;
  decided_at?: string | null;
  rejection_category?: string | null;
};

export type Hcr2AccountLink = {
  id: number;
  player_name: string;
  player_name_norm: string;
  verification_method: Hcr2LinkMethod;
  status: "active" | "revoked" | "suspended";
  requested_at?: string | null;
  approved_at?: string | null;
  approved_by_admin?: string | null;
  revoked_at?: string | null;
  revocation_reason?: string | null;
};

export type Hcr2LinkStatus = {
  link: Hcr2AccountLink | null;
  /** Most recent attempt, editable or not. */
  request: Hcr2LinkRequest | null;
  /** True when `request` is still draft/in_progress/submitted and resumable. */
  request_is_live: boolean;
  history: Hcr2LinkRequest[];
  automatic_verification: boolean;
};

export type Hcr2LinkCodeState = {
  code: string | null;
  player_name?: string;
  code_expires_at?: string | null;
  code_last_generated_at?: string | null;
  code_expired: boolean;
  code_expires_in_seconds: number;
  reroll_available_in_seconds: number;
  reroll_cooldown_seconds: number;
  code_roll_count: number;
  single_use?: boolean;
  previous_code_invalidated?: boolean;
};

export type Hcr2LinkActionResult = {
  request: Hcr2LinkRequest;
  resumed?: boolean;
  message?: string;
  automatic_verification?: boolean;
};

export type Hcr2LinkSubmitResult = {
  request: Hcr2LinkRequest;
  message: string;
  automatic_verification: boolean;
};

export type AdminHcr2LinkRequest = Hcr2LinkRequest & {
  community_user_id: number;
  link_id?: number | null;
  player_id: number;
  code_value?: string | null;
  code_generated_at?: string | null;
  code_visibility_confirmed: boolean;
  community_username?: string | null;
  discord_id?: string | null;
  discord_username?: string | null;
  discord_avatar?: string | null;
  decided_by_admin?: string | null;
  rejection_reason?: string | null;
  admin_note?: string | null;
  other_attempts?: number;
};

export type AdminHcr2LinkListResponse = {
  requests: AdminHcr2LinkRequest[];
  count: number;
  limit: number;
  offset: number;
  status?: string | null;
  method?: string | null;
};

export type AdminHcr2LinkStep = {
  id: number;
  step: string;
  reached_at?: string | null;
  detail: string;
};

export type AdminHcr2LinkConflicts = {
  active_links: number;
  open_requests: number;
  competing_claimants: number;
};

export type AdminHcr2LinkDetail = {
  request: AdminHcr2LinkRequest;
  steps: AdminHcr2LinkStep[];
  history: Array<{
    id: number;
    community_user_id: number;
    player_name: string;
    status: string;
    step: string;
    created_at?: string | null;
    submitted_at?: string | null;
    decided_at?: string | null;
    rejection_category?: string | null;
    rejection_reason?: string | null;
    is_resubmission: boolean;
    attempt_count: number;
    community_username?: string | null;
  }>;
  conflicts: AdminHcr2LinkConflicts;
};

export type AdminHcr2LinkList = {
  links: Array<
    AdminHcr2AccountLink & {
      community_username?: string | null;
      discord_username?: string | null;
    }
  >;
  count: number;
  limit: number;
  offset: number;
};

export type AdminHcr2AccountLink = Hcr2AccountLink & {
  community_user_id: number;
  approved_by_admin?: string | null;
  revoked_by_admin?: string | null;
};

export const HCR2_REJECTION_CATEGORIES: { value: string; label: string }[] = [
  { value: "code_not_visible", label: "Code was censored or not visible in team chat" },
  { value: "wrong_player_name", label: "Wrong player name" },
  { value: "could_not_confirm_account", label: "Could not confirm the account" },
  { value: "screen_share_inconclusive", label: "Screen share was inconclusive" },
  { value: "challenge_mismatch", label: "Challenge link did not match the assigned distance" },
  { value: "name_already_linked", label: "Player name is already linked" },
  { value: "no_contact", label: "Could not reach the user" },
  { value: "request_cancelled", label: "Request cancelled" },
  { value: "other", label: "Other" }
];

export const HCR2_APPOINTMENT_STATUSES: { value: string; label: string }[] = [
  { value: "waiting_contact", label: "Waiting for contact" },
  { value: "awaiting_scheduling", label: "Awaiting scheduling" },
  { value: "scheduled", label: "Scheduled" },
  { value: "awaiting_screen_share", label: "Awaiting screen-share" },
  { value: "awaiting_decision", label: "Awaiting decision" },
  { value: "cancelled", label: "Cancelled" }
];
