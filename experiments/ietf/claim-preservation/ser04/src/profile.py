"""Non-normative, bounded semantic probes. NOT a SER or SCITT crypto verifier."""

import base64
import binascii
import hashlib
import json
import re
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "cp-ser04-local/1"
TYPE = "application/vnd.signed-evidence.eval-receipt+json"
SCHEMA = "https://signed-evidence.org/eval-receipt/v1"
MAX_BYTES = 65536
MAX_DEPTH = 32
REQUIRED = {
    "schema",
    "suite",
    "suite_version",
    "metric",
    "comparator",
    "threshold",
    "score",
    "passed",
    "n",
    "model_id_commit",
    "dataset_id_commit",
    "commit_alg",
    "timestamp",
}
REPRESENTATIONS = ("SER", "DSSE", "DIGEST_ONLY", "DIGEST_RESOLVED")


class Unsupported(ValueError):
    """Input cannot support a claim within this deliberately limited profile."""


class ResourceLimit(Unsupported):
    """Bound reached; this is not a measured evaluation failure."""


class Pairs(list):
    """Keep JSON object pairs before duplicate detection, distinct from arrays."""


def digest(data: bytes) -> str:
    """Return SHA-256 over the exact supplied bytes."""
    return hashlib.sha256(data).hexdigest()


