export const REPO_URL = "https://github.com/HCR2-database-devs/hcr2-database-website";

export const DISCORD_INVITE_URL = "https://discord.gg/GGQPunUbHj";

export type PlannedFeature = {
  id: string;
  label: string;
};

export const PLANNED_FEATURES: PlannedFeature[] = [
  { id: "achievements", label: "Achievements" },
  { id: "xp", label: "XP system" },
  { id: "leaderboard", label: "Community leaderboard" },
  { id: "discord", label: "Discord integration" },
  { id: "friend-requests", label: "Friend requests" },
  { id: "profile-comments", label: "Profile comments" }
];

export const COMMUNITY_LAUNCH_ANNOUNCEMENT_ID = "community-launch-2026-10";