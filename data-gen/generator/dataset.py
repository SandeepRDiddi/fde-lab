from __future__ import annotations

import random
import secrets

from faker import Faker

from generator.domains import DOMAINS
from generator.messiness import MESSINESS_PROFILES, apply_messiness


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

    rng = random.Random(seed if seed is not None else secrets.token_bytes(16))
    fake = Faker()
    fake.seed_instance(rng.randrange(2**32))

    domain_def = DOMAINS[domain]
    rows = [domain_def.build_row(fake, rng, i) for i in range(row_count)]

    profile = MESSINESS_PROFILES[messiness]
    return apply_messiness(rows, domain_def.fieldnames, domain_def.id_field, profile, rng)
