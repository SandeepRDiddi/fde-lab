"""Names and Roles Provisioning Service client (acceptance criterion 3).

Only usable when the launch's NRPS claim was present -- callers should check
`launch.nrps is not None` before calling `fetch_roster`, since not every LMS
deployment enables this service.
"""
from typing import Any, Dict, List

import httpx

from .config import settings
from .launch import LtiLaunch
from .services_auth import get_access_token

NRPS_SCOPE = "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"


def fetch_roster(launch: LtiLaunch) -> List[Dict[str, Any]]:
    if launch.nrps is None:
        raise ValueError("This launch's platform/deployment does not support NRPS")

    platform = settings.platform_for(launch.issuer, launch.client_id)
    if platform is None:
        raise ValueError(f"Unregistered platform: {launch.issuer}")

    access_token = get_access_token(platform, NRPS_SCOPE)
    response = httpx.get(
        launch.nrps["context_memberships_url"],
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json().get("members", [])
