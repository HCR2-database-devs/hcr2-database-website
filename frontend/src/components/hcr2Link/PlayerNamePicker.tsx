import { useEffect, useId, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { searchHcr2LinkPlayers } from "../../services/hcr2Link";
import type { Hcr2LinkPlayerOption } from "../../types/api";

const DEBOUNCE_MS = 250;
const MIN_QUERY_LENGTH = 2;

type PlayerNamePickerProps = {
  value: string | null;
  onSelect: (player: Hcr2LinkPlayerOption) => void;
  disabled?: boolean;
};

/**
 * Searchable dropdown backed by the records database.
 *
 * Free typing is impossible: the list only ever offers names returned by
 * `GET /community/hcr2-link/players`, which are exactly the names that hold or
 * have held an Adventure world record. The backend revalidates the choice on
 * submit and on approval, so this is a usability affordance rather than the
 * security boundary.
 */
export function PlayerNamePicker({ value, onSelect, disabled = false }: PlayerNamePickerProps) {
  const [term, setTerm] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const inputId = useId();
  const listboxId = `${inputId}-listbox`;

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(term.trim()), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [term]);

  useEffect(() => {
    function onDocumentClick(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocumentClick);
    return () => document.removeEventListener("mousedown", onDocumentClick);
  }, []);

  const query = useQuery({
    queryKey: ["hcr2-link", "players", debounced],
    queryFn: () => searchHcr2LinkPlayers(debounced, 20, 0),
    enabled: debounced.length >= MIN_QUERY_LENGTH,
    staleTime: 30_000
  });

  const options = query.data?.players ?? [];
  const expanded = open && debounced.length >= MIN_QUERY_LENGTH;

  function choose(player: Hcr2LinkPlayerOption) {
    onSelect(player);
    setTerm("");
    setDebounced("");
    setOpen(false);
    setActiveIndex(0);
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!expanded) {
      if (event.key === "ArrowDown" || event.key === "Enter") {
        setOpen(true);
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (options.length === 0 ? 0 : (index + 1) % options.length));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) =>
        options.length === 0 ? 0 : (index - 1 + options.length) % options.length
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      const player = options[activeIndex];
      if (player) {
        choose(player);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  if (value) {
    return (
      <div className="hcr2-player-picker">
        <p className="hcr2-player-selected">
          <strong>{value}</strong>
          <span className="frontend-muted">
            Selected from the records database. Only names with an Adventure world record are
            listed.
          </span>
        </p>
      </div>
    );
  }

  return (
    <div className="hcr2-player-picker" ref={containerRef}>
      <label htmlFor={inputId}>
        Search for your HCR2 player name
        <input
          id={inputId}
          type="search"
          role="combobox"
          autoComplete="off"
          aria-expanded={expanded}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={expanded && options[activeIndex] ? `${listboxId}-${activeIndex}` : undefined}
          placeholder="Start typing your in-game name..."
          value={term}
          disabled={disabled}
          onChange={(event) => {
            setTerm(event.target.value);
            setOpen(true);
            setActiveIndex(0);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
      </label>
      <small className="form-hint">
        You cannot type a name freely. Only names that appear in the records database can be
        linked.
      </small>

      {expanded && (
        <ul className="hcr2-player-options" id={listboxId} role="listbox" aria-label="Player names">
          {query.isLoading && <li className="hcr2-player-options-empty">Searching...</li>}
          {query.isError && (
            <li className="hcr2-player-options-empty">Could not load player names.</li>
          )}
          {!query.isLoading && !query.isError && options.length === 0 && (
            <li className="hcr2-player-options-empty">
              No matching player name in the records database.
            </li>
          )}
          {options.map((player, index) => (
            <li
              key={player.id_player}
              id={`${listboxId}-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              className={`hcr2-player-option${index === activeIndex ? " is-active" : ""}`}
              onMouseEnter={() => setActiveIndex(index)}
              onMouseDown={(event) => {
                // mousedown fires before blur, so the click is not lost.
                event.preventDefault();
                choose(player);
              }}
            >
              <span className="hcr2-player-option-name">{player.name_player}</span>
              <span className="hcr2-player-option-meta">
                {player.record_count} world record{player.record_count === 1 ? "" : "s"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}