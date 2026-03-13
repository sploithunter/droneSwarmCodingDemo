The Vision (7:06)

Okay, I need to do a 40 minute presentation on how to do agentic coding.  The problem is I don't have an idea of a project I would like to do. Normally I would pick Genesis, but I don't want questions about Genesis distracting from the agent of coding. It might be nice to show clog code's ability to do an interface. So if it's a 40 minute presentation and I work on the actual coding project tonight, I think it could probably be a couple hours, maybe three hours of work tonight. So that would probably be, I don't know, 8,000, 10,000 lines of code if you're doing the coding. And then I can summarize it into a presentation and give it tomorrow. But I need an idea of what to do.

Thought process Thought process Great challenge — you need something that's visually impressive, demonstrates Claude Code's strengths (especially UI work), and is interesting enough to carry a 40-minute talk without the project topic itself stealing the show.

Here are a few ideas, roughly ordered by how well I think they'd work:

Personal Finance Dashboard — A full-stack app that lets you input transactions (or import a CSV) and visualizes spending by category, trends over time, budget vs. actual, etc. Great for showing Claude Code building out React components, charts (Recharts/D3), and maybe a simple backend. Everyone understands money, nobody will derail into theological debate.

Recipe Manager / Meal Planner — CRUD app with a nice UI where you can add recipes, tag them, search/filter, and generate a weekly meal plan. Shows off form handling, search, layout work. Relatable, low-controversy.

Project Task Board (Trello-lite) — A Kanban board with drag-and-drop columns, task cards, labels, due dates. This is a classic "looks impressive, audience instantly gets it" demo. Drag-and-drop is a great moment to show Claude Code handling complex UI interactions.

Local Weather + Activity Recommender — Pulls weather data from an API and suggests activities. Nice dashboard UI with maps, forecasts, and cards. Shows API integration, responsive layout, and practical utility.

Markdown Knowledge Base / Wiki — A personal wiki app where you write in markdown, organize pages in a tree, and search across everything. Clean UI, shows file handling, rich text rendering, and navigation patterns.

My top pick would be the Task Board. It's immediately recognizable to any technical audience, the drag-and-drop interaction is a "wow" moment when built by an agent, it naturally produces a lot of component code (cards, columns, modals, filters), and nobody's going to ask you questions about the domain — they'll stay focused on how you built it, which is the whole point.

What kind of audience is this for? That might help narrow it down further.

So it's for the dev team in the R&D meeting at Realtime Innovations. I'm getting forced into this even though my last day is Friday. I get to give this presentation tomorrow, which is Thursday.

Ha, nothing like a farewell presentation under duress. At least you get to make it about something genuinely cool.

