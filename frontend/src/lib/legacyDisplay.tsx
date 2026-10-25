import type { SyntheticEvent } from "react";

import { COUNTRIES, COUNTRY_ALIASES, flagUrl } from "./countries";

const countryDisplayNames: Record<string, string> = Object.fromEntries(
  COUNTRIES.map((country) => [country.code, country.name])
);

//: Region-specific codes that are not ISO countries, so they are not in
//: shared/countries.json. The player table stores these as free text.
const subRegionCodes: Record<string, string> = {
  "england": "gb-eng",
  "northern ireland": "gb-nir",
  "scotland": "gb-sct",
  "wales": "gb-wls",
  "alaska": "us-ak",
  "alabama": "us-al",
  "arkansas": "us-ar",
  "arizona": "us-az",
  "california": "us-ca",
  "colorado": "us-co",
  "connecticut": "us-ct",
  "delaware": "us-de",
  "florida": "us-fl",
  "georgia (us)": "us-ga",
  "hawaii": "us-hi",
  "iowa": "us-ia",
  "idaho": "us-id",
  "illinois": "us-il",
  "indiana": "us-in",
  "kansas": "us-ks",
  "kentucky": "us-ky",
  "louisiana": "us-la",
  "massachusetts": "us-ma",
  "maryland": "us-md",
  "maine": "us-me",
  "michigan": "us-mi",
  "minnesota": "us-mn",
  "missouri": "us-mo",
  "mississippi": "us-ms",
  "montana": "us-mt",
  "north carolina": "us-nc",
  "north dakota": "us-nd",
  "nebraska": "us-ne",
  "new hampshire": "us-nh",
  "new jersey": "us-nj",
  "new mexico": "us-nm",
  "nevada": "us-nv",
  "new york": "us-ny",
  "ohio": "us-oh",
  "oklahoma": "us-ok",
  "oregon": "us-or",
  "pennsylvania": "us-pa",
  "rhode island": "us-ri",
  "south carolina": "us-sc",
  "south dakota": "us-sd",
  "tennessee": "us-tn",
  "texas": "us-tx",
  "utah": "us-ut",
  "virginia": "us-va",
  "vermont": "us-vt",
  "washington": "us-wa",
  "wisconsin": "us-wi",
  "west virginia": "us-wv",
  "wyoming": "us-wy",
};

//: Non-country placeholders and territories the ISO list omits.
const extraCountryCodes: Record<string, string> = {
  "kosovo": "xk",
  "united nations": "un",
  "other countries": "question"
};

const countryCodes: Record<string, string> = {
  ...COUNTRY_ALIASES,
  ...extraCountryCodes,
  ...subRegionCodes
};

export function asText(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

export function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
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

export function iconUrl(folder: string, name: unknown) {
  return `/img/${folder}/${iconSlug(name)}.webp`;
}

function fallbackIcon(event: SyntheticEvent<HTMLImageElement>, folder: string, name: string) {
  const image = event.currentTarget;
  const slug = iconSlug(name);
  if (image.src.endsWith(".webp")) {
    image.src = `/img/${folder}/${slug}.svg`;
    return;
  }
  if (!image.src.endsWith(".png")) {
    image.src = `/img/${folder}/${slug}.png`;
    return;
  }
  image.style.display = "none";
}

export function MapWithIcon({ name }: { name: unknown }) {
  const text = asText(name) || "Unknown";
  return (
    <span className="map-cell" title={text}>
      <img
        className="map-icon"
        src={iconUrl("map_icons", text)}
        alt={`${text} icon`}
        width={24}
        height={24}
        loading="lazy"
        decoding="async"
        onError={(event) => fallbackIcon(event, "map_icons", text)}
      />
      <span className="cell-text">{text}</span>
    </span>
  );
}

export function VehicleWithIcon({ name }: { name: unknown }) {
  const text = asText(name) || "Unknown";
  return (
    <span className="vehicle-cell" title={text}>
      <img
        className="vehicle-icon"
        src={iconUrl("vehicle_icons", text)}
        alt={`${text} icon`}
        width={24}
        height={24}
        loading="lazy"
        decoding="async"
        onError={(event) => fallbackIcon(event, "vehicle_icons", text)}
      />
      <span className="cell-text">{text}</span>
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
        src={iconUrl("tuning_parts_icons", text)}
        alt={`${text} icon`}
        title={text}
        width={22}
        height={22}
        loading="lazy"
        decoding="async"
        onError={(event) => fallbackIcon(event, "tuning_parts_icons", text)}
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
          src={iconUrl("tuning_parts_icons", part)}
          alt={`${part} icon`}
          title={part}
          width={22}
          height={22}
          loading="lazy"
          decoding="async"
          onError={(event) => fallbackIcon(event, "tuning_parts_icons", part)}
        />
      ))}
    </>
  );
}

export function getCountryCode(country: unknown): string | null {
  const raw = asText(country).trim();
  if (!raw) {
    return null;
  }
  if (raw.length === 2 && /^[A-Za-z]{2}$/.test(raw)) {
    const lower = raw.toLowerCase();
    return countryCodes[lower] ?? lower;
  }
  const normalized = raw.toLowerCase();
  if (countryCodes[normalized]) {
    return countryCodes[normalized];
  }
  const lastToken = normalized.split(/[,\s]+/).pop() ?? "";
  return countryCodes[lastToken] ?? null;
}

export function normalizeCountryDisplay(country: unknown): string | null {
  const raw = asText(country).trim();
  if (!raw) {
    return null;
  }
  const code = getCountryCode(raw);
  if (!code || code === "question") {
    return null;
  }
  const display = countryDisplayNames[code];
  if (display) {
    return display;
  }
  if (/^(gb|us)-[a-z]{2}$/.test(code)) {
    return raw
      .split(/[\s-]+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  }
  return raw;
}

export function CountryWithFlag({ country }: { country: unknown }) {
  const text = asText(country);
  const code = getCountryCode(text);
  const src = code && code !== "question" ? flagUrl(code) : null;
  if (!text) {
    return null;
  }
  return (
    <span className="country-cell" title={text}>
      {src && (
        <img
          className="country-flag"
          src={src}
          alt={`${text} flag`}
          width={20}
          height={15}
          loading="lazy"
          decoding="async"
        />
      )}
      {code === "question" && <span className="country-flag">?</span>}
      <span className="cell-text">{text}</span>
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
