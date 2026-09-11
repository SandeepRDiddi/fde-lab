"""
FDE Lab -- autonomous story orchestrator.

Picks the next eligible story from STORIES.md, hands it to Claude Code
(headless), commits, pushes, and opens a PR -- then loops to the next
eligible story. Stops when nothing is left that isn't blocked on a
dependency you haven't merged yet.

Nothing here merges to main. The PR review is still the real checkpoint,
per AGENT-WORKFLOW.md -- this just automates everything upstream of that.

Hardening in this version: every step that can fail (a bad git state, a
crashed agent run, an existing branch from a previous attempt, an empty
diff, a duplicate PR) is caught, logged to orchestrator.log, and treated
as "skip this story, keep going" rather than "stop the whole run" -- so
one bad story overnight doesn't block the rest of the backlog.

Prerequisites:
    pip install langgraph
    gh auth login          # GitHub CLI, one-time
    claude --version       # already set up on your subscription

Run it from the root of your cloned fde-lab repo:
    python orchestrator/orchestrator.py
"""

import json
import logging
import re
import subprocess
import traceback
from pathlib import Path
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END

STORIES_MD = Path("STORIES.md")
STORIES_DIR = Path("stories")
MAX_STORIES_PER_RUN = 20  # safety valve -- stops a runaway loop even if a bug slips through

logging.basicConfig(
    filename="orchestrator.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("orchestrator")


def log_and_print(msg: str, level: str = "info") -> None:
    print(msg)
    getattr(log, level)(msg)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class State(TypedDict, total=False):
    story_id: Optional[str]
    story_title: Optional[str]
    story_file: Optional[Path]
    branch: Optional[str]
    agent_result: Optional[str]
    done: bool
    failed: bool
    error: Optional[str]
    skipped: set
    completed: list
    iterations: int


# ---------------------------------------------------------------------------
# STORIES.md parsing
# ---------------------------------------------------------------------------

def parse_stories() -> list[dict]:
    rows = []
    for line in STORIES_MD.read_text().splitlines():
        line = line.strip()
        if not line.startswith("| FDE-"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        story_id, title, priority, depends_on, status = cols
        deps = [] if depends_on in ("\u2014", "-", "") else [
            d.strip() for d in depends_on.split(",")
        ]
        rows.append(
            {
                "id": story_id,
                "title": title,
                "priority": priority,
                "depends_on": deps,
                "status": status,
            }
        )
    return rows


def next_eligible_story(rows: list[dict], skipped: set) -> Optional[dict]:
    done_ids = {r["id"] for r in rows if r["status"] == "Done"}
    candidates = [
        r
        for r in rows
        if r["status"] == "Not started"
        and r["id"] not in skipped
        and all(d in done_ids for d in r["depends_on"])
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda r: r["priority"])  # "P0" < "P1" sorts correctly
    return candidates[0]


def find_story_file(story_id: str) -> Path:
    matches = list(STORIES_DIR.glob(f"{story_id}-*.md"))
    if not matches:
        raise FileNotFoundError(f"No story file found for {story_id}")
    return matches[0]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def mark_status(story_id: str, new_status: str) -> None:
    text = STORIES_MD.read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(f"| {story_id} |"):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            cols[-1] = new_status
            lines[i] = "| " + " | ".join(cols) + " |"
            break
    STORIES_MD.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log_and_print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.stdout:
        log.info(result.stdout)
    if result.returncode != 0:
        log.error(result.stderr or "")
        if check:
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr}"
            )
    return result


def working_tree_clean() -> bool:
    result = run(["git", "status", "--porcelain"], check=False)
    return result.stdout.strip() == ""


def branch_exists_locally(branch: str) -> bool:
    result = run(["git", "rev-parse", "--verify", branch], check=False)
    return result.returncode == 0


