"""Boundary stress test: bad input must raise Python exceptions, never crash."""
import math
import threading

import pytest

from rust_telemetry import TelemetryFrame

process = TelemetryFrame.process_raw_packet


def test_happy_path():
    f = process(1500, 10.0)
    assert f.bytes == 1500
    assert f.latency_ms >= 10.0
    assert 1 <= len(f.target_nodes) <= 5
    assert len(set(f.target_nodes)) == len(f.target_nodes)
    assert set(f.to_dict()) == {"seq", "timestamp_ns", "bytes", "latency_ms", "target_nodes"}


def test_seq_monotonic():
    a, b = process(100, 1.0), process(100, 1.0)
    assert b.seq > a.seq


@pytest.mark.parametrize("bad", [-1, -(2**63), 2**64, 2**200, 10**100])
def test_int_out_of_u64_range(bad):
    with pytest.raises(OverflowError):
        process(bad, 1.0)


@pytest.mark.parametrize("bad", [0, 2**30 + 1, 2**64 - 1])
def test_bytes_out_of_policy_range(bad):
    with pytest.raises(ValueError):
        process(bad, 1.0)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, -0.001, 1e300, 60_001.0])
def test_bad_latency(bad):
    with pytest.raises(ValueError):
        process(100, bad)


@pytest.mark.parametrize("args", [("x", 1.0), (1, "x"), (None, 1.0), (1.5, 1.0), ([], {})])
def test_wrong_types(args):
    with pytest.raises(TypeError):
        process(*args)


def test_frame_immutable():
    f = process(100, 1.0)
    with pytest.raises(AttributeError):
        f.bytes = 5


def test_threaded_use():
    errors = []

    def work():
        try:
            for _ in range(2000):
                process(1500, 5.0)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    ts = [threading.Thread(target=work) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors
