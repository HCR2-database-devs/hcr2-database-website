type UserAvatarProps = {
  avatarUrl?: string | null;
  name?: string | null;
  size?: number;
};

export function UserAvatar({ avatarUrl, name, size = 24 }: UserAvatarProps) {
  const style = { width: size, height: size, fontSize: Math.max(11, Math.round(size * 0.46)) };

  if (avatarUrl) {
    return (
      <img
        className="user-avatar"
        style={style}
        src={avatarUrl}
        alt=""
        width={size}
        height={size}
        referrerPolicy="no-referrer"
      />
    );
  }

  const initial = (name ?? "").trim().charAt(0).toUpperCase() || "?";
  return (
    <span className="user-avatar user-avatar--fallback" style={style} aria-hidden="true">
      {initial}
    </span>
  );
}