def record_failure(state: State, story_id: str, message: str) -> State:
    """Log a failure, preserve any partial work for inspection, return to a
    clean main, and mark this story so the same run doesn't retry it."""
    log_and_print(f"[{story_id}] FAILED: {message}", level="error")
    # Preserve whatever partial work exists rather than losing it
    run(["git", "add", "-A"], check=False)
    run(["git", "commit", "-m", f"wip: failed unattended attempt at {story_id}"], check=False)
    run(["git", "checkout", "main"], check=False)
    skipped = set(state.get("skipped", set()))
    skipped.add(story_id)
    return {"failed": True, "error": message, "skipped": skipped}


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def pick_story(state: State) -> State:
    iterations = state.get("iterations", 0) + 1
    if iterations > MAX_STORIES_PER_RUN:
        log_and_print(
            f"Hit the {MAX_STORIES_PER_RUN}-story safety cap for this run. Stopping.",
            "warning",
        )
        return {"done": True}

    if not working_tree_clean():
        log_and_print(
            "Working tree isn't clean at the start of a pick -- stopping rather "
            "than risking uncommitted work. Clean up manually and rerun.",
            "error",
        )
        return {"done": True}

    try:
        rows = parse_stories()
    except Exception as e:
        log_and_print(f"Could not parse STORIES.md: {e}", "error")
        return {"done": True}

    skipped = state.get("skipped", set())
    story = next_eligible_story(rows, skipped)
    if story is None:
        log_and_print("No eligible stories left to pick up this run. Stopping.")
        return {"done": True}

    try:
        story_file = find_story_file(story["id"])
    except FileNotFoundError as e:
        return record_failure(state, story["id"], str(e))

    log_and_print(f"Picked up {story['id']}: {story['title']}")
    return {
        "story_id": story["id"],
        "story_title": story["title"],
        "story_file": story_file,
        "done": False,
        "failed": False,
        "error": None,
        "iterations": iterations,
    }


def create_branch(state: State) -> State:
    story_id = state["story_id"]
    try:
        branch = f"feature/{story_id.lower()}-{slugify(state['story_title'])}"
        run(["git", "checkout", "main"])
        run(["git", "pull"])
        if branch_exists_locally(branch):
            log_and_print(
                f"[{story_id}] Branch {branch} already exists locally from a "
                f"previous attempt -- deleting and starting fresh."
            )
            run(["git", "branch", "-D", branch])
        run(["git", "checkout", "-b", branch])
        return {"branch": branch}
    except Exception as e:
        return record_failure(state, story_id, f"branch setup failed: {e}")


def run_agent(state: State) -> State:
    if state.get("failed"):
        return {}
    story_id = state["story_id"]
    story_file = state["story_file"]
    prompt = (
        f"Implement {story_id} exactly as specified in {story_file}. "
        f"First read the 'Architecture ref' field in that file and review the "
        f"matching section of architecture.md. Follow the acceptance criteria "
        f"precisely. When finished, append a dated entry under the "
        f"'## Implementation log' heading in {story_file} describing what you "
        f"built and any deviation from the spec -- do not remove the existing "
        f"placeholder line, add your entry above it."
    )
    try:
        result = run(
            [
                "claude", "-p", prompt,
                "--permission-mode", "acceptEdits",
                "--output-format", "json",
            ],
            check=False,
        )
        if result.returncode != 0:
            return record_failure(
                state, story_id, f"claude exited {result.returncode}: {(result.stderr or '')[:500]}"
            )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return record_failure(
                state, story_id, f"claude output wasn't valid JSON: {result.stdout[:500]}"
            )
        if data.get("is_error"):
            return record_failure(
                state, story_id, f"claude reported an error: {str(data.get('result', ''))[:500]}"
            )
        return {"agent_result": data.get("result", "")}
    except Exception as e:
        return record_failure(state, story_id, f"agent run raised: {e}")


def commit_and_push(state: State) -> State:
    if state.get("failed"):
        return {}
    story_id = state["story_id"]
    try:
        if working_tree_clean():
            return record_failure(state, story_id, "agent made no file changes -- nothing to commit")
        run(["git", "add", "-A"])
        run(["git", "commit", "-m", f"feat: implement {story_id}"])
        run(["git", "push", "-u", "origin", state["branch"], "--force-with-lease"])
        return {}
    except Exception as e:
        return record_failure(state, story_id, f"commit/push failed: {e}")


