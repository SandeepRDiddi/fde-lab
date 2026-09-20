import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.compliance import evaluate_submission
from app.database import get_db
from app.grading import GradingError, evaluate_technical_submission
from app.models import ApprovalStatus, ScenarioInstance, ScenarioStatus, Submission
from app.schemas import SubmissionCreate, SubmissionDecision, SubmissionRead
from app.tasks import apply_submission_decision, auto_decide_submission, revoke_task_if_pending

router = APIRouter(prefix="/scenario-instances/{instance_id}/submissions", tags=["submissions"])


def _get_instance_or_404(instance_id: uuid.UUID, db: Session) -> ScenarioInstance:
    instance = db.get(ScenarioInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Scenario instance not found")
    return instance


def _get_submission_or_404(instance_id: uuid.UUID, submission_id: uuid.UUID, db: Session) -> Submission:
    submission = db.get(Submission, submission_id)
    if submission is None or submission.scenario_instance_id != instance_id:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


def _parse_approval_config(config: dict) -> tuple[float | None, ApprovalStatus | None]:
    """WHERE clause of AC2: config["approval_workflow"] is optional. When
    present it must carry both a positive review_delay_seconds and an
    auto_decision of "approved"/"rejected" — a scenario with neither key
    leaves the submission in pending_review until a manual decision."""
    approval_config = (config or {}).get("approval_workflow") or {}
    review_delay_seconds = approval_config.get("review_delay_seconds")
    auto_decision_raw = approval_config.get("auto_decision")

    if (review_delay_seconds is None) != (auto_decision_raw is None):
        raise HTTPException(
            status_code=422,
            detail="config.approval_workflow needs both review_delay_seconds and auto_decision, or neither",
        )
    if review_delay_seconds is None:
        return None, None

    if (
        not isinstance(review_delay_seconds, (int, float))
        or isinstance(review_delay_seconds, bool)
        or review_delay_seconds <= 0
    ):
        raise HTTPException(status_code=422, detail="review_delay_seconds must be a positive number")

    try:
        auto_decision = ApprovalStatus(auto_decision_raw)
    except ValueError:
        auto_decision = None
    if auto_decision not in (ApprovalStatus.approved, ApprovalStatus.rejected):
        raise HTTPException(status_code=422, detail="auto_decision must be 'approved' or 'rejected'")

    return review_delay_seconds, auto_decision


@router.post("", response_model=SubmissionRead, status_code=201)
def create_submission(
    instance_id: uuid.UUID, payload: SubmissionCreate, db: Session = Depends(get_db)
) -> SubmissionRead:
    """AC1: evaluates the submission against the scenario's compliance
    checklist (config["compliance_checklist"]) itself -- this is the actual
    enforcement point, not just a client-side check the frontend could skip
    by calling this endpoint directly. A failing submission is rejected
    (422) and never persisted; only a passing one moves to pending_review.
    FDE-013 AC1-2: when the scenario also configures config["technical_task"],
    content must additionally pass app/grading.py's correctness check (run
    against the instance's own synthetic dataset) -- both gates must pass.
    AC2: optionally schedules an auto-decision per the scenario's configured
    review delay."""
    instance = _get_instance_or_404(instance_id, db)
    if instance.status == ScenarioStatus.closed:
        raise HTTPException(status_code=409, detail="Scenario instance is closed")

    compliance_rules = instance.config.get("compliance_checklist") or []
    passed, failures = evaluate_submission(payload.content, compliance_rules)
    if not passed:
        raise HTTPException(
            status_code=422,
            detail={"message": "Submission failed the compliance checklist", "failures": failures},
        )

    grading_result: dict | None = None
    technical_task = instance.config.get("technical_task")
    if technical_task:
        try:
            graded_passed, grading_failures = evaluate_technical_submission(
                payload.content, instance.dataset_location, technical_task
            )
        except GradingError as exc:
            raise HTTPException(status_code=422, detail={"message": str(exc), "failures": []}) from exc
        if not graded_passed:
            raise HTTPException(
                status_code=422,
                detail={"message": "Submission failed the technical task's grader", "failures": grading_failures},
            )
        grading_result = {"task_type": technical_task.get("task_type"), "passed": True}

    review_delay_seconds, auto_decision = _parse_approval_config(instance.config)

    submission = Submission(
        scenario_instance_id=instance_id,
        content=payload.content,
        status=ApprovalStatus.pending_review,
        grading_result=grading_result,
    )
    if review_delay_seconds is not None:
        submission.review_deadline_at = datetime.now(timezone.utc) + timedelta(seconds=review_delay_seconds)
        submission.auto_decision = auto_decision

    db.add(submission)
    db.commit()
    db.refresh(submission)

    if submission.review_deadline_at is not None:
        try:
            result = auto_decide_submission.apply_async(
                args=[str(submission.id)], eta=submission.review_deadline_at
            )
            submission.auto_decide_task_id = result.id
            db.commit()
            db.refresh(submission)
        except Exception:
            # Broker unreachable -- the submission is already recorded (it
            # just won't auto-resolve on schedule and needs a manual
            # decision instead), so this shouldn't fail the request.
            pass

    return submission


@router.get("", response_model=list[SubmissionRead])
def list_submissions(instance_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Submission]:
    """FDE-009 AC3: lets an instructor console find a student's submission(s)
    for an instance without already knowing a submission id."""
    _get_instance_or_404(instance_id, db)
    return (
        db.query(Submission)
        .filter(Submission.scenario_instance_id == instance_id)
        .order_by(Submission.created_at)
        .all()
    )


@router.get("/{submission_id}", response_model=SubmissionRead)
def get_submission(
    instance_id: uuid.UUID, submission_id: uuid.UUID, db: Session = Depends(get_db)
) -> SubmissionRead:
    _get_instance_or_404(instance_id, db)
    return _get_submission_or_404(instance_id, submission_id, db)


@router.patch("/{submission_id}/decision", response_model=SubmissionRead)
def decide_submission(
    instance_id: uuid.UUID,
    submission_id: uuid.UUID,
    payload: SubmissionDecision,
    db: Session = Depends(get_db),
) -> SubmissionRead:
    """AC3: manual approve/reject — used when a scenario has no configured
    review delay, or an instructor decides before the auto-decision fires."""
    _get_instance_or_404(instance_id, db)
    submission = _get_submission_or_404(instance_id, submission_id, db)

    if submission.status != ApprovalStatus.pending_review:
        raise HTTPException(status_code=409, detail="Submission is not pending review")

    revoke_task_if_pending(submission.auto_decide_task_id)

    if not apply_submission_decision(db, submission, payload.decision):
        # Lost a race with the auto-decide task between the check above and
        # this call -- it already decided the submission first.
        raise HTTPException(status_code=409, detail="Submission was already decided")
    return submission