def encode(value: Any) -> bytes:
    """Encode local JSON deterministically; not a general RFC 8785 implementation."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _reject_constant(value: str) -> None:
    raise Unsupported("Non-JSON numeric constant: " + value)


def parse(data: bytes, *, pairs: bool = False, ijson: bool = True) -> Any:
    """Read bounded UTF-8 JSON; reject duplicates and invalid I-JSON strings."""
    if len(data) > MAX_BYTES:
        raise ResourceLimit("byte limit exceeded")
    if data.startswith(b"\xef\xbb\xbf"):
        raise Unsupported("byte order mark")
    # Bound depth before the recursive JSON decoder, respecting quoted strings.
    depth = 0
    quoted = escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > MAX_DEPTH:
                raise ResourceLimit("nesting limit exceeded")
        elif byte in (93, 125):
            depth -= 1
    try:
        obj = json.loads(
            data.decode("utf-8"), object_pairs_hook=Pairs, parse_constant=_reject_constant
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Unsupported("invalid JSON/UTF-8: " + str(exc)) from exc

    def visit(value: Any) -> Any:
        if isinstance(value, str) and ijson:
            for char in value:
                cp = ord(char)
                if 0xD800 <= cp <= 0xDFFF or 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFF >= 0xFFFE:
                    raise Unsupported("non-I-JSON code point")
        if isinstance(value, Pairs):
            names = [key for key, _ in value]
            if not pairs and len(set(names)) != len(names):
                raise Unsupported("duplicate member name")
            converted = [(visit(k), visit(v)) for k, v in value]
            return Pairs(converted) if pairs else dict(converted)
        if isinstance(value, list):
            return [visit(item) for item in value]
        return value

    return visit(obj)


def decode64(value: Any) -> bytes:
    """Decode canonical padded base64, without whitespace or permissive fallback."""
    if not isinstance(value, str):
        raise Unsupported("base64 must be a string")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise Unsupported("invalid base64") from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise Unsupported("noncanonical base64")
    return raw


def extract_b(receipt: bytes) -> bytes:
    """Execute the bounded receipt extraction of SER-04 steps 1 through 3 only."""
    obj = parse(receipt)
    if not isinstance(obj, dict) or set(obj) != {"schema", "payload_b64", "signature"}:
        raise Unsupported("receipt member set")
    sig = obj["signature"]
    if not isinstance(sig, dict) or set(sig) not in ({"alg", "sig"}, {"alg", "sig", "key"}):
        raise Unsupported("signature member set")
    if obj["schema"] != TYPE:
        raise Unsupported("unsupported receipt type")
    return decode64(obj["payload_b64"])


def compare(score: str, comparator: str, threshold: str) -> bool:
    """Compare exact decimals without float conversion or context rounding."""
    left, right = Decimal(score), Decimal(threshold)
    return {">=": left >= right, ">": left > right, "<=": left <= right, "<": left < right}[
        comparator
    ]


def payload(b: bytes) -> dict:
    """Check the supported SER payload subset; never produce a full SER verdict."""
    obj = parse(b)
    if not isinstance(obj, dict) or set(obj) not in (REQUIRED, REQUIRED | {"criteria_digest"}):
        raise Unsupported("unknown or missing payload member; no extension inference")
    if obj["schema"] != SCHEMA or obj["commit_alg"] != "sha256-salted-v1":
        raise Unsupported("unsupported payload basis")
    if any(not isinstance(obj[k], str) or not obj[k] for k in ("suite", "suite_version", "metric")):
        raise Unsupported("empty or non-string declared identifier")
    if obj["comparator"] not in (">=", ">", "<=", "<"):
        raise Unsupported("unsupported comparator")
    for name in ("score", "threshold"):
        if not isinstance(obj[name], str) or not re.fullmatch(
            r"-?(0|[1-9][0-9]*)(\.[0-9]+)?", obj[name]
        ):
            raise Unsupported("non-decimal score or threshold")
    if type(obj["n"]) is not int or not 1 <= obj["n"] <= 2**53 - 1:
        raise Unsupported("sample count outside supported exact integer range")
    if type(obj["passed"]) is not bool:
        raise Unsupported("passed must be boolean")
    for name in ("model_id_commit", "dataset_id_commit", "criteria_digest"):
        if name in obj and (
            not isinstance(obj[name], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", obj[name])
        ):
            raise Unsupported("invalid commitment/digest syntax")
    stamp = obj["timestamp"]
    if not isinstance(stamp, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp
    ):
        raise Unsupported("timestamp form")
    year, month, day, hour, minute, second = map(int, re.findall(r"[0-9]+", stamp))
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not (
        1 <= month <= 12
        and 1 <= day <= days[month - 1]
        and hour < 24
        and minute < 60
        and second < 60
    ):
        raise Unsupported("timestamp range")
    # This shape has only fixed ASCII keys, strings, boolean, and bounded integer n.
    # Therefore encode() coincides with JCS on this supported subset ONLY.
    if encode(obj) != b:
        raise Unsupported("B is not the supported canonical serialization")
    if compare(obj["score"], obj["comparator"], obj["threshold"]) != obj["passed"]:
        raise Unsupported("internal arithmetic disagreement; not an evaluation verdict")
    return obj


def to_dsse(receipt: bytes) -> bytes:
    """Apply mappings-04 section 4.1, preserving B and the selected signature."""
    b = extract_b(receipt)
    obj = parse(receipt)
    return encode(
        {
            "payloadType": TYPE,
            "payload": base64.b64encode(b).decode("ascii"),
            "signatures": [{"sig": obj["signature"]["sig"]}],
        }
    )


def from_dsse(envelope: bytes) -> bytes:
    """Reconstruct one receipt with no key hint; multi-signature choice is unsupported."""
    obj = parse(envelope)
    if not isinstance(obj, dict) or set(obj) != {"payloadType", "payload", "signatures"}:
        raise Unsupported("unsupported DSSE shape")
    if obj["payloadType"] != TYPE:
        raise Unsupported("unsupported DSSE payloadType")
    sigs = obj["signatures"]
    if not isinstance(sigs, list) or len(sigs) != 1:
        raise Unsupported("ambiguous or missing signature selection")
    if not isinstance(sigs[0], dict) or set(sigs[0]) != {"sig"}:
        raise Unsupported("unsupported DSSE signature shape")
    b = decode64(obj["payload"])
    sig = decode64(sigs[0]["sig"])
    if len(sig) != 64:
        raise Unsupported("unsupported DSSE signature length")
    return encode(
        {
            "schema": TYPE,
            "payload_b64": base64.b64encode(b).decode("ascii"),
            "signature": {"alg": "ed25519", "sig": base64.b64encode(sig).decode("ascii")},
        }
    )


def to_reference(receipt: bytes) -> bytes:
    """Apply the typed digest construction of mappings-04 section 5.1."""
    return encode({"type": TYPE, "digest_alg": "SHA-256", "digest": digest(extract_b(receipt))})


def reference_status(
    reference: bytes,
    candidate: bytes | None,
    *,
    accepts_context: bool = True,
    implements_context: bool = True,
) -> dict:
    """Keep the reference processing state separate from digest matching (section 5.1)."""
    try:
        obj = parse(reference, pairs=True, ijson=False)
    except ResourceLimit:
        return {"state": None, "matching": "INDETERMINATE", "reason": "RESOURCE_LIMIT"}
    except Unsupported as exc:
        return {"state": "Malformed", "matching": "INDETERMINATE", "reason": str(exc)}
    if not isinstance(obj, Pairs):
        return {"state": "Malformed", "matching": "INDETERMINATE", "reason": "not an object"}
    names = [k for k, _ in obj]
    values = dict(obj)
    matching = "INDETERMINATE"
    b = None
    candidate_error = None
    if candidate is not None:
        try:
            b = extract_b(candidate)
        except ResourceLimit:
            candidate_error = "RESOURCE_LIMIT"
        except Unsupported:
            candidate_error = "invalid receipt extraction"
    extractable = all(
        names.count(k) == 1 and isinstance(values.get(k), str) for k in ("digest_alg", "digest")
    )
    algorithm_ok = values.get("digest_alg") == "SHA-256"
    value_ok = isinstance(values.get("digest"), str) and bool(
        re.fullmatch("[0-9a-f]{64}", values["digest"])
    )
    if extractable and algorithm_ok and value_ok and b is not None:
        matching = "MATCH" if digest(b) == values["digest"] else "NO_MATCH"
    well_formed = (
        len(set(names)) == len(names)
        and {"type", "digest_alg", "digest"}
        <= set(names)
        <= {"type", "digest_alg", "digest", "purpose"}
        and all(isinstance(v, str) for _, v in obj)
    )
    if not well_formed:
        state, reason = "Malformed", "reference form"
    elif not accepts_context or values["type"] != TYPE or "purpose" in values:
        state, reason = "Unresolved", "unaccepted context/type/purpose"
    elif not algorithm_ok or not value_ok:
        state, reason = "Failed", "algorithm or digest representation"
    elif not implements_context:
        state, reason = "Unresolved", "unimplemented"
    elif candidate is None:
        state, reason = "Unresolved", "unavailable"
    elif candidate_error == "RESOURCE_LIMIT":
        state, reason = None, "RESOURCE_LIMIT"
    elif candidate_error:
        state, reason = "Failed", candidate_error
    else:
        state = "Verified" if matching == "MATCH" else "Failed"
        reason = "digest comparison only; signature/key/truth not checked"
    return {"state": state, "matching": matching, "reason": reason}


def verification(kind: str, result: str, checked: str, limitation: str) -> dict:
    """Make an INTERNAL typed verification record, never a wire attestation."""
    return {
        "actor": VERSION,
        "procedure": VERSION + "/" + kind,
        "type": kind,
        "checked_input_sha256": checked,
        "result": result,
        "limitation": limitation,
    }


def consume(
    wire: bytes,
    representation: str,
    *,
    candidate: bytes | None = None,
    profile_version: str = VERSION,
) -> dict:
    """Normalize only consumer-visible evidence; never consult hidden source context."""
    view = {
        "representation": representation,
        "profile_version": VERSION,
        "requested_profile_version": profile_version,
        "source_assertions": None,
        "derivations": [],
        "consumer_judgments": [],
        "reliance_records": [],
        "measurement_state": "UNESTABLISHED",
        "coverage": "UNESTABLISHED",
        "actual_executed_identity": "UNESTABLISHED",
        "criteria_before_run": "UNESTABLISHED",
        "prior_mapping_history": "UNESTABLISHED",
        "evidence": {
            "actor": VERSION,
            "context": "this offline consume invocation",
            "B_availability": "UNAVAILABLE",
            "digest_knowledge": "UNAVAILABLE",
        },
        "checks": [],
        "limits": [],
    }
    checked = digest(wire)
    view["checks"].append(
        verification(
            "signature",
            "NOT_EVALUATED",
            checked,
            "No Ed25519 verification or key acceptance performed",
        )
    )
    if profile_version != VERSION:
        view["limits"].append("unsupported local profile version")
        return view
    try:
        if representation == "SER":
            receipt = wire
        elif representation == "DSSE":
            receipt = from_dsse(wire)
        elif representation in ("DIGEST_ONLY", "DIGEST_RESOLVED"):
            actual_candidate = candidate if representation == "DIGEST_RESOLVED" else None
            view["reference"] = reference_status(wire, actual_candidate)
            try:
                ref = parse(wire)
                if (
                    isinstance(ref, dict)
                    and ref.get("digest_alg") == "SHA-256"
                    and isinstance(ref.get("digest"), str)
                    and re.fullmatch("[0-9a-f]{64}", ref["digest"])
                ):
                    view["evidence"].update(digest_knowledge="REPORTED", B_sha256=ref["digest"])
            except Unsupported:
                pass
            if view["reference"]["state"] != "Verified":
                view["limits"].append("reference not resolved; payload assertions unavailable")
                return view
            receipt = actual_candidate
        else:
            raise Unsupported("unknown representation")
        b = extract_b(receipt)
        view["evidence"].update(
            B_availability="AVAILABLE",
            digest_knowledge="RECOMPUTED",
            B_sha256=digest(b),
            receipt_sha256=digest(receipt),
        )
        view["checks"].append(
            verification(
                "digest", "RECOMPUTED", digest(b), "Exact B bytes only; no signature or key binding"
            )
        )
        obj = payload(b)
        view["source_assertions"] = deepcopy(obj)
        view["checks"].append(
            verification(
                "structure_and_arithmetic",
                "SUPPORTED",
                digest(b),
                "Supported payload subset only; not full SER verification",
            )
        )
        view["limits"].extend(
            [
                "Execution status, population completeness and prior mapping history absent in SER",
                "Names and salted identifier commitments do not prove executed artifact identity",
                "Timestamp and criteria digest do not establish ordering",
            ]
        )
    except Unsupported as exc:
        view["limits"].append(str(exc))
        view["checks"].append(verification("semantic_input", "UNESTABLISHED", checked, str(exc)))
    return view


def exercise(receipt: bytes, representation: str, **kwargs: Any) -> tuple[bytes, dict]:
    """Map an exact receipt and consume only the bytes appropriate to that route."""
    if representation == "SER":
        wire = receipt
    elif representation == "DSSE":
        wire = to_dsse(receipt)
    else:
        wire = to_reference(receipt)
    return wire, consume(wire, representation, candidate=receipt, **kwargs)


def judge(view: dict, actor: str, threshold: str, rule: str) -> dict:
    """Apply a later consumer threshold without changing any source assertion."""
    source = view["source_assertions"]
    if source is None:
        return {
            "actor": actor,
            "rule": rule,
            "result": "UNESTABLISHED",
            "reason": "source observation unavailable",
        }
    result = {
        "actor": actor,
        "rule": rule,
        "scope": "one supplied receipt score",
        "inputs": {"B_sha256": view["evidence"]["B_sha256"], "selector": "/score"},
        "threshold": threshold,
        "comparator": ">=",
        "result": compare(source["score"], ">=", threshold),
        "origin": "later_consumer_policy",
        "ordering": "not a source criterion",
    }
    view["consumer_judgments"].append(result)
    return result


def rounded(view: dict, places: int) -> dict:
    """Record a presentation derivation; compare thresholds against original decimals."""
    source = view["source_assertions"]
    if source is None:
        return {"result": "UNESTABLISHED"}
    with localcontext() as ctx:
        ctx.prec = MAX_BYTES
        value = Decimal(source["score"]).quantize(
            Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP
        )
    result = {
        "origin": "local_derivation",
        "procedure": "decimal/ROUND_HALF_UP",
        "places": places,
        "input_score": source["score"],
        "presentation_score": str(value),
        "source_comparison": source["passed"],
        "presentation_comparison": compare(str(value), source["comparator"], source["threshold"]),
        "source_uncertainty": "UNESTABLISHED",
    }
    view["derivations"].append(result)
    return result


def select_receipt(receipts: list[bytes], b_sha256: str | None = None) -> bytes:
    """Select by exact B identity; do not choose a favorable metric or deduplicate attempts."""
    matches = [r for r in receipts if b_sha256 is None or digest(extract_b(r)) == b_sha256]
    if len(matches) != 1:
        raise Unsupported("ambiguous or unresolved result selection")
    return matches[0]


def boundary(record: dict) -> dict:
    """Retain a local pressure record but refuse to encode unsupported states as SER."""
    return {
        "origin": "author_constructed_local_context_NOT_SER",
        "source_record": deepcopy(record),
        "SER_encoding": "UNSUPPORTED",
        "reason": "SER requires a numeric score, criterion and boolean comparison; "
        "it has no execution/non-evaluation state field",
    }


def instance_binding(source: bytes, output: bytes, selector: str) -> dict:
    """Bind a LOCAL experiment record, not a native mapping metadata field."""
    material = {
        "source_sha256": digest(source),
        "output_sha256": digest(output),
        "selector": selector,
        "selector_syntax": "RFC6901 on decoded B",
        "digest_selection": "exact file bytes, no canonicalization",
        "profile_sha256": digest((ROOT / "mapping_profile.json").read_bytes()),
        "implementation_sha256": digest(Path(__file__).read_bytes()),
    }
    return {
        "origin": "local_mapping_observation",
        "material": material,
        "binding_sha256": digest(encode(material)),
        "limitation": "Self-consistency only; not authentication or a native SER field",
    }


def binding_matches(binding: dict, source: bytes, output: bytes, selector: str) -> bool:
    """Detect a substituted local mapping record by recomputing its exact tuple."""
    return binding == instance_binding(source, output, selector)
