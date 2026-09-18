import subprocess

import pytest

from app.provision import ProvisioningError, namespace_for, provision_cohort


@pytest.mark.parametrize(
    "cohort_id,expected",
    [
        ("acme-univ-cs101-fall26", "cohort-acme-univ-cs101-fall26"),
        ("Acme Univ / CS101 Fall'26", "cohort-acme-univ-cs101-fall-26"),
        ("  --leading-trailing--  ", "cohort-leading-trailing"),
    ],
)
def test_namespace_for_slugifies(cohort_id, expected):
    assert namespace_for(cohort_id) == expected


def test_namespace_for_truncates_long_ids():
    namespace = namespace_for("x" * 200)
    # "cohort-" (7 chars) + up to 53 slug chars stays comfortably under the
    # 63-char DNS label limit Kubernetes enforces on namespace names.
    assert len(namespace) <= 63
    assert namespace.startswith("cohort-")


def test_namespace_for_rejects_empty_after_slugify():
    with pytest.raises(ProvisioningError):
        namespace_for("!!!")


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr


def test_provision_cohort_invokes_helm_upgrade_install(tmp_path):
    calls = []

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return _FakeCompletedProcess(returncode=0)

    namespace = provision_cohort("acme-cs101", chart_dir=tmp_path, runner=fake_runner)

    assert namespace == "cohort-acme-cs101"
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[:3] == ["helm", "upgrade", "cohort-acme-cs101"]
    assert "--install" in cmd
    assert "--namespace" in cmd and cmd[cmd.index("--namespace") + 1] == "cohort-acme-cs101"
    # Without this, helm errors out on the very first provision of any
    # cohort, since the namespace doesn't exist yet.
    assert "--create-namespace" in cmd
    assert "--set" in cmd and cmd[cmd.index("--set") + 1] == "cohortId=acme-cs101"


def test_provision_cohort_is_idempotent_by_using_upgrade_install(tmp_path):
    """Calling this twice for the same cohort must not error just because
    the release/namespace already exists (both trigger paths in FDE-012
    AC2 can legitimately fire more than once)."""
    calls = []

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return _FakeCompletedProcess(returncode=0)

    provision_cohort("acme-cs101", chart_dir=tmp_path, runner=fake_runner)
    provision_cohort("acme-cs101", chart_dir=tmp_path, runner=fake_runner)

    assert len(calls) == 2
    assert all("--install" in cmd for cmd in calls)


def test_provision_cohort_raises_on_helm_failure(tmp_path):
    def failing_runner(cmd, **kwargs):
        return _FakeCompletedProcess(returncode=1, stderr="Error: namespaces \"cohort-x\" is forbidden")

    with pytest.raises(ProvisioningError, match="forbidden"):
        provision_cohort("x", chart_dir=tmp_path, runner=failing_runner)


def test_provision_cohort_passes_values_file_and_context(tmp_path):
    calls = []

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return _FakeCompletedProcess(returncode=0)

    provision_cohort(
        "acme-cs101",
        chart_dir=tmp_path,
        values_file="values-prod.yaml",
        kube_context="prod-cluster",
        runner=fake_runner,
    )

    cmd = calls[0]
    assert "-f" in cmd and cmd[cmd.index("-f") + 1] == "values-prod.yaml"
    assert "--kube-context" in cmd and cmd[cmd.index("--kube-context") + 1] == "prod-cluster"