Since it's an R&D dev team at RTI, these are people who know distributed systems, networking, and DDS inside and out. That changes the calculus — you want something that respects their intelligence but doesn't overlap with their day-to-day domain (or it'll turn into a DDS architecture debate instead of an agentic coding talk).

Given that context, I'd actually pivot away from the task board idea. That's a bit generic for this crowd. Here are thoughts tuned for RTI engineers:

Real-time System Monitor Dashboard — A web app that simulates (or actually monitors) system metrics — CPU, memory, network throughput, latency histograms — with live-updating charts, alerting thresholds, and a clean dark-mode UI. It's adjacent enough to what they care about (real-time data) that they'll appreciate it, but it's a monitoring tool, not a DDS thing, so it won't derail. And the live-updating UI is a great showcase for Claude Code building WebSocket connections, streaming chart components, etc.

CLI Tool + Web UI for Log Analysis — Something that ingests log files, parses them, shows timelines of events, lets you filter/search, and highlights anomalies. Every engineer at RTI has suffered through log analysis. They'll get it immediately, and it shows Claude Code handling both a backend parser and a rich frontend.

API Design Playground — A tool where you define an API schema (REST or similar), and it auto-generates mock endpoints, documentation, and a test harness UI. Shows off code generation, form-heavy UI, and practical developer tooling.

I think the system monitor dashboard is your strongest bet. It's visually striking with live charts, the audience will intuitively understand the value, it's a natural fit for showing off Claude Code building complex React components, and it gives you a nice arc for the presentation — start with nothing, end with a polished real-time dashboard.

Plus you can narrate the story of "here's what I built in 3 hours last night" and that landing will hit hard with engineers who know how long this stuff normally takes.

Want me to help you sketch out the feature scope and architecture so you can hit the ground running tonight?

I think we can do DDS, I just don't want to do Genesis. Could we build a somewhat complex DDS system and then have a monitor dashboard?

Gathered user preferences for DDS system domain and implementation language Gathered user preferences for DDS system domain and implementation language That's a much better idea honestly. The audience will actually appreciate seeing DDS used well, and you can narrate the agentic coding story on top of a domain they deeply understand. The "wow" factor doubles — impressive that an agent built it, and they can evaluate the DDS architecture choices it made.

Let me ask a few things to help nail down the scope:

What kind of DDS system would you find most interesting to build? Something like simulated drone swarm telemetry, smart building sensors, fleet tracking, or industrial IoT? Drone swarm What language do you want the DDS publishers/subscribers in? Python For the web dashboard, what tech stack? React + Recharts Drone swarm with Python DDS and React/Recharts — that's a great combo. Visually compelling, technically interesting, and Python keeps the DDS side fast to implement so you can spend more of your 3 hours on the dashboard polish.

Here's how I'd scope it:

DDS Layer (Python + Connext)

IDL types for drone telemetry (position, velocity, battery, status), commands (waypoints, return-to-base), and alerts (geofence breach, low battery) A swarm simulator publisher that runs N drones with semi-realistic flight patterns — waypoint following, battery drain, occasional faults A command publisher for sending missions QoS profiles that actually make sense: reliable for commands, best-effort for high-rate telemetry, deadline/liveliness for health monitoring Bridge Layer

A Python DDS subscriber that forwards data over WebSocket to the frontend — this is the glue piece React Dashboard

A 2D map view showing drone positions updating in real time (canvas or SVG, no need for a full mapping library) Telemetry panels: battery levels, altitude, speed per drone Swarm overview: aggregate stats, how many active/faulted/returning Alert feed: live log of events like geofence violations, low battery warnings Command panel: buttons to send waypoints or recall drones That's probably 6-8 DDS source files, the bridge, and 15-20 React components. Should land solidly in your 8-10K line range and fill 3 hours of agentic coding nicely.

The presentation story practically writes itself: "I sat down at 8pm, gave Claude Code this spec, and here's what happened over the next 3 hours." Then you walk through the key decision points, where you intervened, what the agent got right and wrong.

Want me to write up a more detailed spec document you can feed to Claude Code tonight to get started?


Yeah, I think come up with a highly technical vision document. I think we should have... eight dorms. We use some kind of map. Make the drones somewhat realistic, but don't try to do MavLink or anything. We can just have a straight DDS with drone applications. Yeah, come up with that and then I can feed that to cloud code and we'll come up with the actual implementation plan from your detailed vision document.

Let me read the relevant skill first, then build this out.

Designed DDS drone swarm architecture and vision document Designed DDS drone swarm architecture and vision document View your vision document

That's a ~12-page technical spec covering the full system. Here's what's in it:

DDS layer: 5 topics (DroneState at 10Hz, DroneCommand, DroneAlert, MissionPlan, SwarmSummary) with full IDL definitions and justified QoS profiles — BEST_EFFORT for telemetry, RELIABLE+TRANSIENT_LOCAL for commands and missions, deadline and liveliness for health detection.

8 drones with distinct personalities — ALPHA is reliable, CHARLIE starts low on battery, DELTA is GPS-prone, ECHO has motor issues, HOTEL sits idle waiting for dashboard commands. Each runs its own state machine with simplified flight physics, battery drain, and probabilistic fault injection.

Missions are geometric patterns (perimeter patrol, grid search, radial survey, circle patrol) so they look great on the map.

Dashboard uses Leaflet for a real map centered on Sunnyvale with drone markers, trails, geofence boundaries, and waypoint paths. Side panel has swarm overview, alert feed, per-drone telemetry charts, and a full command panel.

I also included a prioritized implementation order at the end — so if you hit hour 3 and you're not done, you know what to cut. And a suggested 40-minute presentation arc to close with.

Feed that whole file to Claude Code and you should be off to the races tonight.


Continue Discussion (building neural connections) (7:21)
❯ alright, take a look at the vision document in docs. What do you think? What we want here is, in fact the entire goal of this project isn't necessarily the drone, vision, or even DDS. It is to show
the DDS dev team for RTI the current capabilities of agentic coding. So this is what I tackled so that we could come up with a project that would resonate with that audience. What do you think?

⏺ Searched for 1 pattern, read 1 file (ctrl+o to expand)

⏺ This is excellent. A few thoughts:

Why it works for the audience:

The domain choice is spot-on. DDS engineers at RTI will immediately recognize that the IDL, QoS profiles, and pub/sub topology are correct — not just plausible-looking boilerplate. You've got
EXCLUSIVE ownership on telemetry, RELIABLE + TRANSIENT_LOCAL on commands, lifespan on alerts, deadline/liveliness for fault detection. These aren't random QoS knobs — they're the choices a DDS
architect would actually make. That credibility is what will make the audience pay attention to the agentic coding story rather than getting distracted by domain inaccuracies.

What makes it a strong demo vehicle:

It's end-to-end: IDL → Python simulation → DDS middleware → WebSocket bridge → React UI. That's a full-stack distributed system, which makes the "one evening" claim genuinely impressive.
It's visually immediate. Drones on a Leaflet map with trails and real-time charts will land much better than a terminal full of log output.
The fault injection and drone personalities are a smart touch — they make the demo unpredictable and alive, which keeps an audience engaged.
The command panel gives you interactivity during the live demo. You can send an RTB command and watch it happen on screen.

The real meta-story:

The vision doc itself is part of the demo. Section 12 makes this explicit, but I'd lean into it even harder — the quality and specificity of this document is what enables the agent to succeed. It shows that agentic coding isn't "type a prompt and get an app." It's: domain expert writes a precise spec, then the agent handles the implementation grunt work. That framing respects the audience's expertise rather than threatening it.

A few practical notes:


The prioritization list in 11.4 is smart insurance. If time runs short, you still have a working demo at any cutoff point.
Section 11.1 with the rti.connextdds API patterns is critical — that's the kind of context an agent needs since it's a niche API that won't be heavily represented in training data.
The 40-minute presentation arc in Section 12 is well-paced. 20 minutes on the build walkthrough is where the real value is for this audience.

Want to start building it out, or are you still in the planning/refinement phase on the doc?

(build more neural connections)

Still llike the discussion phase, what do you think you would do to augment or reduce the work here? I am looking for purely agentic coding, probably three hours work, I'm thinking 10,000 lines.

⏺ Good question. Let me think about where the time actually goes and what the ROI is for the demo.

What I'd cut or simplify:

Dark mode toggle. It's listed as a nice-to-have but it touches every component's styling. That's 500+ lines of theme plumbing that adds zero to the DDS story. Pick one theme (dark looks better for dashboards) and commit to it.
The Mission Planner as a separate process. It publishes missions at startup and then mostly sits there. Just have each drone's init generate its own mission pattern internally, or have run_swarm.py publish them before spawning drones. Saves an entire process and the mission publishing logic, without losing anything visible.
The Swarm Monitor as a separate process. Same reasoning — the dashboard bridge already subscribes to all DroneState. Compute the SwarmSummary in the bridge and push it to the frontend. Fewer moving parts to demo, fewer things to break live. The topic and type can still exist in the IDL to show the design intent.
Command sequence tracking / ack system. The command_seq field and any round-trip acknowledgment logic. For a demo, fire-and-forget commands are fine. The audience will see the drone respond on the map.

What I'd keep exactly as-is:

The full IDL and QoS profiles — that's the credibility core.
All 8 drones with distinct personalities — it makes the map visually interesting and shows scale.
The fault injection system — it's what makes the demo live and unpredictable.
The full chart suite (battery, altitude, speed, motors, temperature) — each one is ~80-100 lines with Recharts, they're fast to generate, and they fill the screen impressively.
The WebSocket bridge with batching — it's architecturally interesting and practically necessary.

What I'd add:

A connection status banner with reconnect logic. Simple, but it prevents the most embarrassing live demo failure (refreshing the browser and getting a blank screen).
A "drone detail popup" on map marker click — just show callsign, mode, battery, speed inline on the map. It's a small touch that makes the map feel interactive without the full command panel.
Sound or visual pulse on critical alerts. A CSS animation on the alert feed when a CRITICAL comes in. Five lines of CSS, big visual impact during the demo.

Line budget estimate:

---

## Retrospective: What We'd Change to Make DDS Primary from the Start

After completing the project and wiring up actual RTI Connext DDS as a late addition, it became clear that DDS was treated as a bolt-on runtime dependency rather than the core communication fabric. The three planning documents — VISION.md, SPEC.md, and PLAN.md — each contributed to this drift in specific ways.

### What Happened

The PLAN explicitly deferred DDS integration:

> Phase 2E: "DDS integration for drone simulator (deferred — requires RTI runtime)"

The entire drone simulation — physics, battery, faults, state machine, missions, swarm monitor — was built as standalone Python classes that communicated via direct method calls and in-process data passing. DDS was made optional through a feature flag pattern:

```python
try:
    import rti.connextdds as dds
    HAS_DDS = True
except ImportError:
    HAS_DDS = False
```

This meant the system worked perfectly without DDS. The swarm-level aggregation (SwarmSummary) was computed in-process. Individual drone command/state pub/sub over DDS — the most architecturally interesting part for an RTI audience — was the last thing wired up.

### What to Change in the VISION Document

The vision described DDS architecture correctly (section 3.2 shows each drone as a DDS participant with publishers and subscribers) but never **constrained** against non-DDS shortcuts. Adding an explicit architectural constraint would have prevented the drift:

> "DDS is the ONLY inter-process communication mechanism. Components never call each other directly. A drone publishes DroneState; the bridge discovers it via DDS subscription. The dashboard sends DroneCommand; the drone receives it via DDS subscription. There are no shortcuts, no in-process aggregation, no direct function calls between participants."

The priority list in section 11.4 also needed to be more explicit. Instead of:

```
1. DDS types and QoS profiles
2. One working drone simulator
```

It should have been:

```
1. DDS types and QoS profiles
2. One DDS participant that publishes a single DroneState sample
3. One DDS subscriber that reads that sample
4. Flight physics (populating DroneState fields with real data)
5. ...everything else...
```

### What to Change in the GWT SPEC

The spec tested DDS *types* (section 1) and *QoS* (section 2) in isolation, but then sections 3-9 tested **behavior** without requiring DDS as the delivery mechanism. For example, SPEC 3.4:

```
Scenario: HOVER command pauses mission
  Given a drone in EN_ROUTE mode
  When a DroneCommand with command = HOVER is received for that drone
  Then the drone transitions to HOVERING mode
```

"Is received" is ambiguous — it could mean a direct method call or a DDS DataReader callback. The spec never forced the DDS path. Adding per-participant DDS communication scenarios would have closed this gap:

```
Scenario: Drone receives command via DDS subscription
  Given drone 3 is running as a DDS participant on domain 0
  And drone 3 subscribes to "drone/command" filtered by drone_id = 3
  When a separate process publishes a DroneCommand with drone_id = 3
    and command = RETURN_TO_BASE to the "drone/command" topic
  Then drone 3 receives the command via its DDS DataReader
  And drone 3 transitions to RETURNING_TO_BASE mode

Scenario: Drone publishes state that bridge receives via DDS
  Given drone 0 is publishing DroneState at 10 Hz on "drone/state"
  And the bridge is subscribed to "drone/state"
  When 1 second elapses
  Then the bridge's DataReader receives ~10 samples with drone_id = 0
  And each sample contains valid position, battery, and mode data

Scenario: Broadcast command reaches all drones via DDS
  Given 8 drone participants are subscribed to "drone/command"
  When the bridge publishes a DroneCommand with drone_id = 255
  Then all 8 drones receive the command via DDS
  And each drone processes it independently
```

The existing spec tested the *what* (drone transitions to HOVERING) but not the *how* (via DDS subscription). Adding the "how" forces the implementation plan to wire up DDS for individual drone control, not just swarm-level aggregation.

### What to Change in the PLAN

The plan should have structured DDS participant creation as a Phase 1 deliverable, not a deferred Phase 2E:

```
Phase 1: Foundation
  1A — DDS types (same)
  1B — QoS profiles (same)
  1C — Drone config (same)
  1D — React scaffold (same)
  1E — Single drone DDS participant  ← NEW
       - Joins domain 0
       - Publishes DroneState with hardcoded values at 10 Hz
       - Subscribes to DroneCommand and logs received commands
       Gate: a separate Python subscriber reads the DroneState samples

Phase 2: Drone Simulation
  2A — Flight physics (populates DDS-published DroneState fields)
  2B — Battery model
  2C — Fault injector
  2D — State machine (writes to its DDS DataWriter, not just in-memory)
  2E — Bridge DDS subscriber  ← moved up from Phase 3
       Gate: bridge reads DroneState samples published by drone simulator
```

The key structural change: Phase 1 ends with a working DDS data flow, not just data structures in memory. By Phase 2D, the drone state machine is already publishing to DDS.

### Summary

Three things collectively pushed DDS to the end:

1. **VISION** described DDS architecture but didn't constrain against non-DDS shortcuts
2. **SPEC** tested behavior ("drone transitions to X") without requiring the DDS delivery path ("drone receives command via DataReader")
3. **PLAN** explicitly deferred DDS integration, and the `HAS_DDS` fallback pattern made deferral painless

The fix: make the spec scenarios require DDS as the communication mechanism, and make the plan's first working milestone "one drone publishing, one subscriber reading" — before physics, before battery, before faults. DDS becomes the first thing that works, not the last thing bolted on.

