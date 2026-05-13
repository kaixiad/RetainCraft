# 🧠 RetainCraft

> Evidence-based AI-assisted interactive learning protocol for OpenClaw
> 基于循证学习科学的 AI 辅助互动学习协议
>
> *Previously known as "interactive-learning"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What is this?

An [OpenClaw](https://github.com/openclaw) skill that turns 5 scientifically validated learning methods into an interactive system between you and your AI.

Not "here's some material, figure it out yourself" — your AI studies with you, quizzes you, tracks your progress, and reminds you before you forget.

## Features

- **5 evidence-based methods** in one protocol: spaced repetition (d=0.85), active recall (d=0.74), Feynman technique (d=0.54), interleaved practice (d=0.47), elaborative interrogation (d=0.56) — all effect sizes from [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) meta-analysis (242 studies, 169k participants)
- **SM-2 spaced repetition**: auto-calculates review intervals, not fixed schedules
- **Pre-assessment + module tests**: quantifies learning with before/after comparison
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
# From ClawHub
openclaw skills install retaincraft

# Manual
git clone https://github.com/kaixiad/RetainCraft.git ~/.openclaw/workspace/skills/retaincraft
```

## Usage

Tell your AI:
- "I want to learn linear algebra"
- "Teach me Bayes' theorem"
- "Help me make a study plan"

The AI will automatically start the full learning workflow.

## File Structure

```
retaincraft/
├── SKILL.md                    # Main file (execution checklist + workflow)
├── README.md                   # This file
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guide
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI/CD
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── pull_request_template.md # PR template
├── docs/
│   └── docu-review-report.md   # Documentation audit report
└── scripts/
    ├── srs.py                  # SM-2 spaced repetition engine + level system
    ├── test_srs.py             # Unit tests (127 test cases)
    ├── scenarios.md            # Simulation scenario library (7 scenarios)
    ├── evidence.md             # Academic citations and effect sizes
    ├── templates.md            # Output format templates
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
└── config.json                 # Learning preferences
```

## CLI Commands

```bash
python3 scripts/srs.py init <topic>              # Create a topic
python3 scripts/srs.py add <topic> <concept>     # Add a concept
python3 scripts/srs.py review <topic>            # Start review session (interactive)
python3 scripts/srs.py rate <topic> <concept> <rating>  # Rate concept (non-interactive, for AI)
python3 scripts/srs.py due                       # Show today's due reviews
python3 scripts/srs.py status [topic]            # Overview / single topic status
python3 scripts/srs.py record-test <topic> <total> <correct>  # Record module test result
python3 scripts/srs.py test-history [topic]      # View test history
python3 scripts/srs.py record-simulation <topic> <scenario> <score> [--rounds N]  # Record simulation
python3 scripts/srs.py simulation-history [topic]  # View simulation history
python3 scripts/srs.py config                    # View/set configuration
```

## Academic References

| Method | Effect Size | Source |
|--------|------------|--------|
| Spaced Repetition | d=0.85 | [Donoghue & Hattie 2021](https://doi.org/10.3389/feduc.2021.581216) |
| Active Recall | d=0.74 | Donoghue & Hattie 2021 |
| Elaborative Interrogation | d=0.56 | Donoghue & Hattie 2021 |
| Self-Explanation / Feynman | d=0.54 | Donoghue & Hattie 2021 |
| Interleaved Practice | d=0.47 | Donoghue & Hattie 2021 |
| AI Tutoring | 0.63-1.3 SD | [Kestin et al. 2025](https://doi.org/10.1038/s41598-025-97652-6) (Harvard RCT, N=194) |

> All d values from Donoghue & Hattie (2021) meta-analysis (242 studies, 1,619 effect sizes, 169,179 participants). Dunlosky et al. (2013) uses qualitative classification (high/moderate/low utility), not Cohen's d.

## Known Limitations

- **SM-2 algorithm**: This is a well-proven but decades-old algorithm. FSRS (a modern ML-based alternative) migration is planned for a future release.
- **No user validation data yet**: The learning methods are evidence-based, but this specific implementation has not yet been validated with real users at scale.
- **AI judgment in Feynman test**: The AI evaluates whether your explanation is correct. This relies on the underlying LLM's accuracy — cross-check critical knowledge with authoritative sources.
- **Single-language interface**: CLI output and documentation are primarily in Chinese. English interface support is planned.

## Documentation Quality

This project underwent an independent documentation audit:

| Item | Status |
|------|--------|
| All citations verified as real | ✅ |
| Effect size numbers accurate | ✅ |
| Research institution attribution correct | ✅ |
| Protocol logic consistent | ✅ |
| Code tests passing | ✅ |
| Needs customization | ⚠️ Generic template — adapt to your background |

Full audit report: `docs/docu-review-report.md`

## AI-Assisted Development Disclosure

This project was developed with assistance from MiMo-v2.5-Pro, OpenClaw, WorkBuddy, and CodeBuddy. Core architecture design, learning methodology selection, academic citation verification, and code review were done by hand. AI tools assisted with code generation, documentation drafting, and literature search. All AI-generated content has been manually reviewed and verified.

## License

MIT License — free to use, modify, and distribute.
