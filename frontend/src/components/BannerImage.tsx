import { communityBannerUrl } from "../services/community";

type BannerImageProps = {
  communityId: number;
  bannerUpdatedAt?: string | null;
  className?: string;
  alt?: string;
};

export function BannerImage({ communityId, bannerUpdatedAt, className = "", alt = "" }: BannerImageProps) {
  const src = communityBannerUrl(communityId, bannerUpdatedAt);

  if (!src) {
    return <img className={className} src="/img/defaultbanner.svg" alt={alt} loading="lazy" />;
  }

  return <img className={className} src={src} alt={alt} loading="lazy" />;
}