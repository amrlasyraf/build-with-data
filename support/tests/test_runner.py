import pytest

from step_00_setup import run_pipeline as runner


def test_layer_must_be_selected_explicitly():
    with pytest.raises(SystemExit) as error:
        runner.main([])
    assert error.value.code == 2


def test_gold_command_does_not_run_upstream(monkeypatch, tmp_path):
    import duckdb
    path = tmp_path / "runner.duckdb"
    monkeypatch.setattr(runner, "DATABASE_PATH", path)
    def unexpected(*args):
        raise AssertionError("Gold must not touch upstream stages")
    monkeypatch.setattr(runner, "read_sources", unexpected)
    monkeypatch.setattr(runner, "prepare_database", unexpected)
    monkeypatch.setattr(runner, "build_silver", unexpected)
    # Fail Gold deliberately to also verify the process-level failure contract.
    monkeypatch.setattr(runner, "build_gold", lambda path: (_ for _ in ()).throw(ValueError("Gold failed")))
    assert runner.main(["--layer", "gold"]) == 1


def test_all_stops_after_silver_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "read_sources", lambda path: [])
    monkeypatch.setattr(runner, "prepare_database", lambda path: None)
    monkeypatch.setattr(runner, "load_bronze_tables", lambda *args: calls.append("bronze") or {})
    def fail(path):
        calls.append("silver")
        raise ValueError("Silver failed")
    monkeypatch.setattr(runner, "build_silver", fail)
    monkeypatch.setattr(runner, "build_gold", lambda path: calls.append("gold"))
    assert runner.main(["--layer", "all"]) == 1
    assert calls == ["bronze", "silver"]
