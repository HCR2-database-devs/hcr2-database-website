import type { ReactNode, SyntheticEvent } from "react";

const countryCodes: Record<string, string> = {
  finland: "fi",
  sweden: "se",
  norway: "no",
  denmark: "dk",
  germany: "de",
  france: "fr",
  spain: "es",
  italy: "it",
  netherlands: "nl",
  poland: "pl",
  russia: "ru",
  brazil: "br",
  "united states": "us",
  "united states of america": "us",
  usa: "us",
  canada: "ca",
  australia: "au",
  japan: "jp",
  china: "cn",
  "south korea": "kr",
  korea: "kr",
  "united kingdom": "gb",
  uk: "gb",
  ireland: "ie",
  portugal: "pt",
  belgium: "be",
  switzerland: "ch",
  austria: "at",
  czechia: "cz",
  slovakia: "sk",
  hungary: "hu",
  romania: "ro",
  bulgaria: "bg",
  india: "in",
  mexico: "mx",
  argentina: "ar",
  chile: "cl",
  colombia: "co",
  "south africa": "za",
  "new zealand": "nz",
  greece: "gr",
  turkey: "tr",
  turkiye: "tr",
  egypt: "eg",
  uae: "ae",
  "united arab emirates": "ae",
  "other countries": "question"
};

export function asText(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

export function formatDistance(value: unknown, decimals: number | null = null): string {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return asText(value);
  }
  if (decimals !== null) {
    return numberValue.toLocaleString(undefined, {
      maximumFractionDigits: decimals,
      minimumFractionDigits: decimals
    });
  }
  return Math.round(numberValue).toLocaleString();
}

export function iconSlug(name: unknown): string {
  return asText(name)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "");
}

function fallbackToPng(event: SyntheticEvent<HTMLImageElement>, folder: string, name: string) {
  const image = event.currentTarget;
  const pngSource = `/img/${folder}/${iconSlug(name)}.png`;
  if (!image.src.endsWith(".png")) {
    image.src = pngSource;
    return;
  }
  image.style.display = "none";
}

export function MapWithIcon({ name }: { name: unknown }) {
  const text = asText(name) || "Unknown";
  return (
    <span className="map-cell">
      <img
        className="map-icon"
        src={`/img/map_icons/${iconSlug(text)}.svg`}
        alt={`${text} icon`}
        onError={(event) => fallbackToPng(event, "map_icons", text)}
      />{" "}
      {text}
    </span>
  );
}

export function VehicleWithIcon({ name }: { name: unknown }) {
  const text = asText(name) || "Unknown";
  return (
    <span className="vehicle-cell">
      <img
        className="vehicle-icon"
        src={`/img/vehicle_icons/${iconSlug(text)}.svg`}
        alt={`${text} icon`}
        onError={(event) => fallbackToPng(event, "vehicle_icons", text)}
      />{" "}
      {text}
    </span>
  );
}

export function TuningPartWithIcon({ name }: { name: unknown }) {
  const text = asText(name);
  if (!text) {
    return null;
  }
  return (
    <span className="tuning-part-cell">
      <img
        className="tuning-part-icon"
        src={`/img/tuning_parts_icons/${iconSlug(text)}.svg`}
        alt={`${text} icon`}
        title={text}
        onError={(event) => fallbackToPng(event, "tuning_parts_icons", text)}
      />{" "}
      {text}
    </span>
  );
}

export function TuningPartsIcons({ parts }: { parts: unknown }) {
  const partList = asText(parts)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  return (
    <>
      {partList.map((part) => (
        <img
          key={part}
          className="tuning-part-icon"
          src={`/img/tuning_parts_icons/${iconSlug(part)}.svg`}
          alt={`${part} icon`}
          title={part}
          onError={(event) => fallbackToPng(event, "tuning_parts_icons", part)}
        />
      ))}
    </>
  );
}

function getCountryCode(country: unknown): string | null {
  const raw = asText(country).trim();
  if (!raw) {
    return null;
  }
  if (raw.length === 2 && /^[A-Za-z]{2}$/.test(raw)) {
    return raw.toLowerCase();
  }
  const normalized = raw.toLowerCase();
  if (countryCodes[normalized]) {
    return countryCodes[normalized];
  }
  const lastToken = normalized.split(/[,\s]+/).pop() ?? "";
  return countryCodes[lastToken] ?? null;
}

export function CountryWithFlag({ country }: { country: unknown }) {
  const text = asText(country);
  const code = getCountryCode(text);
  if (!text) {
    return null;
  }
  return (
    <span className="country-cell">
      {code && code !== "question" && (
        <img className="country-flag" src={`https://flagcdn.com/20x15/${code}.png`} alt={`${text} flag`} />
      )}
      {code === "question" && <span className="country-flag">?</span>}
      <span>{text}</span>
    </span>
  );
}

export function setupPartsLabel(parts: unknown): string {
  if (Array.isArray(parts)) {
    return parts
      .map((part) =>
        typeof part === "object" && part !== null && "nameTuningPart" in part
          ? asText((part as { nameTuningPart: unknown }).nameTuningPart)
          : asText(part)
      )
      .filter(Boolean)
      .join(", ");
  }
  return asText(parts);
}

export function renderMaybeText(value: ReactNode) {
  return value === "" ? null : value;
}
