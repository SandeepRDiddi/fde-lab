"""Remembers the NRPS/AGS claims from the most recent launch into each LMS
context (course), so the scenario engine can call back into NRPS ("populate
the roster") or AGS ("push the final score") later -- outside the request
where the id_token was available -- without re-deriving them.

Keyed by a hash of (issuer, deployment_id, context_id) rather than those
raw values, so the id is a single URL-safe path segment.
"""
import hashlib
import json
from typing import Any, Dict, Optional

from .launch import LtiLaunch
from .state_store import state_store

_CONTEXT_TTL_SECONDS = 60 * 60 * 24  # a training scenario is time-boxed in hours/days, not weeks


def context_key(issuer: str, deployment_id: str, context_id: str) -> str:
    raw = f"{issuer}|{deployment_id}|{context_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def remember(launch: LtiLaunch) -> str:
    key = context_key(launch.issuer, launch.deployment_id, launch.context_id or "")
    payload = {
        "issuer": launch.issuer,
        "client_id": launch.client_id,
        "deployment_id": launch.deployment_id,
        "context_id": launch.context_id,
        "nrps": launch.nrps,
        "ags": launch.ags,
    }
    state_store.put(f"lti:context:{key}", json.dumps(payload), _CONTEXT_TTL_SECONDS)
    return key


def recall(key: str) -> Optional[Dict[str, Any]]:
    raw = state_store.peek(f"lti:context:{key}")
    return json.loads(raw) if raw else None
