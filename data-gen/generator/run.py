from __future__ import annotations

import uuid

import httpx

from generator.config import settings
from generator.dataset import generate_dataset
from generator.storage import S3DatasetStore

DEFAULT_DOMAIN = "ecommerce_orders"
DEFAULT_ROW_COUNT = 500
DEFAULT_MESSINESS = "medium"


def generate_for_scenario_instance(
    instance_id: uuid.UUID,
    *,
    backend_base_url: str | None = None,
    store: S3DatasetStore | None = None,
) -> str:
    """Cohort-setup-time entry point (architecture.md → Synthetic data
    generation): reads the instance's own `config.data_gen` block for its
    domain/row_count/messiness (AC1-2), generates and uploads a fresh dataset
    (AC4), and records the resulting location back on the scenario instance
    (AC3)."""
    store = store or S3DatasetStore()

    with httpx.Client(base_url=backend_base_url or settings.backend_base_url) as client:
        response = client.get(f"/scenario-instances/{instance_id}")
        response.raise_for_status()
        instance = response.json()

        data_gen_config = instance["config"].get("data_gen", {})
        domain = data_gen_config.get("domain", DEFAULT_DOMAIN)
        row_count = data_gen_config.get("row_count", DEFAULT_ROW_COUNT)
        messiness = data_gen_config.get("messiness", DEFAULT_MESSINESS)

        rows = generate_dataset(domain=domain, row_count=row_count, messiness=messiness)

        # uuid4 per run (never the instance/cohort id alone) so a dataset is
        # never overwritten or reused across runs, even a re-run of the same
        # instance (FDE-003 AC4).
        key = f"datasets/{instance['cohort_id']}/{instance_id}/{uuid.uuid4().hex}.jsonl"
        location = store.upload(key, rows)

        try:
            patch_response = client.patch(
                f"/scenario-instances/{instance_id}/dataset",
                json={"dataset_location": location},
            )
            patch_response.raise_for_status()
        except httpx.HTTPError as exc:
            # The object is already uploaded at this point — surface its
            # location so a failed PATCH is reconcilable instead of a
            # silently orphaned S3 object with nothing pointing at it.
            raise RuntimeError(
                f"Uploaded dataset to {location} but failed to record it on "
                f"scenario instance {instance_id}: {exc}"
            ) from exc

    return location
