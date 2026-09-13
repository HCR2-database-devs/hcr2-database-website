import { flagUrl } from "../lib/countries";

type CountryFlagProps = {
  code?: string | null;
  className?: string;
};

export function CountryFlag({ code, className = "" }: CountryFlagProps) {
  const url = flagUrl(code);
  if (!url) return null;
  return <img className={`country-flag ${className}`.trim()} src={url} alt="" loading="lazy" />;
}