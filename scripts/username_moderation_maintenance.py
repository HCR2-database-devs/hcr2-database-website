import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://www.cs.cmu.edu/~biglou/resources/bad-words.txt"
DATA_PATH = Path(__file__).resolve().parents[1] / "backend/app/core/username_terms.json"


def _normalize(value: str) -> str:
    return value.strip().casefold()


def _reviewed_terms(payload: dict[str, object]) -> set[str]:
    terms: set[str] = set()
    for category in ("exact", "phrase", "compound"):
        values = payload.get(category, [])
        if isinstance(values, list):
            terms.update(_normalize(str(value)) for value in values if str(value).strip())
    return terms


def _covered_by_source(term: str, source_terms: set[str], source_lines: list[str]) -> bool:
    """Return True when the source still covers a reviewed term.

    The upstream file packs several variants onto one line (for example
    "dickhead dick head"), so a multi-word reviewed term is covered when it
    appears as a contiguous run of whitespace-separated tokens in any line, not
    only when it matches a whole line.
    """
    if term in source_terms:
        return True
    if " " not in term:
        return False
    return any(f" {term} " in f" {line} " for line in source_lines)


def _print_report(
    source_terms: set[str],
    reviewed_terms: set[str],
    source_lines: list[str],
) -> tuple[list[str], list[str]]:
    source_sorted = sorted(source_terms)
    reviewed_sorted = sorted(reviewed_terms)
    additions = sorted(source_terms - reviewed_terms)
    removals = sorted(
        term for term in reviewed_terms - source_terms
        if not _covered_by_source(term, source_terms, source_lines)
    )
    print("candidate additions:")
    print("\n".join(additions) if additions else "none")
    print("reviewed terms absent from source:")
    print("\n".join(removals) if removals else "none")
    print("candidate diff:")
    diff = list(
        difflib.unified_diff(
            reviewed_sorted,
            source_sorted,
            fromfile="reviewed",
            tofile="source",
            lineterm="",
        )
    )
    if diff:
        sys.stdout.write("\n".join(diff) + "\n")
    else:
        print("none")
    return additions, removals


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the CMU source and report candidate username moderation changes. "
            "Exits 0 when the vendored list is up to date, 1 when the source cannot be "
            "fetched, and 2 when the source has drifted and needs review."
        )
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        request = Request(SOURCE_URL, headers={"User-Agent": "hcr2-username-maintenance/1"})
        with urlopen(request, timeout=args.timeout) as response:
            raw = response.read()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"unable to fetch source: {exc}", file=sys.stderr)
        return 1

    digest = hashlib.sha256(raw).hexdigest()
    source_lines = [
        normalized
        for line in raw.decode("utf-8").splitlines()
        if (normalized := _normalize(line))
    ]
    source_terms = set(source_lines)
    reviewed_terms = _reviewed_terms(payload)
    print(f"source_url: {SOURCE_URL}")
    print(f"vendored_retrieved_at: {payload.get('retrieved_at', '')}")
    print(f"vendored_sha256: {payload.get('sha256', '')}")
    print(f"fetched_sha256: {digest}")
    if payload.get("sha256") != digest:
        print("checksum status: changed")
    else:
        print("checksum status: matches vendored metadata")
    additions, removals = _print_report(source_terms, reviewed_terms, source_lines)
    # The vendored list is intentionally curated: it is a subset of the source
    # plus extra spaced variants ("ass hole") that catch separator bypasses the
    # upstream file does not cover. Neither additions nor removals are drift on
    # their own, so the only genuine signal is the upstream source changing.
    if payload.get("sha256") == digest:
        print("reviewed list status: up to date")
        print(
            "Note: the reviewed list is curated, so it is expected to differ from "
            "the source. Differences above are not applied automatically."
        )
        return 0
    print(
        "reviewed list status: review required "
        f"(source changed, {len(additions)} candidate additions, "
        f"{len(removals)} reviewed terms no longer covered)"
    )
    print(
        "The upstream source has changed. Review the candidates and update "
        "username_terms.json by hand, then record the new sha256 and retrieved_at."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
