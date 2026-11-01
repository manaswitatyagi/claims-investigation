import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.loader import load_claim  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "data", "fixtures")
RECORDINGS = os.path.join(ROOT, "src", "llm", "recordings")


@pytest.fixture
def smoke_claim():
    return load_claim(os.path.join(FIXTURES, "claim_000_smoke", "claim.json"))


@pytest.fixture
def zero_conflict_claim():
    return load_claim(os.path.join(FIXTURES, "claim_000_zero_conflict", "claim.json"))


@pytest.fixture
def claim_001():
    return load_claim(os.path.join(FIXTURES, "claim_001", "claim.json"))


@pytest.fixture
def recorded_client():
    from src.llm.client import RecordedClient

    def _make(fixture):
        return RecordedClient.from_dir(os.path.join(RECORDINGS, fixture))
    return _make
