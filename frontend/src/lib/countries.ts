import countryData from "@shared/countries.json";

export type CountryOption = {
  code: string;
  name: string;
};

type CountryEntry = {
  code: string;
  name: string;
  /** Legacy free-text spellings that map onto this code. */
  aliases?: string[];
};

const entries = countryData.countries as CountryEntry[];

export const COUNTRY_NAME_COLLATOR = new Intl.Collator("en");

export function compareCountryNames(a: string, b: string): number {
  return COUNTRY_NAME_COLLATOR.compare(a, b);
}

export function compareCountryOptions(a: CountryOption, b: CountryOption): number {
  return compareCountryNames(a.name, b.name);
}

export const COUNTRIES: CountryOption[] = entries.map(({ code, name }) => ({ code, name }));

export const COUNTRY_NAMES: Record<string, string> = Object.fromEntries(
  COUNTRIES.map((country) => [country.code, country.name])
);

/**
 * Every accepted spelling for a code, used to normalise legacy free-text
 * country values from the player table. Includes sub-region codes such as
 * `us-tx`, which are not ISO countries and so live in legacyDisplay.tsx.
 */
export const COUNTRY_ALIASES: Record<string, string> = Object.fromEntries(
  entries.flatMap(({ code, name, aliases = [] }) => [
    [name.toLowerCase(), code],
    ...aliases.map((alias) => [alias, code] as [string, string])
  ])
);

export function countryName(code?: string | null): string | null {
  if (!code) return null;
  return COUNTRY_NAMES[code] ?? code.toUpperCase();
}

export function flagUrl(code?: string | null): string | null {
  if (!code) return null;
  return `https://flagcdn.com/${code}.svg`;
}