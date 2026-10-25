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
    return (
      <img
        className={className}
        src="/img/defaultbanner-1536.webp"
        alt={alt}
        width={1536}
        height={512}
        loading="lazy"
        decoding="async"
        onError={(event) => {
          if (!event.currentTarget.src.endsWith(".jpg")) {
            event.currentTarget.src = "/img/defaultbanner-1536.jpg";
          }
        }}
      />
    );
  }

  return <img className={className} src={src} alt={alt} loading="lazy" />;
}