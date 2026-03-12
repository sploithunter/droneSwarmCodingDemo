"""DDS infrastructure — separate DomainParticipants per VISION.md Section 3.2.

Architecture (all on Domain 0):
  - DroneParticipant (8 instances): PUB DroneState, DroneAlert; SUB DroneCommand, MissionPlan
  - MonitorParticipant (1 instance): PUB SwarmSummary; SUB DroneState, DroneAlert
  - BridgeParticipant (1 instance): SUB All topics; PUB DroneCommand
"""

import os
import rti.connextdds as dds

from drones.types import (
    DroneState, DroneCommand, DroneAlert, MissionPlan, SwarmSummary
)

# Resolve QoS XML path relative to project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QOS_XML = os.path.join(_PROJECT_ROOT, "qos", "USER_QOS_PROFILES.xml")


class DroneParticipant:
    """One per drone — its own DomainParticipant publishing state/alerts,
    subscribing to commands/missions."""

    def __init__(self, drone_id, domain_id=0):
        self.drone_id = drone_id
        self.participant = dds.DomainParticipant(domain_id=domain_id)
        qos = dds.QosProvider(_QOS_XML)

        # Topics
        state_topic = dds.Topic(self.participant, "DroneState", DroneState)
        alert_topic = dds.Topic(self.participant, "DroneAlert", DroneAlert)
        command_topic = dds.Topic(self.participant, "DroneCommand", DroneCommand)
        mission_topic = dds.Topic(self.participant, "MissionPlan", MissionPlan)

        # Publisher + Writers
        pub = dds.Publisher(self.participant)
        self.state_writer = dds.DataWriter(
            pub, state_topic,
            qos=qos.datawriter_qos_from_profile(
                "DroneSwarmLibrary::TelemetryProfile"))
        self.alert_writer = dds.DataWriter(
            pub, alert_topic,
            qos=qos.datawriter_qos_from_profile(
                "DroneSwarmLibrary::AlertProfile"))

        # Subscriber + Readers
        sub = dds.Subscriber(self.participant)
        self.command_reader = dds.DataReader(
            sub, command_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::CommandProfile"))
        self.mission_reader = dds.DataReader(
            sub, mission_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::MissionProfile"))

    def write_state(self, state):
        self.state_writer.write(state)

    def write_alert(self, alert):
        self.alert_writer.write(alert)

    def take_commands(self):
        try:
            return [c for c in self.command_reader.take_data()
                    if c.drone_id == self.drone_id or c.drone_id == 255]
        except Exception:
            return []

    def take_missions(self):
        try:
            return [m for m in self.mission_reader.take_data()
                    if m.drone_id == self.drone_id]
        except Exception:
            return []

    def close(self):
        self.participant.close()


class MonitorParticipant:
    """Swarm Monitor — subscribes to DroneState/DroneAlert,
    publishes SwarmSummary."""

    def __init__(self, domain_id=0):
        self.participant = dds.DomainParticipant(domain_id=domain_id)
        qos = dds.QosProvider(_QOS_XML)

        # Topics
        state_topic = dds.Topic(self.participant, "DroneState", DroneState)
        alert_topic = dds.Topic(self.participant, "DroneAlert", DroneAlert)
        summary_topic = dds.Topic(self.participant, "SwarmSummary", SwarmSummary)

        # Publisher
        pub = dds.Publisher(self.participant)
        self.summary_writer = dds.DataWriter(
            pub, summary_topic,
            qos=qos.datawriter_qos_from_profile(
                "DroneSwarmLibrary::SwarmSummaryProfile"))

        # Subscriber
        sub = dds.Subscriber(self.participant)
        self.state_reader = dds.DataReader(
            sub, state_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::TelemetryProfile"))
        self.alert_reader = dds.DataReader(
            sub, alert_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::AlertProfile"))

    def take_states(self):
        try:
            return list(self.state_reader.take_data())
        except Exception:
            return []

    def take_alerts(self):
        try:
            return list(self.alert_reader.take_data())
        except Exception:
            return []

    def write_summary(self, summary):
        self.summary_writer.write(summary)

    def close(self):
        self.participant.close()


class BridgeParticipant:
    """Dashboard Bridge — subscribes to ALL topics, publishes DroneCommand."""

    def __init__(self, domain_id=0):
        self.participant = dds.DomainParticipant(domain_id=domain_id)
        qos = dds.QosProvider(_QOS_XML)

        # Topics
        state_topic = dds.Topic(self.participant, "DroneState", DroneState)
        alert_topic = dds.Topic(self.participant, "DroneAlert", DroneAlert)
        command_topic = dds.Topic(self.participant, "DroneCommand", DroneCommand)
        mission_topic = dds.Topic(self.participant, "MissionPlan", MissionPlan)
        summary_topic = dds.Topic(self.participant, "SwarmSummary", SwarmSummary)

        # Publisher (for commands from dashboard)
        pub = dds.Publisher(self.participant)
        self.command_writer = dds.DataWriter(
            pub, command_topic,
            qos=qos.datawriter_qos_from_profile(
                "DroneSwarmLibrary::CommandProfile"))
        # Also publish missions (planner role)
        self.mission_writer = dds.DataWriter(
            pub, mission_topic,
            qos=qos.datawriter_qos_from_profile(
                "DroneSwarmLibrary::MissionProfile"))

        # Subscriber (reads all topics for dashboard)
        sub = dds.Subscriber(self.participant)
        self.state_reader = dds.DataReader(
            sub, state_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::TelemetryProfile"))
        self.alert_reader = dds.DataReader(
            sub, alert_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::AlertProfile"))
        self.mission_reader = dds.DataReader(
            sub, mission_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::MissionProfile"))
        self.summary_reader = dds.DataReader(
            sub, summary_topic,
            qos=qos.datareader_qos_from_profile(
                "DroneSwarmLibrary::SwarmSummaryProfile"))

    def write_command(self, cmd):
        self.command_writer.write(cmd)

    def write_mission(self, mission):
        self.mission_writer.write(mission)

    def take_states(self):
        try:
            return list(self.state_reader.take_data())
        except Exception:
            return []

    def take_alerts(self):
        try:
            return list(self.alert_reader.take_data())
        except Exception:
            return []

    def take_missions(self):
        try:
            return list(self.mission_reader.take_data())
        except Exception:
            return []

    def take_summaries(self):
        try:
            return list(self.summary_reader.take_data())
        except Exception:
            return []

    def close(self):
        self.participant.close()
