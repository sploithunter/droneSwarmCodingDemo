"""Unit tests for QoS XML profile validation."""

import os
import xml.etree.ElementTree as ET

import pytest

QOS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'qos', 'USER_QOS_PROFILES.xml')

EXPECTED_PROFILES = [
    "TelemetryProfile",
    "CommandProfile",
    "AlertProfile",
    "MissionProfile",
    "SwarmSummaryProfile",
]


@pytest.fixture(scope="module")
def tree():
    return ET.parse(QOS_FILE)


@pytest.fixture(scope="module")
def profiles(tree):
    root = tree.getroot()
    library = root.find("qos_library")
    return {p.attrib["name"]: p for p in library.findall("qos_profile")}


# --- Structural tests ---

class TestQosXmlStructure:

    def test_file_exists(self):
        assert os.path.isfile(QOS_FILE), f"QoS file not found at {QOS_FILE}"

    def test_well_formed_xml(self):
        ET.parse(QOS_FILE)  # raises ParseError if malformed

    def test_all_profiles_present(self, profiles):
        for name in EXPECTED_PROFILES:
            assert name in profiles, f"Profile '{name}' missing"

    def test_each_profile_has_writer_and_reader(self, profiles):
        for name in EXPECTED_PROFILES:
            p = profiles[name]
            assert p.find("datawriter_qos") is not None, f"{name} missing datawriter_qos"
            assert p.find("datareader_qos") is not None, f"{name} missing datareader_qos"


# --- Helper ---

def _get_text(element, path):
    node = element.find(path)
    assert node is not None, f"Element not found: {path}"
    return node.text.strip()


# --- TelemetryProfile ---

class TestTelemetryProfile:

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["TelemetryProfile"].find("datawriter_qos")
        self.reader = profiles["TelemetryProfile"].find("datareader_qos")

    def test_reliability_best_effort(self):
        assert _get_text(self.writer, "reliability/kind") == "BEST_EFFORT_RELIABILITY_QOS"
        assert _get_text(self.reader, "reliability/kind") == "BEST_EFFORT_RELIABILITY_QOS"

    def test_history_keep_last_depth_1(self):
        assert _get_text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.writer, "history/depth") == "1"

    def test_deadline_200ms(self):
        assert _get_text(self.writer, "deadline/period/sec") == "0"
        assert _get_text(self.writer, "deadline/period/nanosec") == "200000000"

    def test_liveliness_automatic_2s(self):
        assert _get_text(self.writer, "liveliness/kind") == "AUTOMATIC_LIVELINESS_QOS"
        assert _get_text(self.writer, "liveliness/lease_duration/sec") == "2"
        assert _get_text(self.writer, "liveliness/lease_duration/nanosec") == "0"

    def test_ownership_exclusive_strength_100(self):
        assert _get_text(self.writer, "ownership/kind") == "EXCLUSIVE_OWNERSHIP_QOS"
        assert _get_text(self.writer, "ownership_strength/value") == "100"


# --- CommandProfile ---

class TestCommandProfile:

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["CommandProfile"].find("datawriter_qos")
        self.reader = profiles["CommandProfile"].find("datareader_qos")

    def test_reliability_reliable(self):
        assert _get_text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _get_text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_max_blocking_time_1s(self):
        assert _get_text(self.writer, "reliability/max_blocking_time/sec") == "1"
        assert _get_text(self.writer, "reliability/max_blocking_time/nanosec") == "0"

    def test_history_keep_all(self):
        assert _get_text(self.writer, "history/kind") == "KEEP_ALL_HISTORY_QOS"
        assert _get_text(self.reader, "history/kind") == "KEEP_ALL_HISTORY_QOS"

    def test_durability_transient_local(self):
        assert _get_text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _get_text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"


# --- AlertProfile ---

class TestAlertProfile:

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["AlertProfile"].find("datawriter_qos")
        self.reader = profiles["AlertProfile"].find("datareader_qos")

    def test_writer_reliability_reliable(self):
        assert _get_text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_writer_history_keep_last_depth_32(self):
        assert _get_text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.writer, "history/depth") == "32"

    def test_writer_durability_transient_local(self):
        assert _get_text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_writer_lifespan_300s(self):
        assert _get_text(self.writer, "lifespan/duration/sec") == "300"
        assert _get_text(self.writer, "lifespan/duration/nanosec") == "0"

    def test_reader_history_depth_128(self):
        assert _get_text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.reader, "history/depth") == "128"


# --- MissionProfile ---

class TestMissionProfile:

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["MissionProfile"].find("datawriter_qos")
        self.reader = profiles["MissionProfile"].find("datareader_qos")

    def test_reliability_reliable(self):
        assert _get_text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _get_text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_durability_transient_local(self):
        assert _get_text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _get_text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_history_keep_last_depth_1(self):
        assert _get_text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.writer, "history/depth") == "1"
        assert _get_text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.reader, "history/depth") == "1"


# --- SwarmSummaryProfile ---

class TestSwarmSummaryProfile:

    @pytest.fixture(autouse=True)
    def setup(self, profiles):
        self.writer = profiles["SwarmSummaryProfile"].find("datawriter_qos")
        self.reader = profiles["SwarmSummaryProfile"].find("datareader_qos")

    def test_reliability_reliable(self):
        assert _get_text(self.writer, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"
        assert _get_text(self.reader, "reliability/kind") == "RELIABLE_RELIABILITY_QOS"

    def test_durability_transient_local(self):
        assert _get_text(self.writer, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"
        assert _get_text(self.reader, "durability/kind") == "TRANSIENT_LOCAL_DURABILITY_QOS"

    def test_history_keep_last_depth_1(self):
        assert _get_text(self.writer, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.writer, "history/depth") == "1"
        assert _get_text(self.reader, "history/kind") == "KEEP_LAST_HISTORY_QOS"
        assert _get_text(self.reader, "history/depth") == "1"
