import type { ReactNode, SyntheticEvent } from "react";

const countryCodes: Record<string, string> = {
  andorra: "ad",
  "united arab emirates": "ae",
  uae: "ae",
  afghanistan: "af",
  "antigua and barbuda": "ag",
  anguilla: "ai",
  albania: "al",
  armenia: "am",
  angola: "ao",
  antarctica: "aq",
  argentina: "ar",
  "american samoa": "as",
  austria: "at",
  australia: "au",
  aruba: "aw",
  "åland islands": "ax",
  azerbaijan: "az",
  "bosnia and herzegovina": "ba",
  barbados: "bb",
  bangladesh: "bd",
  belgium: "be",
  "burkina faso": "bf",
  bulgaria: "bg",
  bahrain: "bh",
  burundi: "bi",
  benin: "bj",
  "saint barthélemy": "bl",
  "saint barthelemy": "bl",
  bermuda: "bm",
  brunei: "bn",
  bolivia: "bo",
  "caribbean netherlands": "bq",
  brazil: "br",
  bahamas: "bs",
  bhutan: "bt",
  "bouvet island": "bv",
  botswana: "bw",
  belarus: "by",
  belize: "bz",
  canada: "ca",
  "cocos (keeling) islands": "cc",
  "cocos islands": "cc",
  "dr congo": "cd",
  "democratic republic of the congo": "cd",
  "central african republic": "cf",
  "republic of the congo": "cg",
  congo: "cg",
  switzerland: "ch",
  "côte d'ivoire": "ci",
  "ivory coast": "ci",
  "cote d'ivoire": "ci",
  "cook islands": "ck",
  chile: "cl",
  cameroon: "cm",
  china: "cn",
  colombia: "co",
  "costa rica": "cr",
  cuba: "cu",
  "cape verde": "cv",
  curaçao: "cw",
  "christmas island": "cx",
  cyprus: "cy",
  czechia: "cz",
  "czech republic": "cz",
  germany: "de",
  djibouti: "dj",
  denmark: "dk",
  dominica: "dm",
  "dominican republic": "do",
  algeria: "dz",
  ecuador: "ec",
  estonia: "ee",
  egypt: "eg",
  "western sahara": "eh",
  eritrea: "er",
  spain: "es",
  ethiopia: "et",
  "european union": "eu",
  finland: "fi",
  fiji: "fj",
  "falkland islands": "fk",
  micronesia: "fm",
  "faroe islands": "fo",
  france: "fr",
  gabon: "ga",
  "united kingdom": "gb",
  uk: "gb",
  england: "gb-eng",
  "northern ireland": "gb-nir",
  scotland: "gb-sct",
  wales: "gb-wls",
  grenada: "gd",
  georgia: "ge",
  "french guiana": "gf",
  guernsey: "gg",
  ghana: "gh",
  gibraltar: "gi",
  greenland: "gl",
  gambia: "gm",
  guinea: "gn",
  guadeloupe: "gp",
  "equatorial guinea": "gq",
  greece: "gr",
  "south georgia": "gs",
  guatemala: "gt",
  guam: "gu",
  "guinea-bissau": "gw",
  guyana: "gy",
  "hong kong": "hk",
  "heard island and mcdonald islands": "hm",
  honduras: "hn",
  croatia: "hr",
  haiti: "ht",
  hungary: "hu",
  indonesia: "id",
  ireland: "ie",
  israel: "il",
  "isle of man": "im",
  india: "in",
  "british indian ocean territory": "io",
  iraq: "iq",
  iran: "ir",
  iceland: "is",
  italy: "it",
  jersey: "je",
  jamaica: "jm",
  jordan: "jo",
  japan: "jp",
  kenya: "ke",
  kyrgyzstan: "kg",
  cambodia: "kh",
  kiribati: "ki",
  comoros: "km",
  "saint kitts and nevis": "kn",
  "north korea": "kp",
  "south korea": "kr",
  korea: "kr",
  kuwait: "kw",
  "cayman islands": "ky",
  kazakhstan: "kz",
  laos: "la",
  lebanon: "lb",
  "saint lucia": "lc",
  liechtenstein: "li",
  "sri lanka": "lk",
  liberia: "lr",
  lesotho: "ls",
  lithuania: "lt",
  luxembourg: "lu",
  latvia: "lv",
  libya: "ly",
  morocco: "ma",
  monaco: "mc",
  moldova: "md",
  montenegro: "me",
  "saint martin": "mf",
  madagascar: "mg",
  "marshall islands": "mh",
  "north macedonia": "mk",
  mali: "ml",
  myanmar: "mm",
  mongolia: "mn",
  macau: "mo",
  "northern mariana islands": "mp",
  martinique: "mq",
  mauritania: "mr",
  montserrat: "ms",
  malta: "mt",
  mauritius: "mu",
  maldives: "mv",
  malawi: "mw",
  mexico: "mx",
  malaysia: "my",
  mozambique: "mz",
  namibia: "na",
  "new caledonia": "nc",
  niger: "ne",
  "norfolk island": "nf",
  nigeria: "ng",
  nicaragua: "ni",
  netherlands: "nl",
  norway: "no",
  nepal: "np",
  nauru: "nr",
  niue: "nu",
  "new zealand": "nz",
  oman: "om",
  panama: "pa",
  peru: "pe",
  "french polynesia": "pf",
  "papua new guinea": "pg",
  philippines: "ph",
  pakistan: "pk",
  poland: "pl",
  "saint pierre and miquelon": "pm",
  "pitcairn islands": "pn",
  "puerto rico": "pr",
  palestine: "ps",
  portugal: "pt",
  palau: "pw",
  paraguay: "py",
  qatar: "qa",
  réunion: "re",
  reunion: "re",
  romania: "ro",
  serbia: "rs",
  russia: "ru",
  rwanda: "rw",
  "saudi arabia": "sa",
  "solomon islands": "sb",
  seychelles: "sc",
  sudan: "sd",
  sweden: "se",
  singapore: "sg",
  "saint helena": "sh",
  slovenia: "si",
  "svalbard and jan mayen": "sj",
  slovakia: "sk",
  "sierra leone": "sl",
  "san marino": "sm",
  senegal: "sn",
  somalia: "so",
  suriname: "sr",
  "south sudan": "ss",
  "são tomé and príncipe": "st",
  "sao tome and principe": "st",
  "el salvador": "sv",
  "sint maarten": "sx",
  syria: "sy",
  eswatini: "sz",
  swaziland: "sz",
  "turks and caicos islands": "tc",
  chad: "td",
  "french southern and antarctic lands": "tf",
  togo: "tg",
  thailand: "th",
  tajikistan: "tj",
  tokelau: "tk",
  "timor-leste": "tl",
  "east timor": "tl",
  turkmenistan: "tm",
  tunisia: "tn",
  tonga: "to",
  turkey: "tr",
  turkiye: "tr",
  "trinidad and tobago": "tt",
  tuvalu: "tv",
  taiwan: "tw",
  tanzania: "tz",
  ukraine: "ua",
  uganda: "ug",
  "united states minor outlying islands": "um",
  "united nations": "un",
  "united states": "us",
  "united states of america": "us",
  usa: "us",
  alaska: "us-ak",
  alabama: "us-al",
  arkansas: "us-ar",
  arizona: "us-az",
  california: "us-ca",
  colorado: "us-co",
  connecticut: "us-ct",
  delaware: "us-de",
  florida: "us-fl",
  "georgia (us)": "us-ga",
  hawaii: "us-hi",
  iowa: "us-ia",
  idaho: "us-id",
  illinois: "us-il",
  indiana: "us-in",
  kansas: "us-ks",
  kentucky: "us-ky",
  louisiana: "us-la",
  massachusetts: "us-ma",
  maryland: "us-md",
  maine: "us-me",
  michigan: "us-mi",
  minnesota: "us-mn",
  missouri: "us-mo",
  mississippi: "us-ms",
  montana: "us-mt",
  "north carolina": "us-nc",
  "north dakota": "us-nd",
  nebraska: "us-ne",
  "new hampshire": "us-nh",
  "new jersey": "us-nj",
  "new mexico": "us-nm",
  nevada: "us-nv",
  "new york": "us-ny",
  ohio: "us-oh",
  oklahoma: "us-ok",
  oregon: "us-or",
  pennsylvania: "us-pa",
  "rhode island": "us-ri",
  "south carolina": "us-sc",
  "south dakota": "us-sd",
  tennessee: "us-tn",
  texas: "us-tx",
  utah: "us-ut",
  virginia: "us-va",
  vermont: "us-vt",
  washington: "us-wa",
  wisconsin: "us-wi",
  "west virginia": "us-wv",
  wyoming: "us-wy",
  uruguay: "uy",
  uzbekistan: "uz",
  "vatican city": "va",
  "holy see": "va",
  "saint vincent and the grenadines": "vc",
  venezuela: "ve",
  "british virgin islands": "vg",
  "united states virgin islands": "vi",
  "us virgin islands": "vi",
  vietnam: "vn",
  vanuatu: "vu",
  "wallis and futuna": "wf",
  samoa: "ws",
  kosovo: "xk",
  yemen: "ye",
  mayotte: "yt",
  "south africa": "za",
  zambia: "zm",
  zimbabwe: "zw",
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

export function getCountryCode(country: unknown): string | null {
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
        <img className="country-flag" src={`https://flagcdn.com/${code}.svg`} alt={`${text} flag`} />
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
