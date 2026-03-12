"""Acceptance tests for SPEC sections 2.1-2.5: QoS profile requirements."""

import os
import xml.etree.ElementTree as ET

import pytest

QOS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'qos', 'USER_QOS_PROFILES.xml')


@pytest.fixture(scope="module")
def profiles():
    tree = ET.parse(QOS_FILE)
    root = tree.getroot()
    library = root.find("qos_library")
    return {p.attrib["name"]: p for p in library.findall("qos_profile")}


def _text(element, path):
    node = element.find(path)
    assert node is not None, f"Missing element: {path}"
    return node.text.strip()


# ---- SPEC 2.1: Telemetry QoS ----

class TestSpec21Telemetry:
    """SPEC 2.1 - High-rate telemetry: best-effort, 200 ms deadline,
    exclusive ownership with strength 100, automatic liveliness 2 s."""

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["TelemetryProfile"].find("datawriter_qos")
        self.reader = profiles["TelemetryProfile"].find("datareader_qos")

    def test_best_effort_reliability(self):
        assert _text(self.writer, "reliability/kind") == "BEST_EFFORT_RELIABILITY_QOS"
        assert _text(self.reader, "reliability/kind") == "BEST_EFFORT_RELIABILITY_QOS"

    def test_keep_last_depth_1(self):
        assert _text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.writer, "history/depth") == "1"

    def test_deadline_200ms(self):
        assert _text(self.writer, "deadline/period/sec") == "0"
        assert _text(self.writer, "deadline/period/nanosec") == "200000000"
        assert _text(self.reader, "deadline/period/sec") == "0"
        assert _text(self.reader, "deadline/period/nanosec") == "200000000"

    def test_liveliness_automatic_2s(self):
        assert _text(self.writer, "liveliness/kind") == "AUTOMATIC_LIVELINESS_QOS"
        assert _text(self.writer, "liveliness/lease_duration/sec") == "2"

    def test_ownership_exclusive_strength_100(self):
        assert _text(self.writer, "ownership/kind") == "EXCLUSIVE_OWNERSHIP_QOS"
        assert _text(self.writer, "ownership_strength/value") == "100"


# ---- SPEC 2.2: Command QoS ----

class TestSpec22Command:
    """SPEC 2.2 - Reliable commands: reliable with 1 s blocking,
    keep-all history, transient-local durability."""

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["CommandProfile"].find("datawriter_qos")
        self.reader = profiles["CommandProfile"].find("datareader_qos")

    def test_reliable(self):
        assert _text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_max_blocking_time_1s(self):
        assert _text(self.writer, "reliability/max_blocking_time/sec") == "1"

    def test_keep_all_history(self):
        assert _text(self.writer, "history/kind") == "KEEP_ALL_HISTORY_QOS"
        assert _text(self.reader, "history/kind") == "KEEP_ALL_HISTORY_QOS"

    def test_transient_local_durability(self):
        assert _text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"


# ---- SPEC 2.3: Alert QoS ----

class TestSpec23Alert:
    """SPEC 2.3 - Alerts: reliable, writer keeps last 32, reader keeps last 128,
    transient-local, lifespan 300 s."""

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["AlertProfile"].find("datawriter_qos")
        self.reader = profiles["AlertProfile"].find("datareader_qos")

    def test_reliable(self):
        assert _text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_writer_history_depth_32(self):
        assert _text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.writer, "history/depth") == "32"

    def test_reader_history_depth_128(self):
        assert _text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.reader, "history/depth") == "128"

    def test_transient_local_durability(self):
        assert _text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_lifespan_300s(self):
        assert _text(self.writer, "lifespan/duration/sec") == "300"
        assert _text(self.writer, "lifespan/duration/nanosec") == "0"


# ---- SPEC 2.4: Mission QoS ----

class TestSpec24Mission:
    """SPEC 2.4 - Mission plans: reliable, transient-local, keep-last depth 1."""

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["MissionProfile"].find("datawriter_qos")
        self.reader = profiles["MissionProfile"].find("datareader_qos")

    def test_reliable(self):
        assert _text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_transient_local_durability(self):
        assert _text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_keep_last_depth_1(self):
        assert _text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.writer, "history/depth") == "1"
        assert _text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.reader, "history/depth") == "1"


# ---- SPEC 2.5: Swarm Summary QoS ----

class TestSpec25SwarmSummary:
    """SPEC 2.5 - Swarm summary: reliable, transient-local, keep-last depth 1."""

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["SwarmSummaryProfile"].find("datawriter_qos")
        self.reader = profiles["SwarmSummaryProfile"].find("datareader_qos")

    def test_reliable(self):
        assert _text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_transient_local_durability(self):
        assert _text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_keep_last_depth_1(self):
        assert _text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.writer, "history/depth") == "1"
        assert _text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _text(self.reader, "history/depth") == "1"
