import pytest

from app.code_runner import CodeRunnerError, run_python_script

DEDUP_SCRIPT = """
import json

with open("input.json") as f:
    rows = json.load(f)

seen = {}
for row in rows:
    seen[row["order_id"]] = row

with open("output.json", "w") as f:
    json.dump(list(seen.values()), f)
"""


def test_run_python_script_reads_input_and_writes_output():
    rows = [{"order_id": "A", "x": 1}, {"order_id": "A", "x": 1}, {"order_id": "B", "x": 2}]

    output = run_python_script(DEDUP_SCRIPT, rows)

    assert len(output) == 2
    assert {row["order_id"] for row in output} == {"A", "B"}


def test_run_python_script_respects_custom_filenames():
    script = """
import json
with open("orders.json") as f:
    rows = json.load(f)
with open("cleaned.json", "w") as f:
    json.dump(rows, f)
"""
    output = run_python_script(script, [{"a": 1}], input_filename="orders.json", output_filename="cleaned.json")
    assert output == [{"a": 1}]


def test_run_python_script_raises_on_nonzero_exit():
    script = "raise RuntimeError('boom')"
    with pytest.raises(CodeRunnerError, match="exited with code"):
        run_python_script(script, [])


def test_run_python_script_raises_when_no_output_written():
    script = "pass"
    with pytest.raises(CodeRunnerError, match="did not write an output file"):
        run_python_script(script, [])


def test_run_python_script_raises_on_invalid_output_json():
    script = """
with open("output.json", "w") as f:
    f.write("not json")
"""
    with pytest.raises(CodeRunnerError, match="not valid JSON"):
        run_python_script(script, [])


def test_run_python_script_raises_on_timeout():
    script = "import time; time.sleep(5)"
    with pytest.raises(CodeRunnerError, match="timed out"):
        run_python_script(script, [], timeout=0.5)


def test_run_python_script_cannot_read_parent_environment():
    script = """
import json, os
with open("output.json", "w") as f:
    json.dump([{"secret_seen": os.environ.get("FDE_TEST_SECRET")}], f)
"""
    import os as _os

    _os.environ["FDE_TEST_SECRET"] = "do-not-leak"
    try:
        output = run_python_script(script, [])
    finally:
        del _os.environ["FDE_TEST_SECRET"]

    assert output == [{"secret_seen": None}]
