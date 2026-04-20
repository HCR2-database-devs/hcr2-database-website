export type LegacyRow = Record<string, unknown>;

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
