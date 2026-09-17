from __future__ import annotations

import random
import secrets

from faker import Faker

from generator.domains import DOMAINS
from generator.messiness import MESSINESS_PROFILES, apply_messiness

# Bounds the in-memory row list and the single joined upload body built in
# S3DatasetStore.upload — row_count comes from caller-controlled scenario
# config (config.data_gen.row_count), not a trusted internal value.
MAX_ROW_COUNT = 100_000


def generate_dataset(
    *, domain: str, row_count: int, messiness: str, seed: bytes | None = None
) -> list[dict]:
    """Build a fresh dataset for one scenario instance run.

    `seed` defaults to a freshly drawn random seed rather than anything
    derived from the scenario/cohort, so no two calls — even for the same
    domain/messiness — ever produce the same content (FDE-003 AC4).
    """
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain: {domain!r}. Known domains: {sorted(DOMAINS)}")
    if messiness not in MESSINESS_PROFILES:
        raise ValueError(
            f"Unknown messiness level: {messiness!r}. Known levels: {sorted(MESSINESS_PROFILES)}"
        )
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0:
        raise ValueError(f"row_count must be a non-negative integer, got {row_count!r}")
    if row_count > MAX_ROW_COUNT:
        raise ValueError(f"row_count exceeds the maximum of {MAX_ROW_COUNT} (got {row_count})")

    rng = random.Random(seed if seed is not None else secrets.token_bytes(16))
    fake = Faker()
    fake.seed_instance(rng.randrange(2**32))

    domain_def = DOMAINS[domain]
    rows = [domain_def.build_row(fake, rng, i) for i in range(row_count)]

    profile = MESSINESS_PROFILES[messiness]
    return apply_messiness(rows, domain_def.fieldnames, domain_def.id_field, profile, rng)