def open_pr(state: State) -> State:
    if state.get("failed"):
        return {}
    story_id = state["story_id"]
    try:
        result = run(
            [
                "gh", "pr", "create",
                "--title", f"{story_id}: implementation",
                "--body",
                f"Unattended implementation of {story_id}, generated by the "
                f"LangGraph orchestrator while you were away. Needs human "
                f"review before merge -- nothing here has been checked yet.",
                "--head", state["branch"],
            ],
            check=False,
        )
        if result.returncode != 0:
            stderr_lower = (result.stderr or "").lower()
            if "already exists" in stderr_lower:
                log_and_print(f"[{story_id}] PR already exists for this branch -- continuing.")
                return {}
            return record_failure(state, story_id, f"gh pr create failed: {(result.stderr or '')[:500]}")
        return {}
    except Exception as e:
        return record_failure(state, story_id, f"opening PR failed: {e}")


def mark_in_review(state: State) -> State:
    if state.get("failed"):
        return {}
    story_id = state["story_id"]
    try:
        run(["git", "checkout", "main"])
        run(["git", "pull"])
        mark_status(story_id, "In review")
        run(["git", "add", "STORIES.md"])
        run(["git", "commit", "-m", f"chore: mark {story_id} in review"])
        run(["git", "push"])
        log_and_print(f"[{story_id}] Done for this run -- PR open, status updated.")
        completed = list(state.get("completed", [])) + [story_id]
        return {"completed": completed}
    except Exception as e:
        return record_failure(state, story_id, f"updating STORIES.md status failed: {e}")


def route_after_pick(state: State) -> str:
    if state.get("done"):
        return "stop"
    if state.get("failed"):
        return "retry"  # a pick-time failure (e.g. missing story file) -- try the next one
    return "continue"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(State)
    graph.add_node("pick_story", pick_story)
    graph.add_node("create_branch", create_branch)
    graph.add_node("run_agent", run_agent)
    graph.add_node("commit_and_push", commit_and_push)
    graph.add_node("open_pr", open_pr)
    graph.add_node("mark_in_review", mark_in_review)

    graph.set_entry_point("pick_story")
    graph.add_conditional_edges(
        "pick_story",
        route_after_pick,
        {"stop": END, "retry": "pick_story", "continue": "create_branch"},
    )
    graph.add_edge("create_branch", "run_agent")
    graph.add_edge("run_agent", "commit_and_push")
    graph.add_edge("commit_and_push", "open_pr")
    graph.add_edge("open_pr", "mark_in_review")
    graph.add_edge("mark_in_review", "pick_story")  # loop back for the next one

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    try:
        final_state = app.invoke({}, config={"recursion_limit": 200})
    except Exception:
        log_and_print("Orchestrator crashed unexpectedly:\n" + traceback.format_exc(), "error")
        raise

    completed = final_state.get("completed", [])
    skipped = final_state.get("skipped", set())
    print("\n--- Run summary ---")
    print(f"Opened PRs, awaiting your review: {', '.join(completed) or 'none'}")
    if skipped:
        print(f"Skipped due to errors (see orchestrator.log): {', '.join(sorted(skipped))}")
    print("Orchestrator run finished.")


# ---------------------------------------------------------------------------
# Setup notes
# ---------------------------------------------------------------------------
#
# 1. pip install langgraph
# 2. Install GitHub CLI and log in once: https://cli.github.com  ->  gh auth login
# 3. Make sure the claude command already works interactively in this repo
#    (i.e. you've logged in with your subscription already).
# 4. Run from the repo root: python orchestrator/orchestrator.py
#
# To let it run overnight instead of watching it:
#   nohup python orchestrator/orchestrator.py > orchestrator_stdout.log 2>&1 &
# (macOS/Linux; check orchestrator.log and orchestrator_stdout.log when you're
# back. On Windows, use Task Scheduler or
# start /B python orchestrator\orchestrator.py > orchestrator_stdout.log 2>&1)
#
# Your machine needs to stay on and awake for the duration -- disable sleep,
# or this stops the moment the OS suspends the process.
