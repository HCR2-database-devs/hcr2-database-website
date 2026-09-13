import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";

import { MemberCard } from "../components/MemberCard";
import { COUNTRIES } from "../lib/countries";
import { getCommunityMembers } from "../services/community";

const PAGE_SIZE = 24;

const SORT_OPTIONS = [
  { value: "new", label: "Newest members" },
  { value: "name", label: "Name (A-Z)" },
  { value: "active", label: "Recently active" }
];

export function CommunityPage() {
  const [search, setSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");
  const [sort, setSort] = useState("new");
  const [country, setCountry] = useState("");
  const [offset, setOffset] = useState(0);

  const membersQuery = useQuery({
    queryKey: ["community", "members", submittedSearch, sort, country, offset],
    queryFn: () =>
      getCommunityMembers({
        search: submittedSearch || undefined,
        sort: sort || undefined,
        country: country || undefined,
        limit: PAGE_SIZE,
        offset
      })
  });

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

  return (
    <div className="page-container community-page">
      <div className="section-header">
        <h1>Community</h1>
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
        <button className="button" type="submit">
          Search
        </button>
      </form>

      {membersQuery.isLoading && <p className="community-status">Loading community...</p>}

      {!membersQuery.isLoading && membersQuery.isError && (
        <p className="frontend-error">Could not load the community. Please try again.</p>
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
              {count === 0 ? 0 : offset + 1}-{Math.min(offset + members.length, count)} of {count}
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