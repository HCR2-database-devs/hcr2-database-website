import { useState } from "react";

type BadgeIconProps = {
  name: string;
  src?: string | null;
  size?: number;
};

export function BadgeIcon({ name, src, size = 56 }: BadgeIconProps) {
  const [failed, setFailed] = useState(false);
  const initial = name.trim().charAt(0).toUpperCase() || "?";
  return (
    <span
      className={`badge-icon${src && !failed ? "" : " badge-icon--placeholder"}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {src && !failed ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <span>{initial}</span>
      )}
    </span>
  );
}
