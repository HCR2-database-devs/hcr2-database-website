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
    return <div className={`community-banner-placeholder ${className}`.trim()} aria-hidden="true" />;
  }

  return <img className={className} src={src} alt={alt} loading="lazy" />;
}