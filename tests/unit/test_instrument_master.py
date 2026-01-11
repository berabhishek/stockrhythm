from apps.backend.src.instrument_master import InstrumentMaster


def test_instrument_master_load_and_resolve(tmp_path):
    csv_path = tmp_path / "instruments.csv"
    csv_path.write_text(
        "symbol,exchange,series,isin,nse_scrip_code,bse_code\n"
        "RELIANCE,NSE,EQ,INE002A01018,2885,500325\n"
        "TCS,NSE,EQ,INE467B01029,11536,532540\n"
    )

    master = InstrumentMaster(csv_path=str(csv_path))
    master.load()

    assert master.resolve("RELIANCE") == "nse_cm|2885"
    assert master.resolve("tcs") == "nse_cm|11536"
    assert master.resolve("UNKNOWN") is None
