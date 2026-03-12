# Agentic Coding Process Document

## How to Build a 10K-Line Project in ~90 Minutes with AI Pair Programming

_Based on the DDS Drone Swarm Monitoring System build session — a real-time 8-drone simulation with Python backend and React dashboard, built as a demonstration for RTI's DDS development team._

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase -1: Ideation & Audience Fit](#2-phase--1-ideation--audience-fit)
3. [Phase 0: Vision & Neural Connection](#3-phase-0-vision--neural-connection)
4. [Phase 0.5: GWT Specification](#4-phase-05-gwt-specification)
5. [Phase 1: Implementation Planning](#5-phase-1-implementation-planning)
6. [Phase 2: Parallel Execution](#6-phase-2-parallel-execution)
7. [Phase 3: Debugging & Integration](#7-phase-3-debugging--integration)
8. [Phase 4: Packaging & Delivery](#8-phase-4-packaging--delivery)
9. [Key Pitfalls & Lessons Learned](#9-key-pitfalls--lessons-learned)
10. [Anti-Patterns to Avoid](#10-anti-patterns-to-avoid)
11. [Checklist](#11-checklist)

---

## 1. Overview

### The Method in One Sentence

**Vision → Discussion → Specification → Plan → Parallel Build → Test Gate → Debug → Ship.**

### What Makes This Different from Normal AI Coding

Most people open a chat and say "build me X." That produces mediocre, inconsistent code that falls apart at integration. The method described here front-loads alignment so the AI can execute autonomously with high quality.

### Timeline (Actual — 7:06 PM to 8:35 PM, ~90 minutes)

| Clock Time | Elapsed | Activity | Output |
|------------|---------|----------|--------|
| 7:06 | 0:00 | Ideation — choosing what to build | Project concept selected |
| 7:06–7:20 | 0:00–0:14 | Vision document creation | `VISION.md` (~500 lines, 12 sections) |
| 7:21–7:29 | 0:15–0:23 | Neural connection discussion | Shared mental model, scope refinement |
| 7:30–7:44 | 0:24–0:38 | GWT specification writing | `SPEC.md` (21 sections, ~120 scenarios) |
| 7:45–7:47 | 0:39–0:41 | Implementation planning (plan mode) | `PLAN.md` (5 phases, 17 sub-phases) |
| 7:48 | 0:42 | Phase 1: Foundation (4 parallel agents) | Types, QoS, config, React scaffold — 137 tests |
| 7:48–7:57 | 0:42–0:51 | Phase 2: Drone Simulation (4+2 agents) | Physics, battery, faults, state machine, missions — 278 tests |
| 7:57–8:05 | 0:51–0:59 | Phases 3+4: Bridge + Dashboard (parallel) | WebSocket bridge, all React components — 370 tests |
| 8:05–8:10 | 0:59–1:04 | Phase 5: Integration & Polish | Launch scripts, e2e tests, CSS |
| 8:10–8:24 | 1:04–1:18 | Debugging running system | Map fix, StrictMode fix, mock fixes |
| 8:24–8:35 | 1:18–1:29 | Git, README, packaging | Pushed to GitHub |

---

## 2. Phase -1: Ideation & Audience Fit

### 2.1 Choose Your Project Based on Your Audience

The ideation phase is often skipped, but it's where the entire demo succeeds or fails. The user started this session at 7:06 PM with no project idea — just a constraint: "40-minute presentation on agentic coding for RTI's DDS dev team."

The AI brainstormed several options:
- Personal finance dashboard
- Recipe manager / meal planner
- Project task board (Trello-lite)
- Weather + activity recommender
- Markdown knowledge base

Each was evaluated against the audience. The initial top pick was a task board — visually impressive, universally understood, drag-and-drop is a "wow" moment. But once the user revealed the audience was **RTI's R&D engineering team**, the calculus changed.

**The pivot:** For DDS engineers, a generic CRUD app would be underwhelming. The project needed to demonstrate that the AI could handle their domain correctly — not just plausible-looking code, but correct IDL, correct QoS choices, correct pub/sub topology. The drone swarm concept was born from this constraint.

### 2.2 The Audience Test

Before committing to a project, ask:

1. **Will the audience recognize quality in this domain?** — RTI engineers would immediately spot wrong QoS choices. A task board wouldn't test domain competence.
2. **Will the project hold attention without the domain stealing the show?** — The user specifically avoided using their actual product (Genesis) because questions about it would derail the agentic coding story.
3. **Is it visually immediate?** — Drones on a map with real-time charts lands better than terminal output.
4. **Does it have natural interactivity for live demo?** — The command panel lets the presenter send an RTB command and watch it happen on screen.

### 2.3 Scope Refinement

After the vision document was drafted, the AI and user had a critical scope conversation. The AI suggested:

**Cut:**
- Dark mode toggle (500+ lines of theme plumbing, zero DDS story value) — *User overrode this: "you could do that with your eyes closed"*
- Mission planner as separate process → generate missions at startup
- Swarm monitor as separate process → compute summary in the bridge
- Command acknowledgment/sequence tracking → fire-and-forget for demo

**Keep:**
- Full IDL and QoS profiles — credibility core for the audience
- All 8 drone personalities — visual interest and scale demonstration
- Fault injection — makes the demo live and unpredictable
- Full chart suite — fast to generate, fills the screen impressively
- WebSocket bridge with batching — architecturally interesting

**Add:**
- Connection status banner with reconnect logic — prevents the most embarrassing live demo failure
- Critical alert visual pulse — 5 lines of CSS, big impact

**Lesson:** Scope refinement is a negotiation. The AI proposes cuts based on ROI; the user overrides based on knowledge the AI doesn't have (e.g., "dark mode is trivial for you"). Both perspectives improve the final scope.

### 2.4 The DDS "Wire-Centric" Insight

A key moment in ideation was the user pointing out: *"Since DDS is wire-centric, we could just add or duplicate the drone package with some kind of identifier. We only need to code and maintain one drone application. We just start it eight times."*

This is the kind of domain insight that shapes the entire architecture:
- One `DroneSim` class, parameterized by `drone_id`
- The `@key drone_id` on DroneState means 8 processes writing to the same topic produces 8 keyed instances
- No routing logic, no broker configuration, no discovery coordination
- Scaling from 8 to 50 drones is a config change, not a code change

**Lesson:** Domain experts often have architectural insights that dramatically simplify the implementation. The neural connection conversation is where these emerge.

---

## 3. Phase 0: Vision & Neural Connection

### 3.1 Writing the Vision Document

The vision document is the single most important artifact. It's not a requirements doc — it's a **technical blueprint** that gives the AI enough context to make good decisions autonomously.

#### What to Include

1. **System architecture diagram** — ASCII art showing components, data flow, and ports
2. **Data type definitions** — Full IDL/schema with field names, types, and annotations
3. **Configuration tables** — Every tunable parameter with specific values (not "configurable")
4. **Protocol specifications** — Message formats, serialization, wire protocols
5. **UI layout description** — What panels exist, what data they show, how they interact
6. **Technology choices** — Specific frameworks, versions, and why

#### What NOT to Include

- Vague requirements ("the system should be responsive")
- Implementation details that constrain the AI unnecessarily
- Aspirational features you won't build in this session

#### Example: Good vs Bad Vision Content

**Bad:**
```
The system should support multiple drones with different characteristics.
```

**Good:**
```
| ID | Callsign | Battery | Speed  | Trait                    |
|----|----------|---------|--------|--------------------------|
| 0  | ALPHA    | 100%    | 10 m/s | Reliable baseline        |
| 1  | BRAVO    | 95%     | 12 m/s | Aggressive speed         |
| 2  | CHARLIE  | 88%     | 10 m/s | Low battery start        |
| 3  | DELTA    | 100%    | 10 m/s | GPS-prone (3x fault rate)|
```

**Why it matters:** The AI can't make good decisions about drone behavior, test scenarios, or UI display without these specifics. Every ambiguity becomes a coin flip.

### 3.2 The Neural Connection Conversation

After the vision document exists, **don't immediately start coding.** Have a 15-20 minute conversation where:

1. **The AI reads and summarizes** the vision back to you
2. **You correct misunderstandings** ("No, the bridge batches at 5Hz, not each drone publishes at 5Hz")
3. **You explore edge cases together** ("What happens when a drone gets a GOTO command while in FAULT mode?")
4. **You establish priorities** ("The map must work; chart animations are nice-to-have")

#### Why This Step Matters

The AI is about to generate thousands of lines of code autonomously. Every misunderstanding here multiplies into dozens of bugs later. This conversation is cheap (15 minutes) and prevents the most expensive class of errors (architectural mismatches).

#### What to Watch For

- **The AI confidently restates something wrong** — correct it immediately
- **You realize the vision is ambiguous** — update VISION.md right then
- **The AI suggests something better** — adopt it and update the vision
- **Domain-specific knowledge gaps** — e.g., the AI may not know DDS QoS semantics; teach it

---

## 4. Phase 0.5: GWT Specification

### 4.1 What Are GWT Specs?

Given-When-Then (GWT) acceptance scenarios that serve as both requirements and test cases:

```
### Scenario 3.2: Takeoff Sequence
Given a drone in IDLE mode with a mission assigned
When the simulation starts
Then the drone transitions to TAKEOFF mode
And climbs to mission altitude at 3 m/s ascent rate
And transitions to EN_ROUTE when within 2m of target altitude
```

### 4.2 How to Write Them

1. **One scenario per behavior** — not one scenario per component
2. **Include specific numbers** — "at 3 m/s," not "at the configured rate"
3. **Cover the happy path AND failure modes** — "When battery hits 15%, Then forced RTB regardless of current command"
4. **Organize by system section** — Types, Physics, Battery, Faults, State Machine, etc.

### 4.3 How Many Do You Need?

For a project of this size (~10K lines), aim for **100-130 scenarios** across **15-21 sections**. This sounds like a lot but they write quickly once you have the vision document.

### 4.4 The Spec Drives Everything

- **Tests are 1:1 with spec scenarios** — `test_spec_03_statemachine.py` tests SPEC section 3
- **The plan references spec sections** — "Phase 2A covers SPEC sections 4.1, 4.2"
- **Debugging references specs** — "The map should show trails per SPEC 12.3"

**Critical rule:** Tests are never deleted or skipped. If a test fails, the code is fixed, not the test.

---

## 5. Phase 1: Implementation Planning

### 5.1 Structure of a Good Plan

The plan must have:

1. **Phases** — logical groups that can be built and tested independently
2. **Sub-phases** — units of work within each phase (e.g., 2A, 2B, 2C)
3. **Test gates** — every sub-phase ends with "Gate: all tests pass"
4. **Dependency ordering** — types before physics, physics before simulator, simulator before bridge
5. **SPEC coverage map** — which spec sections are covered by which phase
6. **File list** — exactly which files will be created/modified in each sub-phase

### 5.2 Phase Ordering Principles

```
Foundation (types, config) → Core Logic (physics, battery, faults)
    → Orchestration (state machine, monitor) → Communication (bridge)
        → UI (dashboard components) → Integration (e2e, polish)
```

Each layer only depends on layers above it. This enables parallel execution within layers.

### 5.3 Test Gate Design

Every sub-phase gate runs:
- **New tests** for the sub-phase
- **ALL previous tests** to catch regressions

```bash
# Phase 2C gate — runs all tests, not just fault injector tests
pytest tests/unit/ tests/acceptance/
```

### 5.4 PERSIST THE PLAN TO DISK

**This is the #1 lesson from this build.** If the AI creates the plan in conversation context only, and the context window fills up or the session crashes, the plan is lost. The code-in-progress can't be continued without it.

```
# Do this IMMEDIATELY after plan creation
Write plan to docs/PLAN.md
```

The user caught this during the build — the plan existed only in the chat context and hadn't been saved to `docs/PLAN.md`. If the session had crashed at that point, we'd have lost the roadmap.

---

### 5.5 The Plan Mode Workflow

In Claude Code, "plan mode" is a distinct interaction mode where the AI explores the codebase and designs an implementation approach before writing any code. The user explicitly requested this:

> *"Enter plan mode and come up with a very detailed implementation plan. The implementation plan should include the concept of test early test often... we shall never leave any test behind even if the failure of a test resulted in some other code or previous coding errors. Nothing can pass unless all unit tests, all end-to-end tests, and all appropriate acceptance tests are met."*

The plan mode workflow:
1. AI enters plan mode (exploration only, no edits)
2. AI reads existing files (VISION.md, SPEC.md) to understand context
3. AI designs phases, sub-phases, test gates, and dependency ordering
4. AI presents the plan for user approval
5. User reviews and approves (or requests changes)
6. AI exits plan mode and begins execution

**Key advantage:** The plan exists as a reviewable artifact before any code is written. The user can catch architectural mistakes before they become 1,000 lines of code to rework.

---

## 6. Phase 2: Parallel Execution

### 6.1 When to Parallelize

Sub-phases within a layer can run in parallel when they have no data dependencies:

```
✅ Parallel OK:
  2A (flight physics) + 2B (battery model) + 2C (fault injector)
  — These are independent modules with no shared state

❌ Cannot parallelize:
  2D (drone simulator) depends on 2A, 2B, 2C outputs
  — The simulator imports and orchestrates all three
```

### 6.2 How to Parallelize with Agents

Launch multiple agents simultaneously, each handling one sub-phase:

```
Agent 1: "Implement Phase 2A — flight physics"
Agent 2: "Implement Phase 2B — battery model"
Agent 3: "Implement Phase 2C — fault injector"
```

Each agent gets:
- The full plan (or relevant section)
- The vision document context
- The spec scenarios it needs to satisfy
- Access to foundation code from Phase 1

### 6.3 Integration After Parallel Work

After parallel agents complete, run the full test suite before proceeding:

```bash
pytest tests/unit/ tests/acceptance/ -v
```

Fix any integration issues (import errors, interface mismatches) before starting the next layer.

### 6.4 Realistic Parallelism Limits

- **3-4 agents** simultaneously is the practical maximum
- More than that risks conflicting file edits and merge issues
- Python backend phases and React dashboard phases can often run in parallel since they touch completely different files

---

### 6.5 How Parallelism Actually Played Out

In the actual build, here's how agents were deployed:

**Phase 1** — 4 agents in parallel (all independent foundation work):
- 1A: Types + skeleton
- 1B: QoS profiles XML
- 1C: Drone config
- 1D: React scaffold
- Result: 137 tests, completed in ~3 minutes

**Phase 2, Round 1** — 4 agents in parallel (independent algorithms):
- 2A: Flight physics
- 2B: Battery model
- 2C: Fault injector
- 2F: Mission patterns
- Result: All pass

**Phase 2, Round 2** — 2 agents in parallel (depend on Round 1):
- 2D: Drone state machine (imports physics, battery, faults)
- 2G: Swarm monitor + launcher
- Result: 278 total tests

**Phases 3+4** — Bridge and dashboard phases ran in parallel since they touch completely different files (Python vs React):
- Phase 3A: WebSocket bridge
- Phase 4A: WebSocket context + hooks
- Then 4B-4G in subsequent parallel batches
- Result: 370 total tests

**Phase 5** — 2 agents for final integration:
- 5A: Launch scripts
- 5C-5D: E2E tests

**Total implementation time: ~25 minutes** for all 5 phases, from first agent launch to all 370 tests passing.

---

## 7. Phase 3: Debugging & Integration

### 7.1 The Debugging Workflow

Once the full system is assembled:

1. **Start the backend** — `python -m drones.run_swarm`
2. **Start the frontend** — `cd dashboard && npm run dev`
3. **Open the browser** — verify visual output matches expectations
4. **Check the console** — look for WebSocket errors, JS exceptions
5. **Verify data flow** — are drones moving? Are charts updating? Are alerts appearing?

### 7.2 Common Integration Issues

#### WebSocket Connection

**Symptom:** Dashboard shows "Disconnected," no drone data appears.

**Debug steps:**
1. Is the Python process running? (`ps aux | grep run_swarm`)
2. Is port 8765 listening? (`lsof -i :8765`)
3. Can you connect manually? (`python -c "import asyncio, websockets; ..."`)
4. Check browser console for WebSocket errors

**Common cause:** Missing Python package (`pip install websockets`).

#### Map Not Rendering

**Symptom:** Map panel is blank/gray, no tiles or markers visible.

**Root cause in this build:** Leaflet was imported incorrectly.

```javascript
// WRONG — assumes Leaflet is loaded via CDN as a global
const L = window.L;

// RIGHT — import from npm module
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
```

**General lesson:** When using npm-installed packages, always use ES module imports, never assume globals exist. If you see `window.X` in generated code for an npm package, it's wrong.

#### React StrictMode Double-Render Issues

**Symptom:** Console warning "WebSocket is closed before the connection is established."

**Root cause:** React 18 StrictMode mounts/unmounts/remounts components in development. If a WebSocket connects on mount, StrictMode's first unmount closes it before `onopen` fires.

**Fix:**
```javascript
useEffect(() => {
  let cancelled = false;
  const timer = setTimeout(() => {
    if (!cancelled) connect();
  }, 0);
  return () => {
    cancelled = true;
    clearTimeout(timer);
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect on intentional close
      wsRef.current.close();
    }
  };
}, [connect]);
```

**General lesson:** Any side-effect in a React useEffect (WebSocket, EventSource, timers) needs StrictMode-safe cleanup. Wrapping in `setTimeout(fn, 0)` gives the cleanup function a chance to cancel before the effect runs.

#### Test Mock Incompleteness

**Symptom:** Tests pass before a code change, fail after with "X is not a function."

**Root cause:** Mock objects don't implement all methods the real object has. When code is updated to call new methods, the mock breaks.

**Fix:** Make mocks return chainable objects with all expected methods:
```javascript
const mkMarker = () => ({
  setLatLng() { return this; },
  setIcon() { return this; },
  addTo() { return this; },
  bindPopup() { return this; },
  on() { return this; },
});
```

### 7.3 When Browser Debugging Tools Fail

In this build, the Chrome automation extension repeatedly failed to connect. The workaround:

1. **User takes screenshots** and pastes them into the conversation
2. **AI reads the screenshots** (multimodal) to identify visual issues
3. **AI reads console errors from screenshots** to diagnose JavaScript issues
4. **Verify data flow independently** — write a small Python script to connect to the WebSocket and print messages, bypassing the browser entirely

**Lesson:** Always have a fallback debugging path that doesn't depend on any single tool.

---

## 8. Phase 4: Packaging & Delivery

### 8.1 Git Initialization and Commit

```bash
git init
git add <specific files>  # Never use git add -A blindly
git commit -m "Descriptive message"
git remote add origin <url>
git push -u origin main
```

**Watch out for:**
- `.gitignore` should be committed first to avoid tracking `node_modules/`, `__pycache__/`, etc.
- Don't commit `.env` files, credentials, or large binaries
- Stage files explicitly rather than using `git add .`

### 8.2 README Contents

A good README for a demo project includes:
1. One-paragraph description
2. Architecture diagram (ASCII art)
3. Prerequisites (Python version, Node version, packages)
4. Quick start (install + run in <5 commands)
5. What you'll see (describe the visual output)
6. How to run tests
7. Project structure (file tree with descriptions)
8. Tech stack summary

### 8.3 Launch Scripts

Create `scripts/start_all.sh` and `scripts/stop_all.sh`:
- Start script launches backend and frontend with proper ordering
- Stop script kills all related processes cleanly
- Both scripts should be idempotent (safe to run multiple times)

---

## 9. Key Pitfalls & Lessons Learned

### 9.1 Persist Everything to Disk

**The problem:** AI conversation context can be lost (crashes, context limit, session timeout). Anything that exists only in the chat is at risk.

**The rule:** Every important artifact gets written to a file immediately:
- Vision → `docs/VISION.md`
- Spec → `docs/SPEC.md`
- Plan → `docs/PLAN.md`
- Process notes → `docs/PROCESS.md`

**When the user caught this:** Midway through implementation, the user asked "Have you committed the plan to docs or somewhere else on disk?" The plan existed only in the conversation. If the session had crashed, we'd have lost the implementation roadmap and couldn't continue where we left off.

### 9.2 Test-First Prevents Drift

**The problem:** When the AI writes code without tests, it tends to drift from the spec. Small decisions accumulate into large deviations.

**The rule:** Every sub-phase produces tests alongside production code. Tests run at every gate. Tests reference spec scenarios by number.

**The payoff:** When all 370 tests pass (313 Python + 57 JS), you have high confidence the system works as specified.

### 9.3 Don't Trust "It Works in My Head"

**The problem:** The AI can generate code that looks correct but has subtle integration issues (wrong import style, missing method on a mock, off-by-one in a ring buffer).

**The rule:** Always verify with actual execution:
- Run the test suite after every phase
- Start the system and visually inspect after all phases complete
- Check the browser console — warnings matter

### 9.4 Front-Load Specificity

**The problem:** Vague requirements produce code that needs extensive rework.

**The examples:**
- "Battery drain" → needs specific rates (0.5%/min hover, 1.0%/min cruise, 1.5%/min high-speed)
- "Fault injection" → needs specific probabilities (2%/min motor, 3%/min GPS) and effects (30-50% RPM drop for 30-60s)
- "Drone personalities" → needs exact table with callsigns, initial batteries, speeds, fault multipliers

**The rule:** If you can't write a GWT test for it, the requirement isn't specific enough.

### 9.5 Layer Dependencies Correctly

**The problem:** Building things in the wrong order creates circular dependency nightmares.

**The correct order for this type of project:**
```
1. Types/enums/data structures
2. Configuration/constants
3. Independent algorithms (physics, battery, faults)
4. Orchestrator (state machine using #3)
5. Communication layer (bridge using #4)
6. Presentation layer (dashboard consuming #5)
7. Integration/e2e tests
```

### 9.6 Handle the DDS/No-DDS Duality

**The pattern:**
```python
try:
    import rti.connextdds as dds
    HAS_DDS = True
except ImportError:
    HAS_DDS = False
```

**Why it matters:** The system must run and be fully testable without proprietary DDS libraries installed. All DDS-dependent code paths have fallbacks. Tests for DDS-specific behavior are marked `@pytest.mark.skipif(not HAS_DDS)`.

**General lesson:** When building on top of optional/proprietary dependencies, design the fallback path first. The fallback path IS the test path.

### 9.7 Ring Buffers Prevent Memory Leaks

**The problem:** Telemetry data arrives at 5Hz per drone. 8 drones × 5Hz × 60 seconds = 2,400 data points per minute. Without bounds, the browser runs out of memory.

**The solution:**
- Telemetry history: 120-second ring buffer (trimmed by timestamp)
- Drone trails: 60-second ring buffer
- Alerts: capped at 100, oldest dropped

**Implementation:** Trim on every state update, using timestamp comparison rather than array length (so timing variations don't cause inconsistent behavior).

### 9.8 Python Output Buffering

**The symptom:** You start `python -m drones.run_swarm` and redirect output to a log file. The log file stays empty even though the system is running and port 8765 is listening.

**The cause:** Python buffers stdout when it's not connected to a terminal.

**The fix:** Use `python -u` (unbuffered) or `PYTHONUNBUFFERED=1` when running in the background.

---

## 10. Anti-Patterns to Avoid

### 10.1 "Just Build It" Without a Spec

Starting implementation without GWT scenarios means:
- No way to verify correctness
- No shared understanding of edge cases
- Tests written after the fact tend to test implementation, not behavior

### 10.2 One Giant Prompt

Trying to build everything in a single prompt fails because:
- Context window limits mean the AI forgets early instructions
- No intermediate test gates means errors compound
- No opportunity to catch architectural mistakes early

### 10.3 Deleting Failing Tests

When a test fails, the temptation is to adjust or remove it. Don't. The test represents a requirement from the spec. If the test is wrong, the spec is wrong — fix the spec first, then the test, then the code.

### 10.4 Skipping the Vision Discussion

Going straight from vision document to implementation skips the "neural connection" phase where misunderstandings get caught. The 15-minute discussion saves hours of rework.

### 10.5 Manual File-by-File Implementation

Without parallel agents, building 30+ files serially takes much longer. The phase/sub-phase structure is designed specifically to enable parallelism. Use it.

### 10.6 Over-Engineering the Foundation

The types and configuration phase should be simple dataclasses and constants. Don't build elaborate type validation, custom serializers, or plugin architectures in Phase 1. Keep it minimal — complexity comes from composing simple pieces.

### 10.7 Ignoring Console Warnings

"It's just a warning" is how subtle bugs survive to production. The WebSocket StrictMode warning in this build was benign but indicated a real issue (wasted connections). Always investigate warnings.

---

## 11. Checklist

### Before Starting

- [ ] Vision document written with specific numbers, tables, and diagrams
- [ ] 15-20 minute discussion to build shared understanding
- [ ] GWT spec written with 100+ scenarios covering happy paths and failure modes
- [ ] Implementation plan with phases, sub-phases, test gates, and dependency ordering
- [ ] **Plan persisted to disk** (not just in conversation)

### During Each Sub-Phase

- [ ] Production code + tests written together
- [ ] Tests reference specific SPEC scenario numbers
- [ ] Sub-phase gate passes: new tests + ALL previous tests
- [ ] No test deletions or skips

### During Parallel Execution

- [ ] Independent sub-phases identified (no shared state or imports)
- [ ] Each agent gets sufficient context (plan section + vision + specs)
- [ ] Full test suite run after agents complete, before next layer
- [ ] Integration issues fixed immediately

### During Debugging

- [ ] Backend process running and port listening
- [ ] Frontend building and serving
- [ ] Browser console checked for errors AND warnings
- [ ] Data flow verified end-to-end (producer → bridge → WebSocket → UI)
- [ ] Fallback debugging method available if primary tool fails

### Before Shipping

- [ ] All tests passing (unit + acceptance + e2e)
- [ ] `.gitignore` committed before any `git add`
- [ ] No secrets or credentials in committed files
- [ ] README with quick start instructions
- [ ] Launch/stop scripts tested
- [ ] Visual smoke test in browser

---

## Appendix: Project Stats

| Metric | Value |
|--------|-------|
| Total lines of code | ~10,000 |
| Production code | ~6,000 lines |
| Test code | ~4,000 lines |
| Python test count | 313 |
| JavaScript test count | 57 |
| Total files | 30+ |
| Build time | ~90 minutes (7:06 PM – 8:35 PM) |
| Phases | 5 |
| Sub-phases | 17 |
| SPEC scenarios | ~120 |
| Drones simulated | 8 |
| Mission patterns | 7 |

---

_This process document was generated from the actual build session of the DDS Drone Swarm Monitoring System, capturing what worked, what broke, and what to do differently next time._
