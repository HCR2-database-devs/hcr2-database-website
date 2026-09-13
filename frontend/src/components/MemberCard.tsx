import { Link } from "react-router-dom";

import { BannerImage } from "./BannerImage";
import { CountryFlag } from "./CountryFlag";
import { UserAvatar } from "./UserAvatar";
import { countryName } from "../lib/countries";
import { formatMemberSince } from "../lib/format";
import type { CommunityMember } from "../types/api";

export function MemberCard({ member }: { member: CommunityMember }) {
  return (
    <Link className="member-card" to={`/community/${member.id}`}>
      <BannerImage
        communityId={member.id}
        bannerUpdatedAt={member.banner_updated_at}
        className="member-card-banner"
      />
      <div className="member-card-body">
        <UserAvatar avatarUrl={member.discord_avatar} name={member.discord_username} size={48} />
        <div className="member-card-copy">
          <span className="member-card-name">{member.discord_username}</span>
          <span className="member-card-meta">
            {member.country && (
              <>
                <CountryFlag code={member.country} /> {countryName(member.country)} ·{" "}
              </>
            )}
            Member since {formatMemberSince(member.created_at) ?? "unknown"}
          </span>
        </div>
      </div>
      {member.bio && <p className="member-card-bio">{member.bio}</p>}
      <div className="member-card-favorites">
        {member.favorite_vehicle_name && <span className="chip">{member.favorite_vehicle_name}</span>}
        {member.favorite_map_name && <span className="chip">{member.favorite_map_name}</span>}
      </div>
    </Link>
  );
}