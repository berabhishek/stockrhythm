import json
import pytest
from stockrhythm.models import UniverseFilterSpec, FilterCondition, FilterOp, SortSpec, SortDir
from stockrhythm.client import _model_dump

def test_universe_filter_spec_serialization():
    """
    Verify that UniverseFilterSpec with Enums serializes to JSON-safe primitives.
    This tests the fix for Pydantic v2 Enum serialization.
    """
    spec = UniverseFilterSpec(
        candidates={"type": "watchlist", "symbols": ["RELIANCE"]},
        conditions=[
            FilterCondition(field="last_price", op=FilterOp.GT, value=100)
        ],
        sort=[
            SortSpec(field="last_price", direction=SortDir.DESC)
        ]
    )

    # Dump the model using our helper
    dumped = _model_dump(spec)

    # Assertions on dumped types (should be strings, not Enum objects)
    assert isinstance(dumped["conditions"][0]["op"], str)
    assert dumped["conditions"][0]["op"] == "gt"
    assert isinstance(dumped["sort"][0]["direction"], str)
    assert dumped["sort"][0]["direction"] == "desc"

    # Crucial test: JSON serialization
    try:
        json_str = json.dumps(dumped)
        assert isinstance(json_str, str)
        # Verify it contains the values
        assert '"op": "gt"' in json_str
        assert '"direction": "desc"' in json_str
    except TypeError as e:
        pytest.fail(f"JSON serialization failed: {e}")

if __name__ == "__main__":
    test_universe_filter_spec_serialization()
