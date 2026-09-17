import random

from generator.domains import DOMAINS
from generator.messiness import MESSINESS_PROFILES, apply_messiness


def _build_rows(domain_name, row_count, rng):
    from faker import Faker

    domain = DOMAINS[domain_name]
    fake = Faker()
    fake.seed_instance(1234)
    return [domain.build_row(fake, rng, i) for i in range(row_count)], domain


def test_low_messiness_never_drifts_schema():
    rng = random.Random(1)
    rows, domain = _build_rows("ecommerce_orders", 200, rng)

    result = apply_messiness(rows, domain.fieldnames, domain.id_field, MESSINESS_PROFILES["low"], rng)

    for row in result:
        assert set(row) == set(domain.fieldnames)


def test_high_messiness_introduces_nulls_duplicates_and_drift():
    rng = random.Random(2)
    rows, domain = _build_rows("ecommerce_orders", 500, rng)
    original_count = len(rows)

    result = apply_messiness(rows, domain.fieldnames, domain.id_field, MESSINESS_PROFILES["high"], rng)

    assert len(result) > original_count  # duplicates appended

    has_null = any(
        row[field] is None for row in result[:original_count] for field in domain.fieldnames if field in row
    )
    assert has_null

    drifted_keys = {key for row in result for key in row} - set(domain.fieldnames)
    assert drifted_keys  # schema drift added at least one unexpected/renamed key


def test_ids_are_never_nulled():
    rng = random.Random(3)
    rows, domain = _build_rows("hr_employees", 300, rng)

    result = apply_messiness(rows, domain.fieldnames, domain.id_field, MESSINESS_PROFILES["high"], rng)

    assert all(row.get(domain.id_field) not in (None, "") for row in result if domain.id_field in row)
