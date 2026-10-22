use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use rand::Rng;

/// Upper bound on a single packet's size (1 GiB); larger values are rejected.
const MAX_PACKET_BYTES: u64 = 1 << 30;
/// Upper bound on the base latency in milliseconds.
const MAX_LATENCY_MS: f64 = 60_000.0;
const NODE_ID_SPACE: u32 = 1024;
const MAX_TARGETS: usize = 5;

static SEQUENCE: AtomicU64 = AtomicU64::new(0);

/// Immutable telemetry frame. All fields are plain owned data, so the type is
/// `Send + Sync`; `frozen` lets PyO3 skip runtime borrow-checking locks.
#[pyclass(frozen, skip_from_py_object, module = "rust_telemetry")]
#[derive(Clone, Debug)]
pub struct TelemetryFrame {
    #[pyo3(get)]
    seq: u64,
    #[pyo3(get)]
    timestamp_ns: u64,
    #[pyo3(get)]
    bytes: u64,
    #[pyo3(get)]
    latency_ms: f64,
    #[pyo3(get)]
    target_nodes: Vec<u32>,
}

#[pymethods]
impl TelemetryFrame {
    /// Validate and process a raw packet's attributes into a frame.
    ///
    /// Raises `ValueError` for out-of-range / non-finite input and
    /// `OverflowError` (from PyO3 conversion) for negative or >u64 ints.
    #[staticmethod]
    fn process_raw_packet(bytes: u64, base_latency: f64) -> PyResult<Self> {
        if bytes == 0 || bytes > MAX_PACKET_BYTES {
            return Err(PyValueError::new_err(format!(
                "bytes must be in 1..={MAX_PACKET_BYTES}, got {bytes}"
            )));
        }
        if !base_latency.is_finite() || !(0.0..=MAX_LATENCY_MS).contains(&base_latency) {
            return Err(PyValueError::new_err(format!(
                "base_latency must be finite and in 0..={MAX_LATENCY_MS}, got {base_latency}"
            )));
        }

        let mut rng = rand::rng();

        // Simulated processing: jitter scales mildly with payload size.
        let size_penalty = (bytes as f64).log2() * 0.01;
        let jitter: f64 = rng.random_range(0.0..=base_latency.max(1.0) * 0.1);
        let latency_ms = base_latency + size_penalty + jitter;

        let n_targets = rng.random_range(1..=MAX_TARGETS);
        let mut target_nodes: Vec<u32> = Vec::with_capacity(n_targets);
        while target_nodes.len() < n_targets {
            let id = rng.random_range(0..NODE_ID_SPACE);
            if !target_nodes.contains(&id) {
                target_nodes.push(id);
            }
        }

        // A clock before the epoch yields 0 rather than panicking.
        let timestamp_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| u64::try_from(d.as_nanos()).unwrap_or(u64::MAX))
            .unwrap_or(0);

        Ok(Self {
            seq: SEQUENCE.fetch_add(1, Ordering::Relaxed),
            timestamp_ns,
            bytes,
            latency_ms,
            target_nodes,
        })
    }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new(py);
        d.set_item("seq", self.seq)?;
        d.set_item("timestamp_ns", self.timestamp_ns)?;
        d.set_item("bytes", self.bytes)?;
        d.set_item("latency_ms", self.latency_ms)?;
        d.set_item("target_nodes", &self.target_nodes)?;
        Ok(d)
    }

    fn __repr__(&self) -> String {
        format!(
            "TelemetryFrame(seq={}, bytes={}, latency_ms={:.3}, target_nodes={:?})",
            self.seq, self.bytes, self.latency_ms, self.target_nodes
        )
    }
}

#[pymodule]
fn rust_telemetry(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TelemetryFrame>()?;
    Ok(())
}
