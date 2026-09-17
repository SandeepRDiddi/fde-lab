"""Assignment and Grade Services client (acceptance criterion 4): pushes a
completion score back to the LMS gradebook once a scenario finishes.

Only usable when the launch's AGS claim was present -- callers should check
`launch.ags is not None` before calling `publish_score`.
"""
import datetime as dt
from typing import Optional

import httpx

from .config import settings
from .launch import LtiLaunch
from .services_auth import get_access_token

AGS_SCORE_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
SCORE_MEDIA_TYPE = "application/vnd.ims.lis.v1.score+json"


def publish_score(
    launch: LtiLaunch,
    *,
    score_given: float,
    score_maximum: float,
    lineitem_url: Optional[str] = None,
) -> None:
    if launch.ags is None:
        raise ValueError("This launch's platform/deployment does not support AGS")

    lineitem_url = lineitem_url or launch.ags.get("lineitem")
    if not lineitem_url:
        raise ValueError(
            "No lineitem URL on the launch claim or passed explicitly -- the "
            "scenario engine must create/select a lineitem via the AGS "
            "lineitems endpoint first if the resource link didn't come with one"
        )

    platform = settings.platform_for(launch.issuer, launch.client_id)
    if platform is None:
        raise ValueError(f"Unregistered platform: {launch.issuer}")

    access_token = get_access_token(platform, AGS_SCORE_SCOPE)
    response = httpx.post(
        f"{lineitem_url}/scores",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": SCORE_MEDIA_TYPE,
        },
        json={
            "userId": launch.subject,
            "scoreGiven": score_given,
            "scoreMaximum": score_maximum,
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        timeout=10.0,
    )
    response.raise_for_status()
