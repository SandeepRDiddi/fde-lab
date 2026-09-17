import pytest

from generator.dataset import generate_dataset
from generator.domains import DOMAINS


@pytest.mark.parametrize("domain", list(DOMAINS))
def test_generate_dataset_matches_domain_schema(domain):
    rows = generate_dataset(domain=domain, row_count=50, messiness="low")

    domain_fields = set(DOMAINS[domain].fieldnames)
    for row in rows:
        # low messiness never drifts the schema, so every row's keys must be
        # exactly the domain's canonical fields (possibly with some nulled).
        assert set(row) == domain_fields


def test_generate_dataset_unknown_domain_raises():
    with pytest.raises(ValueError):
        generate_dataset(domain="not-a-real-domain", row_count=10, messiness="low")


def test_generate_dataset_unknown_messiness_raises():
    with pytest.raises(ValueError):
        generate_dataset(domain="ecommerce_orders", row_count=10, messiness="chaotic")


def test_two_runs_produce_demonstrably_different_datasets():
    first = generate_dataset(domain="ecommerce_orders", row_count=100, messiness="medium")
    second = generate_dataset(domain="ecommerce_orders", row_count=100, messiness="medium")

    assert first != second


def test_same_seed_is_reproducible_but_default_calls_never_reuse_it():
    seeded_a = generate_dataset(domain="ecommerce_orders", row_count=20, messiness="low", seed=b"fixed")
    seeded_b = generate_dataset(domain="ecommerce_orders", row_count=20, messiness="low", seed=b"fixed")
    assert seeded_a == seeded_b  # sanity check the RNG plumbing is deterministic given a seed

    unseeded_a = generate_dataset(domain="ecommerce_orders", row_count=20, messiness="low")
    unseeded_b = generate_dataset(domain="ecommerce_orders", row_count=20, messiness="low")
    assert unseeded_a != unseeded_b
