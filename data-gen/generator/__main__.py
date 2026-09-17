"""CLI entry point invoked at cohort setup time.

    python -m generator <scenario-instance-id>
"""
from __future__ import annotations

import argparse
import uuid

from generator.run import generate_for_scenario_instance


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic dataset for a scenario instance.")
    parser.add_argument("instance_id", type=uuid.UUID)
    args = parser.parse_args()

    location = generate_for_scenario_instance(args.instance_id)
    print(location)


if __name__ == "__main__":
    main()
