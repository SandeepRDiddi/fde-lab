"""LTI 1.3 launch service -- the LMS entry point into FDE Lab (FDE-011).

Routes:
  GET/POST /lti/login    step 1 of the OIDC launch: redirect to the platform
  POST     /lti/launch   step 2: validate the id_token, land the student in
                          their scenario instance with a session already set
  GET      /.well-known/jwks.json   this tool's public key, for the platform
  GET      /internal/lti-contexts/{key}/roster   NRPS roster pull (AC3)
  POST     /internal/lti-contexts/{key}/scores   AGS score push (AC4)
"""
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from . import ags, nrps
from .config import settings
from .keys import tool_jwks
from .launch import LtiLaunch, validate_launch
from .launch_context_cache import recall, remember
from .oidc_login import build_authentication_redirect
from .scenario_client import resolve_scenario_instance
from .session import issue_session_token

app = FastAPI(title="FDE Lab LTI launch service")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/.well-known/jwks.json")
def jwks():
    try:
        return tool_jwks()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _login_params(request: Request) -> dict:
    if request.method == "GET":
        return dict(request.query_params)
    form = await request.form()
    return dict(form)


@app.api_route("/lti/login", methods=["GET", "POST"])
async def lti_login(request: Request):
    params = await _login_params(request)
    try:
        iss = params["iss"]
        login_hint = params["login_hint"]
        target_link_uri = params["target_link_uri"]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Missing required login param: {exc}") from exc

    redirect_url = build_authentication_redirect(
        iss=iss,
        login_hint=login_hint,
        target_link_uri=target_link_uri,
        client_id=params.get("client_id"),
        lti_deployment_id=params.get("lti_deployment_id"),
        lti_message_hint=params.get("lti_message_hint"),
    )
    return RedirectResponse(redirect_url, status_code=302)


@app.post("/lti/launch")
def lti_launch(state: str = Form(...), id_token: str = Form(...)):
    # Plain `def`, not `async def`: this handler makes several blocking
    # network calls (platform JWKS fetch, scenario-engine lookup) with no
    # async client -- FastAPI runs sync route functions in a threadpool, so
    # a slow platform/backend doesn't stall the event loop for every other
    # in-flight request.
    launch = validate_launch(state=state, id_token=id_token)
    scenario = resolve_scenario_instance(launch)
    session_token = issue_session_token(launch, scenario)
    remember(launch)

    response = RedirectResponse(
        f"{settings.frontend_base_url}{scenario.launch_path}", status_code=303
    )
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        # SameSite=None requires Secure (browsers reject the combination
        # otherwise) -- only used when the cookie is actually secure, i.e.
        # real deployments where this redirect is cross-site from the LMS.
        samesite="none" if settings.session_cookie_secure else "lax",
    )
    return response


def _launch_from_context(ctx: dict, subject: Optional[str] = None) -> LtiLaunch:
    return LtiLaunch(
        subject=subject or "",
        issuer=ctx["issuer"],
        client_id=ctx["client_id"],
        deployment_id=ctx["deployment_id"],
        context_id=ctx["context_id"],
        roles=[],
        name=None,
        email=None,
        nrps=ctx.get("nrps"),
        ags=ctx.get("ags"),
    )


@app.get("/internal/lti-contexts/{context_key}/roster")
def get_roster(context_key: str):
    ctx = recall(context_key)
    if ctx is None:
        raise HTTPException(status_code=404, detail="No cached launch for this context (or it expired)")
    launch = _launch_from_context(ctx)
    if launch.nrps is None:
        raise HTTPException(status_code=422, detail="This LMS context doesn't support NRPS")
    return {"members": nrps.fetch_roster(launch)}


class ScorePush(BaseModel):
    student_sub: str
    score_given: float
    score_maximum: float


@app.post("/internal/lti-contexts/{context_key}/scores")
def post_score(context_key: str, payload: ScorePush):
    ctx = recall(context_key)
    if ctx is None:
        raise HTTPException(status_code=404, detail="No cached launch for this context (or it expired)")
    launch = _launch_from_context(ctx, subject=payload.student_sub)
    if launch.ags is None:
        raise HTTPException(status_code=422, detail="This LMS context doesn't support AGS")
    ags.publish_score(launch, score_given=payload.score_given, score_maximum=payload.score_maximum)
    return {"status": "submitted"}
