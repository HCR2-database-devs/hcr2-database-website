"""Pure helpers for the playhcr.com jeep challenge verification method.

Method C (see ``docs/hcr2-account-linking.md``) asks the user to drive a
server-assigned random distance, 1 to 2000 metres, with a jeep in Countryside
Adventure, to turn that into a challenge on playhcr.com, and to send the link
to the resulting challenge.

Two rules make the method worth anything:

* The distance is drawn **here**, on the server, when the method is chosen.
  A client that picked its own number would only ever be asked to prove it can
  follow its own instructions, so ``random_distance_m`` is the only source of
  the value that ends up on the request. There is deliberately no re-roll: one
  request gets one distance.
* The link is only accepted when it points at the challenge page itself. A
  submitted value is free text typed by a member, so it is validated against an
  exact prefix rather than merely parsed: ``playhcr.com.attacker.tld``,
  ``http://playhcr.com/...`` and a lookalike that merely *contains* the host
  all fail.

Nothing here reads configuration or touches the database.
"""

import secrets

#: The only accepted shape of a challenge link. Kept as a module constant
#: rather than configuration so the validation rule cannot be loosened by an
#: environment variable, and so the wizard and the service always agree.
CHALLENGE_URL_PREFIX = "https://playhcr.com/challenge?id="

#: Shortest distance the server may assign, in metres.
MIN_DISTANCE_M = 1

#: Longest distance the server may assign, in metres.
MAX_DISTANCE_M = 2000

#: Longest accepted challenge id. Comfortably above any realistic id while
#: keeping a pasted paragraph of text out of the database.
MAX_CHALLENGE_ID_LENGTH = 128

#: Longest accepted link overall.
MAX_CHALLENGE_URL_LENGTH = 512


def random_distance_m(
    *,
    minimum_m: int = MIN_DISTANCE_M,
    maximum_m: int = MAX_DISTANCE_M,
) -> int:
    """Draw a challenge distance in metres, inclusive on both ends.

    Uses :mod:`secrets` rather than :mod:`random` so the value is not
    predictable from earlier draws: a member who could guess the next number
    could farm requests until a 1 m roll came up. Returns ``minimum_m`` when the
    range is degenerate rather than raising, because a misconfigured maximum
    must not turn "pick a method" into a 500.
    """
    low = max(int(minimum_m), 1)
    high = max(int(maximum_m), low)
    return secrets.randbelow(high - low + 1) + low


def normalize_challenge_url(raw: str) -> tuple[str, str]:
    """Validate a submitted challenge link and split out its challenge id.

    Returns ``(url, challenge_id)``. Raises :class:`ValueError` with a message
    meant to be shown to the member as-is when the value is not a
    ``https://playhcr.com/challenge?id=<id>`` link.
    """
    candidate = (raw or "").strip()
    if not candidate:
        raise ValueError("Paste the link to your playhcr.com challenge.")
    if len(candidate) > MAX_CHALLENGE_URL_LENGTH:
        raise ValueError("That link is too long to be a challenge link.")
    if not candidate.startswith(CHALLENGE_URL_PREFIX):
        raise ValueError(
            "The link has to start with https://playhcr.com/challenge?id= ."
        )

    challenge_id = candidate[len(CHALLENGE_URL_PREFIX) :]
    # A pasted link is routinely followed by a full stop or wrapped in
    # smart quotes; strip only trailing whitespace and sentence punctuation so
    # the stored id stays exactly what playhcr.com issued.
    challenge_id = challenge_id.strip().rstrip(".")
    if not challenge_id:
        raise ValueError("That link is missing the challenge id after 'id='.")
    if len(challenge_id) > MAX_CHALLENGE_ID_LENGTH:
        raise ValueError("That challenge id is too long to be a real one.")

    normalized = f"{CHALLENGE_URL_PREFIX}{challenge_id}"
    return normalized, challenge_id