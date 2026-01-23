from stockrhythm.filters import UniverseFilter
from stockrhythm.models import FilterOp, SortDir


def test_universe_filter_builder_outputs_spec():
    builder = (
        UniverseFilter.from_watchlist(["AAA", "BBB"], refresh_seconds=5)
        .where("last_price", FilterOp.GT, 100)
        .sort_by("last_price", SortDir.ASC)
    )

    spec = builder.build()

    assert spec.candidates == {"type": "watchlist", "symbols": ["AAA", "BBB"]}
    assert spec.refresh_seconds == 5
    assert spec.max_symbols == 2
    assert len(spec.conditions) == 1
    assert spec.conditions[0].field == "last_price"
    assert spec.conditions[0].op.value == "gt"
    assert spec.conditions[0].value == 100
    assert spec.sort[0].field == "last_price"
    assert spec.sort[0].direction == SortDir.ASC


def test_universe_filter_from_index_defaults():
    builder = UniverseFilter.from_index("NIFTY500")
    spec = builder.build()

    assert spec.candidates == {"type": "index", "name": "NIFTY500"}
    assert spec.refresh_seconds == 60
    assert spec.max_symbols == 50
