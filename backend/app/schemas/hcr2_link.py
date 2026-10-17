"""Pydantic payloads for Phase 4 HCR2 player account linking."""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Hcr2LinkPayload(BaseModel):
    """Base for payloads that accept both camelCase and snake_case keys."""

    model_config = ConfigDict(populate_by_name=True)


class StartLinkRequest(Hcr2LinkPayload):
    player_name: str = Field(
        default="",
        validation_alias=AliasChoices("playerName", "player_name"),
    )


class ChooseMethodRequest(Hcr2LinkPayload):
    verification_method: str = Field(
        default="",
        validation_alias=AliasChoices("verificationMethod", "verification_method"),
    )


class SubmitLinkRequest(Hcr2LinkPayload):
    instructions_followed: bool = Field(
        default=False,
        validation_alias=AliasChoices("instructionsFollowed", "instructions_followed"),
    )
    method_steps_completed: bool = Field(
        default=False,
        validation_alias=AliasChoices("methodStepsCompleted", "method_steps_completed"),
    )


class CodeSentRequest(Hcr2LinkPayload):
    visibility_confirmed: bool = Field(
        default=False,
        validation_alias=AliasChoices("visibilityConfirmed", "visibility_confirmed"),
    )


class ChallengeLinkRequest(Hcr2LinkPayload):
    """The playhcr.com challenge the member made for their assigned distance."""

    challenge_url: str = Field(
        default="",
        max_length=512,
        validation_alias=AliasChoices("challengeUrl", "challenge_url"),
    )


class AdminNoteRequest(Hcr2LinkPayload):
    note: str | None = None


class AdminRejectRequest(Hcr2LinkPayload):
    category: str = ""
    reason: str = ""
    note: str | None = None


class AdminAppointmentRequest(Hcr2LinkPayload):
    appointment_status: str = Field(
        default="",
        validation_alias=AliasChoices("appointmentStatus", "appointment_status"),
    )
    appointment_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("appointmentAt", "appointment_at"),
    )
    note: str | None = None


class AdminLinkStatusRequest(Hcr2LinkPayload):
    status: str = ""
    reason: str | None = None


class AdminLinkDetail(Hcr2LinkPayload):
    """Shape documentation for the admin review payload.

    Declared so the response contract is explicit and type-checked in tests;
    the router returns ``response_model=None`` because the payload is assembled
    from several repository queries.
    """

    request: dict
    steps: list[dict]
    history: list[dict]
    conflicts: dict