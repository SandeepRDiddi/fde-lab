"""Issues the FDE Lab session that lets a launched student skip a separate
login (acceptance criterion 1), by signing a short-lived JWT the frontend/
backend accept as proof of an already-completed LTI launch.
"""
import time

import jwt

from .config import settings
from .launch import LtiLaunch
from .scenario_client import ScenarioInstance


def issue_session_token(launch: LtiLaunch, scenario: ScenarioInstance) -> str:
    now = int(time.time())
    claims = {
        "iss": "fde-lab-lti-service",
        "sub": f"{launch.issuer}|{launch.subject}",
        "iat": now,
        "exp": now + settings.session_ttl_seconds,
        "name": launch.name,
        "email": launch.email,
        "roles": launch.roles,
        "scenario_instance_id": scenario.scenario_instance_id,
        "lms_context_id": launch.context_id,
    }
    return jwt.encode(claims, settings.tool_private_key_pem, algorithm="RS256")
