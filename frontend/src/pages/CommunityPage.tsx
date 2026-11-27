import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { BetaBadge } from "../components/BetaBadge";
import { FeatureGate } from "../components/FeatureGate";
import { MemberCard } from "../components/MemberCard";
import { RequireAuth } from "../components/RequireAuth";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { COUNTRIES } from "../lib/countries";
import { getCommunityMembers } from "../services/community";
import { getPublicData } from "../services/publicData";

const PAGE_SIZE = 24;

const SORT_OPTIONS = [
  { value: "new", label: "Newest members" },
  { value: "name", label: "Name (A-Z)" },
  { value: "active", label: "Recently active" }
];

export function CommunityPage() {
  return (
    <RequireAuth>
      <FeatureGate feature="community_members">
        <CommunityPageContent />
      </FeatureGate>
    </RequireAuth>
  );
}

function CommunityPageContent() {
  const { data: authStatus } = useAuthStatus();
  const [search, setSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const [sort, setSort] = useState("new");
  const [country, setCountry] = useState("");
  const [favoriteVehicleId, setFavoriteVehicleId] = useState("");
  const [favoriteMapId, setFavoriteMapId] = useState("");
  const [hasHcr2, setHasHcr2] = useState("");
  const [offset, setOffset] = useState(0);

  const needsOnboarding =
    authStatus?.logged === true &&
    authStatus.community !== undefined &&
    authStatus.community !== null &&
    !authStatus.community.username;

  const vehiclesQuery = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles"),
    enabled: !needsOnboarding,
    staleTime: 5 * 60 * 1000
  });

  const mapsQuery = useQuery({
    queryKey: ["public-data", "maps"],
    queryFn: () => getPublicData("maps"),
    enabled: !needsOnboarding,
    staleTime: 5 * 60 * 1000
  });

  const membersQuery = useQuery({
    queryKey: [
      "community",
      "members",
      submittedSearch,
      sort,
      country,
      favoriteVehicleId,
      favoriteMapId,
      hasHcr2,
      offset
    ],
    queryFn: () =>
      getCommunityMembers({
        search: submittedSearch || undefined,
        sort: sort || undefined,
        country: country || undefined,
        favorite_vehicle_id: favoriteVehicleId ? Number(favoriteVehicleId) : undefined,
        favorite_map_id: favoriteMapId ? Number(favoriteMapId) : undefined,
        has_hcr2: hasHcr2 === "" ? undefined : hasHcr2 === "true",
        limit: PAGE_SIZE,
        offset
      }),
    enabled: !needsOnboarding
  });

  const vehicleOptions = (vehiclesQuery.data ?? []).flatMap((row) => {
    const id = Number(row.idVehicle);
    const name = String(row.nameVehicle ?? "");
    return Number.isFinite(id) && name ? [{ id, name }] : [];
  });

  const mapOptions = (mapsQuery.data ?? []).flatMap((row) => {
    const id = Number(row.idMap);
    const name = String(row.nameMap ?? "");
    return Number.isFinite(id) && name ? [{ id, name }] : [];
  });

  if (needsOnboarding) {
    return (
      <div className="page-container">
        <div className="account-card">
          <h1>Choose a community username</h1>
          <p className="frontend-message">
            You need a username before you can take part in the community — the
            member directory and player profiles are hidden until you choose one.
          </p>
          <div className="frontend-modal-actions">
            <Link className="button" to="/onboarding">
              Choose my username
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const members = membersQuery.data?.members ?? [];
  const count = membersQuery.data?.count ?? 0;
  const hasMore = offset + members.length < count;

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedSearch(search.trim());
    setOffset(0);
  }

  function handleSortChange(value: string) {
    setSort(value);
    setOffset(0);
  }

  function handleCountryChange(value: string) {
    setCountry(value);
    setOffset(0);
  }

  function handleFavoriteVehicleChange(value: string) {
    setFavoriteVehicleId(value);
    setOffset(0);
  }

  function handleFavoriteMapChange(value: string) {
    setFavoriteMapId(value);
    setOffset(0);
  }

  function handleHcr2Change(value: string) {
    setHasHcr2(value);
    setOffset(0);
  }

  return (
    <div className="page-container community-page">
      <div className="section-header">
        <h1>
          Community <BetaBadge feature="community_members" />
        </h1>
        <p className="section-subtitle">Public profiles of HCR2 players who have joined the database.</p>
      </div>

      <form className="community-filters" onSubmit={handleSearch}>
        <label>
          Search
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Find a player..."
            maxLength={50}
          />
        </label>
        <label>
          Sort
          <select value={sort} onChange={(event) => handleSortChange(event.target.value)}>
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Country
          <select value={country} onChange={(event) => handleCountryChange(event.target.value)}>
            <option value="">All countries</option>
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Favorite vehicle
          <select
            value={favoriteVehicleId}
            onChange={(event) => handleFavoriteVehicleChange(event.target.value)}
            disabled={vehiclesQuery.isLoading}
          >
            <option value="">All vehicles</option>
            {vehicleOptions.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Favorite map
          <select
            value={favoriteMapId}
            onChange={(event) => handleFavoriteMapChange(event.target.value)}
            disabled={mapsQuery.isLoading}
          >
            <option value="">All maps</option>
            {mapOptions.map((mapOption) => (
              <option key={mapOption.id} value={mapOption.id}>
                {mapOption.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          HCR2
          <select value={hasHcr2} onChange={(event) => handleHcr2Change(event.target.value)}>
            <option value="">Any HCR2 status</option>
            <option value="true">Linked name shown</option>
            <option value="false">No linked name</option>
          </select>
        </label>
        <button className="button" type="submit">
          Search
        </button>
      </form>

      {membersQuery.isLoading && <p className="community-status" role="status">Loading community...</p>}

      {!membersQuery.isLoading && membersQuery.isError && (
        <p className="frontend-error" role="alert">Could not load the community. Please try again.</p>
      )}

      {!membersQuery.isLoading && !membersQuery.isError && members.length === 0 && (
        <p className="community-status">No members found.</p>
      )}

      {members.length > 0 && (
        <>
          <div className="member-grid">
            {members.map((member) => (
              <MemberCard key={member.id} member={member} />
            ))}
          </div>

          <div className="community-pagination">
            <button
              className="button-ghost"
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
            >
              Previous
            </button>
            <span className="community-pagination-info">
              {count === 0 ? "0 profiles" : `${offset + 1}-${Math.min(offset + members.length, count)} of ${count} profiles`}
            </span>
            <button
              className="button-ghost"
              type="button"
              disabled={!hasMore}
              onClick={() => setOffset((current) => current + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}