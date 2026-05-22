# 🧠 RetainCraft

[English](README.md) | [中文](README.zh-CN.md)

> Evidence-based AI-assisted interactive learning protocol for AI agents (OpenClaw compatible)
>
> *Previously known as "interactive-learning"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What is this?

An [AI agent skill](https://github.com/kaixiad/RetainCraft) (OpenClaw compatible) that turns 5 scientifically validated learning methods into an interactive system between you and your AI.

Not "here's some material, figure it out yourself" — your AI studies with you, quizzes you, tracks your progress, and reminds you before you forget.

## Features

- **5 evidence-based methods** in one protocol: distributed practice (d=0.85), practice testing (d=0.74), self-explanation (d=0.54), interleaved practice (d=0.47), elaborative interrogation (d=0.56) — all effect sizes from [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) meta-analysis (242 studies, 169k participants). We implement these as: spaced repetition (code-enforced), active recall (hybrid), Feynman technique (AI-guided), interleaved practice (AI-guided), and causal questioning (AI-guided). See Academic References below for execution layer details.
- **FSRS-5 spaced repetition (default)**: ML-based scheduling from IEEE TKDE 2023 research, with SM-2 as fallback. Personalizable via `optimize-params` after 1000+ reviews
- **Pre-assessment + module tests**: quantifies learning with before/after comparison
- **Reminder system**: daily learning plans + weekly reports, platform-native notifications
- **Learning contract**: "If X happens, I will do Y" format based on implementation intentions (Gollwitzer 1999)
- **Forgetting risk**: Ebbinghaus curve analysis, warns when knowledge is about to decay
- **Burnout detection**: auto-lowers difficulty or suggests breaks after consecutive mistakes
- **Search-first policy**: AI verifies facts before answering, cites sources
- **Persistent memory**: learning data survives across sessions
- **Heartbeat integration**: auto-reminds when reviews are due

## Prerequisites

- Python >= 3.10
- No external dependencies — Python standard library only

> **Windows users**: use `python` instead of `python3` if the latter is not available.

## Installation

```bash
# OpenClaw (from ClawHub)
openclaw skills install retaincraft

# OpenClaw (manual)
git clone https://github.com/kaixiad/RetainCraft.git ~/.openclaw/workspace/skills/retaincraft

# WorkBuddy / Claude Code / Other AI agents
git clone https://github.com/kaixiad/RetainCraft.git
# Then point your agent to the SKILL.md file
```

## Usage

### Quick Start

Tell your AI:
- "I want to learn linear algebra"
- "Teach me Bayes' theorem"
- "Help me make a study plan"

The AI will automatically start the full learning workflow.

### First Session Setup

1. **Create a topic**: AI runs `srs.py init <topic>`
2. **Add concepts**: AI discovers and adds key concepts
3. **Setup reminders**: AI creates timed learning reminders (via `setup-reminder` on OpenClaw, or sign-contract on other platforms)
4. **Sign a learning contract**: AI helps you create "If X, then Y" plans (Gollwitzer 1999)

### Daily Workflow

1. **Check due reviews**: `srs.py due` — see what's due today
2. **Review + rate**: `srs.py review <topic>` — interactive review session
3. **Module test**: Periodic tests to track level progression (L1→L5)
4. **Weekly report**: `srs.py weekly-report` — review your learning trends

## File Structure

```
retaincraft/
├── SKILL.md                    # Main file (execution checklist + workflow)
├── README.md                   # English readme
├── README.zh-CN.md             # Chinese readme
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guide
├── requirements.txt            # Python version requirement
├── learning-templates.json     # Pre-built learning templates
├── references/
│   └── full-workflow.md        # Detailed workflow reference
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI/CD
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── pull_request_template.md # PR template
└── scripts/
    ├── srs.py                  # FSRS-5 (default) + SM-2 spaced repetition engine + level system
    ├── test_srs.py             # Unit tests (169 test cases)
    ├── scenarios.md            # Simulation scenario library (7 scenarios)
    ├── evidence.md             # Academic citations and effect sizes
    └── templates.md            # Output format templates
```

## Data Storage

```
~/learn/
├── topics/{topic}/
│   ├── concepts.json           # SM-2 state per concept
│   ├── notes.md                # Learning notes
│   └── progress.md             # Mastery tracking
├── test_history.json           # Module test history
├── simulation_history.json     # Simulation history
├── learning_log.json           # Learning activity log (v1.2.0)
└── config.json                 # Learning preferences
```

## CLI Commands

```bash
# Core
python3 scripts/srs.py init <topic>              # Create a topic
python3 scripts/srs.py add <topic> <concept>     # Add a concept
python3 scripts/srs.py review <topic>            # Start review session (interactive)
python3 scripts/srs.py rate <topic> <concept> <rating>  # Rate concept (non-interactive, for AI)
python3 scripts/srs.py due                       # Show today's due reviews
python3 scripts/srs.py status [topic]            # Overview / single topic status

# Testing
python3 scripts/srs.py record-test <topic> <total> <correct>  # Record module test result
python3 scripts/srs.py test-history [topic]      # View test history
python3 scripts/srs.py record-simulation <topic> <scenario> <score> [--rounds N]  # Record simulation
python3 scripts/srs.py simulation-history [topic]  # View simulation history

# Profile
python3 scripts/srs.py profile                   # Show user profile
python3 scripts/srs.py profile --update          # Update profile for all topics
python3 scripts/srs.py profile --compare <job>   # Compare profile with job requirements

# Diagnostics
python3 scripts/srs.py check-session [topic]     # Check for unrecorded tests
python3 scripts/srs.py check-burnout <topic>     # Analyze burnout risk

# Reminders
python3 scripts/srs.py setup-reminder            # Setup learning reminder + weekly report cron
python3 scripts/srs.py reminder                  # Generate today's learning plan
python3 scripts/srs.py weekly-report             # Generate weekly report data
python3 scripts/srs.py check-reminder            # Check reminder status
python3 scripts/srs.py switch-channel            # Switch reminder notification channel

# Config
python3 scripts/srs.py config                    # View/set configuration
python3 scripts/srs.py config set algorithm sm2  # Switch to SM-2 algorithm (FSRS-5 is default)

# v1.3.0 New
python3 scripts/srs.py today                     # Today's learning plan with overdue analysis
python3 scripts/srs.py streak                    # Consecutive learning days
python3 scripts/srs.py analyze                   # Learning trends and weak concepts
python3 scripts/srs.py optimize-params           # Personalize FSRS-5 weights (needs 1000+ reviews)

# v1.4.0 New
python3 scripts/srs.py sign-contract             # Sign learning contract + create reminder
```

## Academic References

| Method | Effect Size | Execution Layer | Source |
|--------|------------|----------------|--------|
| Spaced Repetition | d=0.85 | 🟢 Code | [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) |
| Active Recall | d=0.74 | 🟢🟡 Hybrid | Donoghue & Hattie 2021 |
| Causal Questioning | d=0.56 | 🔵 AI-Guided | Donoghue & Hattie 2021 |
| Self-Explanation / Feynman | d=0.54 | 🔵 AI-Guided | Donoghue & Hattie 2021 |
| Interleaved Practice | d=0.47 | 🔵 AI-Guided | Donoghue & Hattie 2021 |
| AI Tutoring | 0.63-1.3 SD | 🟢🟡 Hybrid | [Kestin et al. 2025](https://doi.org/10.1038/s41598-025-97652-6) (Harvard RCT, N=194) |
| Implementation Intentions | — | 🟢 Code | [Gollwitzer 1999](https://doi.org/10.1037/0003-066X.54.7.493) (Learning Contract) |
| Burnout Theory | — | ⚪ Reference | [Maslach & Leiter 2016](https://doi.org/10.1002/wps.20273) (Burnout Detection) |
| Procrastination | — | ⚪ Reference | [Steel 2007](https://doi.org/10.1037/0033-2909.133.1.65) (Forgetting Risk) |
| Forgetting Curve | — | 🟢 Code | [Ebbinghaus 1885](https://doi.org/10.1371/journal.pone.0120644) (Murre & Dros 2015 validation) |
| Self-Efficacy | — | ⚪ Reference | [Bandura 1997](https://en.wikipedia.org/wiki/Self-efficacy) (Weekly Report) |

> 🟢 Code-enforced | 🟢🟡 Hybrid (code + AI) | 🔵 AI-guided (conversation) | ⚪ Theoretical reference
> All citations verified, detailed evidence in [evidence.md](scripts/evidence.md).

## Known Limitations

- **No user validation data yet**: The learning methods are evidence-based, but this specific implementation has not yet been validated with real users at scale.
- **AI judgment in Feynman test**: The AI evaluates whether your explanation is correct. This relies on the underlying LLM's accuracy — cross-check critical knowledge with authoritative sources.

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| v1.3.0 | FSRS-5 (default) + SM-2 fallback + 4 new commands + optimize-params | ✅ Done |
| v1.4.0 | Multi-agent-framework reminder + sign-contract + learning_log pruning | ✅ Done |
| v1.5.0 | Learning video search + AI hallucination defense | Planned |

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Documentation Quality

This project underwent an independent documentation audit:

| Item | Status |
|------|--------|
| All citations verified as real | ✅ |
| Effect size numbers accurate | ✅ |
| Research institution attribution correct | ✅ |
| Protocol logic consistent | ✅ |
| Code tests passing (169/169) | ✅ |

## AI-Assisted Development Disclosure

This project was developed with assistance from MiMo-v2.5-Pro, OpenClaw, WorkBuddy, and CodeBuddy. Core architecture design, learning methodology selection, academic citation verification, and code review were done by hand. AI tools assisted with code generation, documentation drafting, and literature search. All AI-generated content has been manually reviewed and verified.

## License

MIT License — free to use, modify, and distribute.
