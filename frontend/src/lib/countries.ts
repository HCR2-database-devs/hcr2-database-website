export type CountryOption = {
  code: string;
  name: string;
};

export const COUNTRIES: CountryOption[] = [
  { code: "ad", name: "Andorra" },
  { code: "ae", name: "United Arab Emirates" },
  { code: "ar", name: "Argentina" },
  { code: "at", name: "Austria" },
  { code: "au", name: "Australia" },
  { code: "be", name: "Belgium" },
  { code: "bg", name: "Bulgaria" },
  { code: "br", name: "Brazil" },
  { code: "ca", name: "Canada" },
  { code: "ch", name: "Switzerland" },
  { code: "cl", name: "Chile" },
  { code: "cn", name: "China" },
  { code: "co", name: "Colombia" },
  { code: "cz", name: "Czechia" },
  { code: "de", name: "Germany" },
  { code: "dk", name: "Denmark" },
  { code: "ee", name: "Estonia" },
  { code: "eg", name: "Egypt" },
  { code: "es", name: "Spain" },
  { code: "fi", name: "Finland" },
  { code: "fr", name: "France" },
  { code: "gb", name: "United Kingdom" },
  { code: "gr", name: "Greece" },
  { code: "hr", name: "Croatia" },
  { code: "hu", name: "Hungary" },
  { code: "id", name: "Indonesia" },
  { code: "ie", name: "Ireland" },
  { code: "il", name: "Israel" },
  { code: "in", name: "India" },
  { code: "it", name: "Italy" },
  { code: "jp", name: "Japan" },
  { code: "kr", name: "South Korea" },
  { code: "lt", name: "Lithuania" },
  { code: "lv", name: "Latvia" },
  { code: "mx", name: "Mexico" },
  { code: "my", name: "Malaysia" },
  { code: "nl", name: "Netherlands" },
  { code: "no", name: "Norway" },
  { code: "nz", name: "New Zealand" },
  { code: "pe", name: "Peru" },
  { code: "ph", name: "Philippines" },
  { code: "pl", name: "Poland" },
  { code: "pt", name: "Portugal" },
  { code: "ro", name: "Romania" },
  { code: "ru", name: "Russia" },
  { code: "sa", name: "Saudi Arabia" },
  { code: "se", name: "Sweden" },
  { code: "sg", name: "Singapore" },
  { code: "si", name: "Slovenia" },
  { code: "sk", name: "Slovakia" },
  { code: "th", name: "Thailand" },
  { code: "tr", name: "Turkey" },
  { code: "tw", name: "Taiwan" },
  { code: "ua", name: "Ukraine" },
  { code: "us", name: "United States" },
  { code: "uy", name: "Uruguay" },
  { code: "ve", name: "Venezuela" },
  { code: "vn", name: "Vietnam" },
  { code: "za", name: "South Africa" }
];

const COUNTRY_NAMES: Record<string, string> = Object.fromEntries(COUNTRIES.map((c) => [c.code, c.name]));

export function countryName(code?: string | null): string | null {
  if (!code) return null;
  return COUNTRY_NAMES[code] ?? code.toUpperCase();
}

export function flagUrl(code?: string | null): string | null {
  if (!code) return null;
  return `https://flagcdn.com/${code}.svg`;
}