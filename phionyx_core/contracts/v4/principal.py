"""Principal — on whose authority a decision was taken (AARM R6 / AIREP subject.principal).

AARM R6 requires every action receipt to be *cryptographically bound to an agent
identity*. Before this module, Phionyx records carried an ``actor`` string. That
string is covered by the record hash, so its **integrity** is protected — nobody
can alter it after the fact without breaking the chain. But integrity of a field
is not assurance of an identity. A value the recording system writes about itself
is a claim, and a signature over a claim signs the claim, not the fact.

This module carries the missing half: **how the identity was established**. It
mirrors ``subject.principal`` in the AIREP core schema so that a record produced
here and a record produced by another AIREP implementation answer the same
question in the same vocabulary.

The discipline, quoted from that schema because it is the whole point:

    An identity the controlled system asserts about itself is worth exactly as
    much as a control path the controlled system can write - which is to say, it
    is a claim, not evidence. Omitting the field is better than implying
    verification that did not happen.

So ``established_by`` is required whenever a principal is recorded at all, and
``ASSERTED_BY_CALLER`` — the weakest honest value — is the correct answer for
most of what Phionyx does today. Recording that weakness is the improvement.
Recording something stronger than the truth would not be.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EstablishedBy(str, Enum):
    """How the identity in a principal block was established, weakest first.

    Values and meanings are the AIREP ``subject.principal.established_by`` enum.
    """

    #: The caller said so. No verification. The honest default.
    ASSERTED_BY_CALLER = "asserted_by_caller"
    #: A credential was presented and checked.
    VERIFIED_CREDENTIAL = "verified_credential"
    #: Established by mutual TLS at the transport layer.
    MUTUAL_TLS = "mutual_tls"
    #: The platform attested the workload identity.
    PLATFORM_ATTESTED = "platform_attested"
    #: Established by a signature produced outside the controlled system.
    OUT_OF_BAND_SIGNATURE = "out_of_band_signature"
    #: Explicitly not established. Better than a value that implies it was.
    NOT_ESTABLISHED = "not_established"


#: The values that do NOT constitute independent verification. A record whose
#: ``established_by`` is in this set carries a claimed identity, and any reader
#: treating it as a verified one is making an error the record warned them about.
UNVERIFIED = frozenset(
    {EstablishedBy.ASSERTED_BY_CALLER, EstablishedBy.NOT_ESTABLISHED}
)


class Principal(BaseModel):
    """On whose authority a decision was taken.

    ``subject.runtime`` says which system decided; this says who it decided for.
    All identity layers are optional because a producer that cannot determine one
    should leave it out rather than invent it. ``established_by`` is not optional:
    a principal without it is exactly the ambiguity this model exists to remove.
    """

    human: str | None = Field(
        None, description="Identifier of the human principal on whose authority the action ran")
    service: str | None = Field(
        None, description="Identifier of the service or workload identity the action ran under")
    session: str | None = Field(
        None, description="Identifier of the agent session or delegation this decision belongs to")
    scope: list[str] = Field(
        default_factory=list,
        description="Roles or privileges in force at decision time")
    established_by: EstablishedBy = Field(
        ...,
        description="How the identity was established. Record honestly; the weak values are useful")
    attestation_ref: str | None = Field(
        None,
        description="Pointer to the artifact establishing the identity, when one exists")

    @property
    def is_verified(self) -> bool:
        """Whether this principal was established by something other than assertion."""
        return self.established_by not in UNVERIFIED

    def hash_content(self) -> dict:
        """The stable projection of this principal for inclusion in a record hash.

        Sorted, primitive-only, and stable across pydantic versions — a record
        hash must not move because a serialiser changed.
        """
        return {
            "human": self.human,
            "service": self.service,
            "session": self.session,
            "scope": sorted(self.scope),
            "established_by": self.established_by.value,
            "attestation_ref": self.attestation_ref,
        }
