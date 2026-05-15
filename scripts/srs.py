#!/usr/bin/env python3
"""
SM-2 Spaced Repetition System for RetainCraft skill.

Usage:
    python3 srs.py init <topic>              # Create a new topic
    python3 srs.py add <topic> <concept>     # Add a concept to a topic
    python3 srs.py review <topic>            # Start a review session
    python3 srs.py rate <topic> <concept> <rating>  # Rate a concept (non-interactive)
    python3 srs.py due                       # Show all due reviews
    python3 srs.py status                    # Show overall status
    python3 srs.py status <topic>            # Show topic status
    python3 srs.py record-test <topic> <total> <correct>  # Record a test result
    python3 srs.py test-history [topic]      # Show test history
    python3 srs.py record-simulation <topic> <scenario> <score> [--rounds N]  # Record a simulation result
    python3 srs.py simulation-history [topic]  # Show simulation history
    python3 srs.py profile                   # Show user profile
    python3 srs.py profile --update          # Update profile for all topics
    python3 srs.py profile --compare <job>   # Compare profile with job requirements
    python3 srs.py check-session [topic]      # Check for unrecorded tests
    python3 srs.py check-burnout <topic>      # Analyze burnout risk
    python3 srs.py config                     # Show config
    python3 srs.py config set <key> <value>  # Set config value
    python3 srs.py setup-reminder             # Setup learning reminder + weekly report cron
    python3 srs.py reminder                   # Generate today's learning plan
    python3 srs.py weekly-report              # Generate weekly report data
    python3 srs.py check-reminder             # Check reminder status
    python3 srs.py switch-channel             # Switch reminder notification channel

Storage: ~/learn/
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# --- Path traversal protection ---

class SanitizeError(ValueError):
    """Raised when a topic or concept name contains invalid characters."""
    pass


# Pattern: letters, digits, hyphens, underscores, and CJK characters only
_SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$')


def sanitize_topic(topic: str) -> str:
    """
    Validate and sanitize a topic name to prevent path traversal attacks.

    Args:
        topic: Raw topic name from user input

    Returns:
        The validated topic name (unchanged if valid)

    Raises:
        SanitizeError: If the topic name contains invalid characters
    """
    if not topic or not _SAFE_NAME_PATTERN.match(topic):
        raise SanitizeError(
            f"Invalid topic name: '{topic}'. "
            "Only letters, digits, hyphens, underscores, and CJK characters are allowed."
        )
    return topic


def sanitize_concept(concept_name: str) -> str:
    """
    Validate and sanitize a concept name to prevent path traversal attacks.

    Args:
        concept_name: Raw concept name from user input

    Returns:
        The validated concept name (unchanged if valid)

    Raises:
        SanitizeError: If the concept name is empty, too long, or contains invalid characters
    """
    if not concept_name or not _SAFE_NAME_PATTERN.match(concept_name):
        raise SanitizeError(
            f"Invalid concept name: '{concept_name}'. "
            "Only letters, digits, hyphens, underscores, and CJK characters are allowed."
        )
    if len(concept_name) > 200:
        raise SanitizeError(
            f"Concept name too long ({len(concept_name)} chars). Maximum length is 200 characters."
        )
    return concept_name


LEARN_DIR = Path.home() / "learn"
TOPICS_DIR = LEARN_DIR / "topics"
CONFIG_FILE = LEARN_DIR / "config.json"
TEST_HISTORY_FILE = LEARN_DIR / "test_history.json"
SIMULATION_HISTORY_FILE = LEARN_DIR / "simulation_history.json"
PROFILE_FILE = LEARN_DIR / "profile.json"
LEARNING_LOG_FILE = LEARN_DIR / "learning_log.json"

# For cron detection (used by setup-reminder)
SCRIPTS_DIR = Path(__file__).parent

DEFAULT_CONFIG = {
    "learning_depth": "standard",
    "learner_type": "practical",
    "daily_review_limit": 20,
    "session_duration": 60,
    "burnout_threshold": 3,
    "mastery_threshold": 0.8,
    "level_thresholds": {
        "L2": 0.2,
        "L3": 0.4,
        "L4": 0.7,
        "L5": 0.9
    }
}

DEFAULT_CONCEPT = {
    "added": None,
    "interval_days": 1,
    "next_review": None,
    "ease_factor": 2.5,
    "reviews": 0,
    "correct_count": 0,
    "total_count": 0,
    "mastery": "unseen",
}


def _atomic_json_save(filepath: Path, data: dict) -> None:
    """
    Atomically write JSON data to a file using temp file + os.replace.

    This prevents data corruption if the process is interrupted during write.

    Args:
        filepath: Target file path
        data: Data to serialize as JSON
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=filepath.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _atomic_text_save(filepath: Path, content: str) -> None:
    """
    Atomically write text content to a file using temp file + os.replace.

    This prevents data corruption if the process is interrupted during write.

    Args:
        filepath: Target file path
        content: Text content to write

    Raises:
        OSError: If the file cannot be written
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=filepath.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_learning_log() -> list[dict[str, Any]]:
    """
    Load learning log from file.

    Returns:
        List of learning log entries
    """
    if LEARNING_LOG_FILE.exists():
        try:
            with open(LEARNING_LOG_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def append_learning_log(action: str, topic: str, details: dict[str, Any]) -> None:
    """
    Append an entry to the learning log.

    Args:
        action: Action type (e.g., "rate", "record-test")
        topic: Topic name
        details: Additional details about the action
    """
    log = load_learning_log()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "topic": topic,
        **details
    }
    log.append(entry)
    LEARNING_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_save(LEARNING_LOG_FILE, log)


def get_last_learning_time() -> datetime | None:
    """
    Get the timestamp of the last learning activity.

    Returns:
        datetime of last activity, or None if no activity found
    """
    log = load_learning_log()
    if not log:
        return None
    try:
        last_entry = log[-1]
        return datetime.fromisoformat(last_entry["timestamp"])
    except (ValueError, KeyError):
        return None


def load_test_history() -> dict[str, list[dict[str, Any]]]:
    """
    Load test history from file.
    
    Returns:
        Dictionary mapping topics to test history lists
    """
    if TEST_HISTORY_FILE.exists():
        try:
            with open(TEST_HISTORY_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_test_history(history: dict[str, list[dict[str, Any]]]) -> None:
    """
    Save test history to file using atomic write.
    
    Args:
        history: Dictionary mapping topics to test history lists
    """
    ensure_dirs()
    _atomic_json_save(TEST_HISTORY_FILE, history)


def record_test(topic: str, total: int, correct: int) -> dict[str, Any]:
    """
    Record a test result for a topic.
    
    Args:
        topic: Topic name
        total: Total number of questions
        correct: Number of correct answers
    
    Returns:
        Recorded test result dictionary
    
    Raises:
        ValueError: If input parameters are invalid
    """
    # Validate input
    topic = sanitize_topic(topic)
    if total <= 0:
        raise ValueError(f"Total questions must be positive, got: {total}")
    if correct < 0:
        raise ValueError(f"Correct answers cannot be negative, got: {correct}")
    if correct > total:
        raise ValueError(f"Correct answers ({correct}) cannot exceed total ({total})")
    
    history = load_test_history()
    if topic not in history:
        history[topic] = []
    
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "accuracy": correct / total,
        "total": total,
        "correct": correct
    }
    history[topic].append(test_result)
    save_test_history(history)
    # Log the test action
    append_learning_log("record-test", topic, {
        "total": total,
        "correct": correct,
        "accuracy": correct / total
    })
    return test_result


def load_simulation_history() -> dict[str, list[dict[str, Any]]]:
    """
    Load simulation history from file.
    
    Returns:
        Dictionary mapping topics to simulation history lists
    """
    if SIMULATION_HISTORY_FILE.exists():
        try:
            with open(SIMULATION_HISTORY_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_simulation_history(history: dict[str, list[dict[str, Any]]]) -> None:
    """
    Save simulation history to file using atomic write.
    
    Args:
        history: Dictionary mapping topics to simulation history lists
    """
    ensure_dirs()
    _atomic_json_save(SIMULATION_HISTORY_FILE, history)


def record_simulation(topic: str, scenario: str, score: int, rounds: int = 3) -> dict[str, Any]:
    """
    Record a simulation result for a topic.
    
    Args:
        topic: Topic name
        scenario: Scenario name
        score: Simulation score (0-100)
        rounds: Number of rounds (default: 3)
    
    Returns:
        Recorded simulation result dictionary
    
    Raises:
        ValueError: If input parameters are invalid
    """
    # Validate input
    topic = sanitize_topic(topic)
    if score < 0 or score > 100:
        raise ValueError(f"Simulation score must be between 0-100, got: {score}")
    if rounds < 1:
        raise ValueError(f"Simulation rounds must be positive, got: {rounds}")
    
    history = load_simulation_history()
    if topic not in history:
        history[topic] = []
    
    simulation_result = {
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario,
        "score": score,
        "rounds": rounds
    }
    history[topic].append(simulation_result)
    save_simulation_history(history)
    # Log the simulation action
    append_learning_log("record-simulation", topic, {
        "scenario": scenario,
        "score": score,
        "rounds": rounds
    })
    return simulation_result


def check_session(topic: str | None = None, stale_minutes: int = 120) -> dict[str, Any]:
    """
    Check if there are unrecorded module tests in the current session.

    Compares the timestamp of the last record-test call against the current
    time. If the gap exceeds *stale_minutes*, the session is flagged so
    the AI can remind the user (or the user can invoke this manually).

    Args:
        topic: Topic name to check (None = all topics)
        stale_minutes: Minutes of silence after which a record is considered stale (default 120)

    Returns:
        Dictionary with check result details
    """
    history = load_test_history()
    topics_to_check = [topic] if topic else list(history.keys())

    if not topics_to_check:
        return {
            "status": "no_history",
            "message": "No test history found. Start learning first!",
        }

    now = datetime.now()
    findings: list[dict[str, Any]] = []

    for t in topics_to_check:
        tests = history.get(t, [])
        if not tests:
            continue
        latest = tests[-1]
        ts = datetime.fromisoformat(latest["timestamp"])
        gap_minutes = (now - ts).total_seconds() / 60

        finding: dict[str, Any] = {
            "topic": t,
            "last_record": latest["timestamp"],
            "gap_minutes": round(gap_minutes, 1),
            "last_accuracy": latest["accuracy"],
            "stale": gap_minutes > stale_minutes,
        }
        findings.append(finding)

    if not findings:
        return {
            "status": "no_history",
            "message": "No test history found.",
        }

    stale_topics = [f for f in findings if f["stale"]]
    status = "stale" if stale_topics else "fresh"

    return {
        "status": status,
        "stale_minutes_threshold": stale_minutes,
        "findings": findings,
        "stale_count": len(stale_topics),
    }


def check_burnout(topic: str, window: int = 5) -> dict[str, Any]:
    """
    Analyze burnout risk for a topic based on recent test trends.

    Looks at the last *window* tests and computes:
      - accuracy trend (declining / stable / improving)
      - consecutive below-50% tests
      - average accuracy over the window

    Returns a structured burnout assessment.

    Args:
        topic: Topic name to analyze
        window: Number of recent tests to consider (default 5)

    Returns:
        Dictionary with burnout analysis
    """
    topic = sanitize_topic(topic)
    history = load_test_history().get(topic, [])

    if len(history) == 0:
        return {
            "status": "no_data",
            "topic": topic,
            "message": "No test history found for this topic.",
        }

    recent = history[-window:]

    # Calculate trend (compare first half avg vs second half avg)
    mid = len(recent) // 2
    if mid == 0:
        first_half_avg = recent[0]["accuracy"]
        second_half_avg = recent[0]["accuracy"]
    else:
        first_half_avg = sum(t["accuracy"] for t in recent[:mid]) / mid
        second_half_avg = (
            sum(t["accuracy"] for t in recent[mid:]) / (len(recent) - mid)
        )

    diff = second_half_avg - first_half_avg
    if diff < -0.1:
        trend = "declining"
    elif diff > 0.1:
        trend = "improving"
    else:
        trend = "stable"

    # Count consecutive below-50% tests from the end
    consecutive_low = 0
    for t in reversed(recent):
        if t["accuracy"] < 0.5:
            consecutive_low += 1
        else:
            break

    avg_accuracy = sum(t["accuracy"] for t in recent) / len(recent)

    # Burnout risk level
    if consecutive_low >= 3 or (trend == "declining" and avg_accuracy < 0.4):
        risk = "high"
    elif consecutive_low >= 2 or (trend == "declining" and avg_accuracy < 0.6):
        risk = "medium"
    else:
        risk = "low"

    suggestions = []
    if risk == "high":
        suggestions.append("休息至少 30 分钟后再继续学习。")
        suggestions.append("复习已掌握的概念以重建信心。")
        suggestions.append("考虑暂时切换到其他主题。")
    elif risk == "medium":
        suggestions.append("缩短下次学习时长。")
        suggestions.append("专注复习薄弱点，不要学新内容。")
        suggestions.append("如果感到疲劳，休息 10-15 分钟。")

    return {
        "status": "ok",
        "topic": topic,
        "window": window,
        "recent_tests": len(recent),
        "avg_accuracy": round(avg_accuracy, 3),
        "trend": trend,
        "consecutive_below_50": consecutive_low,
        "risk": risk,
        "suggestions": suggestions,
    }


def load_profile() -> dict[str, Any]:
    """
    Load user profile from file.
    
    Returns:
        User profile dictionary
    """
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "goal": "",
        "started": today(),
        "total_hours": 0,
        "topics": {},
        "strengths": [],
        "weaknesses": [],
        "last_updated": datetime.now().isoformat()
    }


def save_profile(profile: dict[str, Any]) -> None:
    """
    Save user profile to file using atomic write.
    
    Args:
        profile: User profile dictionary to save
    """
    ensure_dirs()
    profile["last_updated"] = datetime.now().isoformat()
    _atomic_json_save(PROFILE_FILE, profile)


def update_profile(topic: str) -> dict[str, Any]:
    """
    Update user profile with topic data.
    
    Args:
        topic: Topic name to update
    
    Returns:
        Updated user profile dictionary
    """
    topic = sanitize_topic(topic)
    profile = load_profile()
    concepts = load_concepts(topic)
    test_history = load_test_history().get(topic, [])

    # Calculate topic stats
    mastered, total, _ = calc_mastery_overview(concepts)
    level_code, _, _ = calc_level_by_accuracy(topic, concepts_fallback=concepts)

    # Calculate test average
    test_avg = 0
    if test_history:
        test_avg = sum(t["accuracy"] for t in test_history) / len(test_history) * 100

    # Calculate total hours (estimate from test count)
    # Rough estimate: each test takes ~15 minutes
    hours = len(test_history) * 0.25

    # Update topic data
    profile["topics"][topic] = {
        "level": level_code,
        "status": "completed" if level_code in ("L4", "L5") else "in_progress",
        "hours": hours,
        "concepts_mastered": mastered,
        "concepts_total": total,
        "test_avg": test_avg
    }

    # Update total hours
    profile["total_hours"] = sum(t["hours"] for t in profile["topics"].values())

    # Update strengths and weaknesses
    strengths = []
    weaknesses = []
    for name, c in concepts.items():
        if c["mastery"] == "mastered":
            strengths.append(name)
        elif c["mastery"] == "learning":
            weaknesses.append(name)
    profile["strengths"] = strengths[:10]  # Top 10
    profile["weaknesses"] = weaknesses[:10]  # Top 10

    save_profile(profile)
    return profile


def compare_profile_with_job(job_title: str) -> dict[str, Any]:
    """
    Compare user profile with job requirements.
    
    Args:
        job_title: Job title to compare with
    
    Returns:
        Dictionary with comparison results
    """
    profile = load_profile()
    
    # Get current level from topics
    topics = profile.get("topics", {})
    if not topics:
        return {
            "job_title": job_title,
            "current_level": "L1",
            "mastered_skills": [],
            "weaknesses": [],
            "total_hours": 0,
            "suggestion": "Run Step 2a industry research to search for job requirements."
        }
    
    # Find the highest level topic (use numeric comparison)
    highest_level = "L1"
    highest_level_num = 1
    total_hours = 0
    
    for _, data in topics.items():
        level = data.get("level", "L1")
        # Extract numeric level for comparison
        try:
            level_num = int(level[1:])
        except (ValueError, IndexError):
            level_num = 1
        if level_num > highest_level_num:
            highest_level = level
            highest_level_num = level_num
        total_hours += data.get("hours", 0)
    
    # Get strengths and weaknesses from profile
    strengths = profile.get("strengths", [])
    weaknesses = profile.get("weaknesses", [])
    
    return {
        "job_title": job_title,
        "current_level": highest_level,
        "mastered_skills": strengths[:10],
        "weaknesses": weaknesses[:10],
        "total_hours": total_hours,
        "suggestion": f"Run Step 2a industry research to search for '{job_title} 岗位要求' and get gap analysis."
    }


def calc_level_by_accuracy(topic: str, concepts_fallback: dict[str, Any] | None = None) -> tuple[str, str, str]:
    """
    Calculate level based on test accuracy (not SM-2 mastery).
    
    Args:
        topic: Topic name
        concepts_fallback: Optional concepts dictionary for fallback calculation
    
    Returns:
        Tuple of (level_code, level_name, level_emoji)
    
    算法说明：
    1. 初始等级为L1
    2. 前2次测试平均答对率 >= 20% → 升级到L2
    3. 遍历所有相邻测试对，检查是否满足下一级阈值：
       - L2→L3: 连续2次 >= 40%
       - L3→L4: 连续2次 >= 70%
       - L4→L5: 连续2次 >= 90%
    4. 每次匹配成功只升一级，不能跳级
    5. 降级检查：如果最近3次测试都低于当前等级阈值，则降一级
    6. 最低降到L2，L1只在无测试历史时触发
    """
    history = load_test_history().get(topic, [])

    # 从 config.json 读取等级阈值
    config = load_config()
    level_thresholds = config["level_thresholds"]

    if len(history) == 0:
        if concepts_fallback:
            _, _, pct = calc_mastery_overview(concepts_fallback)
            if pct >= 0.9:
                return "L4", "熟练 (Proficient)", "[L4]"
            elif pct >= 0.5:
                return "L3", "进阶 (Intermediate)", "[L3]"
            elif pct >= 0.2:
                return "L2", "初学 (Beginner)", "[L2]"
        return "L1", "入门 (Novice)", "[L1]"

    if len(history) == 1:
        avg = history[0]["accuracy"]
        if avg >= level_thresholds["L2"]:
            return "L2", "初学 (Beginner)", "[L2]"
        return "L1", "入门 (Novice)", "[L1]"

    # --- Tiered upgrade: walk through test pairs from L1 ---
    level = 1
    first_avg = sum(h["accuracy"] for h in history[:2]) / 2
    if first_avg >= level_thresholds["L2"]:
        level = 2

    thresholds = {3: level_thresholds["L3"], 4: level_thresholds["L4"], 5: level_thresholds["L5"]}
    next_level = 3
    for i in range(len(history) - 1):
        if next_level > 5:
            break
        pair = history[i:i+2]
        threshold = thresholds[next_level]
        # Only upgrade if current level is at least next_level - 1 (no skipping)
        if all(h["accuracy"] >= threshold for h in pair) and level >= next_level - 1:
            level = next_level
            next_level += 1

    # --- Demotion check ---
    # Maintain thresholds: L2=0.2, L3=0.4, L4=0.7, L5=0.9
    # Demotion check: only demote ONE level per check (gradual degradation)
    # SM-2 principle: incorrect answers reset interval but don't skip stages
    # Ebbinghaus: forgetting is continuous, not stepwise
    maintain_thresholds = {2: level_thresholds["L2"], 3: level_thresholds["L3"], 4: level_thresholds["L4"], 5: level_thresholds["L5"]}

    if level >= 3 and len(history) >= 3:
        threshold = maintain_thresholds[level]
        last3 = history[-3:]
        if all(h["accuracy"] < threshold for h in last3):
            level -= 1  # demote one level only

    level_map = {
        "L1": ("L1", "入门 (Novice)", "[L1]"),
        "L2": ("L2", "初学 (Beginner)", "[L2]"),
        "L3": ("L3", "进阶 (Intermediate)", "[L3]"),
        "L4": ("L4", "熟练 (Proficient)", "[L4]"),
        "L5": ("L5", "精通 (Mastery)", "[L5]")
    }
    return level_map.get(f"L{level}", level_map["L1"])


def calc_mastery_overview(concepts: dict[str, Any]) -> tuple[int, int, float]:
    """
    Calculate mastery overview for display purposes only.
    NOT used for level calculation.
    
    Args:
        concepts: Dictionary of concepts
    
    Returns:
        Tuple of (mastered_count, total_count, percentage)
    """
    if not concepts:
        return 0, 0, 0
    total = len(concepts)
    mastered = sum(1 for c in concepts.values() if c["mastery"] == "mastered")
    pct = mastered / total if total > 0 else 0
    return mastered, total, pct


def ensure_dirs() -> None:
    """Ensure required directories exist."""
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)


# Cache for config to avoid repeated file reads
_config_cache: dict[str, Any] | None = None
_config_cache_time: float | None = None


def load_config(use_cache: bool = True) -> dict[str, Any]:
    """
    Load configuration from file with optional caching.
    
    Args:
        use_cache: Whether to use cached config (default: True)
    
    Returns:
        Configuration dictionary
    """
    global _config_cache, _config_cache_time
    
    # Check cache validity (5 minutes)
    if use_cache and _config_cache is not None and _config_cache_time is not None:
        if (datetime.now().timestamp() - _config_cache_time) < 300:  # 5 minutes
            return copy.deepcopy(_config_cache)
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding='utf-8') as f:
                config = json.load(f)
            # Merge with defaults for missing keys
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading config file: {e}")
            config = DEFAULT_CONFIG.copy()
    else:
        config = DEFAULT_CONFIG.copy()
    
    # Update cache
    _config_cache = copy.deepcopy(config)
    _config_cache_time = datetime.now().timestamp()
    
    return config


def save_config(config: dict[str, Any]) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
    """
    global _config_cache, _config_cache_time
    
    ensure_dirs()
    _atomic_json_save(CONFIG_FILE, config)
    
    # Invalidate cache
    _config_cache = None
    _config_cache_time = None


def load_concepts(topic: str) -> dict[str, Any]:
    """
    Load concepts for a specific topic.
    
    Args:
        topic: Topic name
    
    Returns:
        Dictionary of concepts
    """
    topic_dir = TOPICS_DIR / topic
    concepts_file = topic_dir / "concepts.json"
    if concepts_file.exists():
        try:
            with open(concepts_file, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_concepts(topic: str, concepts: dict[str, Any]) -> None:
    """
    Save concepts for a specific topic using atomic write.
    
    Args:
        topic: Topic name
        concepts: Dictionary of concepts to save
    """
    ensure_dirs()
    topic_dir = TOPICS_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    concepts_file = topic_dir / "concepts.json"
    _atomic_json_save(concepts_file, concepts)


def load_progress(topic: str) -> str:
    """
    Load progress content for a specific topic.
    
    Args:
        topic: Topic name
    
    Returns:
        Progress content as string
    """
    topic_dir = TOPICS_DIR / topic
    progress_file = topic_dir / "progress.md"
    if progress_file.exists():
        return progress_file.read_text()
    return ""


def save_progress(topic: str, content: str) -> None:
    """
    Save progress content for a specific topic.
    
    Args:
        topic: Topic name
        content: Progress content to save
    """
    topic_dir = TOPICS_DIR / topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    progress_file = topic_dir / "progress.md"
    _atomic_text_save(progress_file, content)


def today() -> str:
    """
    Get today's date as string.
    
    Returns:
        Today's date in YYYY-MM-DD format
    """
    return datetime.now().strftime("%Y-%m-%d")


def calc_next_review(concept: dict[str, Any], rating: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    SM-2 algorithm implementation.

    Args:
        concept: Concept dictionary with SM-2 parameters
        rating: Review rating ("easy", "good", "hard", "wrong")
        config: Optional configuration dictionary (loaded if not provided)
    
    Returns:
        Updated concept dictionary with new review schedule
    
    Raises:
        ValueError: If rating is not valid
    """
    if rating not in ("easy", "good", "hard", "wrong"):
        raise ValueError(f"Invalid rating: {rating}. Must be 'easy', 'good', 'hard', or 'wrong'")
    
    c = concept.copy()
    # reviews==1 means this is the 2nd review (0-indexed), check before incrementing
    is_second_review = (c["reviews"] == 1)

    c["reviews"] += 1
    c["total_count"] += 1

    # Load config only once if not provided
    if config is None:
        config = load_config()
    mastery_threshold = config.get("mastery_threshold", 0.8)

    if rating == "wrong":
        # Reset interval
        c["interval_days"] = 1
        c["ease_factor"] = max(1.3, c["ease_factor"] - 0.2)
    elif rating == "hard":
        c["interval_days"] = max(1, int(c["interval_days"] * 1.2))
        c["ease_factor"] = max(1.3, c["ease_factor"] - 0.15)
        c["correct_count"] += 1
    elif rating == "good":
        # SM-2 fix: second review should be 6 days (original SM-2 algorithm)
        if is_second_review:
            c["interval_days"] = 6
        else:
            c["interval_days"] = max(1, int(c["interval_days"] * c["ease_factor"]))
        # ease_factor unchanged
        c["correct_count"] += 1
    elif rating == "easy":
        # SM-2 fix: second review should be 6 days (original SM-2 algorithm)
        if is_second_review:
            c["interval_days"] = 6
        else:
            c["interval_days"] = max(1, int(c["interval_days"] * (c["ease_factor"] + 0.15)))
        c["ease_factor"] = c["ease_factor"] + 0.15
        c["correct_count"] += 1

    # Update mastery based on recent accuracy
    if c["total_count"] >= 1 and c["mastery"] == "unseen":
        c["mastery"] = "learning"
    if c["total_count"] >= 3:
        accuracy = c["correct_count"] / c["total_count"]
        if accuracy >= mastery_threshold and c["reviews"] >= 3:
            c["mastery"] = "mastered"
        elif accuracy >= 0.6:
            c["mastery"] = "reviewing"
        else:
            c["mastery"] = "learning"

    # Calculate next review date
    next_date = datetime.now() + timedelta(days=c["interval_days"])
    c["next_review"] = next_date.strftime("%Y-%m-%d")

    return c


def get_accuracy_str(concept: dict[str, Any]) -> str:
    """
    Get accuracy string for display.
    
    Args:
        concept: Concept dictionary
    
    Returns:
        Accuracy percentage string or "N/A"
    """
    if concept["total_count"] == 0:
        return "N/A"
    acc = concept["correct_count"] / concept["total_count"]
    return f"{acc:.0%}"


def calc_overdue(next_review: str | None) -> int:
    """
    Calculate overdue days from next_review date string.
    
    Args:
        next_review: Date string in YYYY-MM-DD format, or None
    
    Returns:
        Number of overdue days (0 if not overdue or invalid date)
    """
    if not next_review:
        return 0
    try:
        review_date = datetime.strptime(next_review, "%Y-%m-%d")
        return max(0, (datetime.now() - review_date).days)
    except ValueError:
        return 0


def get_mastery_emoji(mastery: str) -> str:
    """
    Get mastery status emoji for display.
    
    Args:
        mastery: Mastery status string
    
    Returns:
        Mastery status emoji string
    """
    return {"mastered": "[MASTERED]", "reviewing": "[REVIEWING]", "learning": "[LEARNING]", "unseen": "[UNSEEN]"}.get(mastery, "[UNSEEN]")


def calc_level(concepts: dict[str, Any], topic: str | None = None) -> tuple[str, str, str]:
    """
    Calculate skill level.

    If topic is provided, uses test_history for authoritative level.
    Otherwise, falls back to mastery-based overview (for display only).
    
    Args:
        concepts: Dictionary of concepts
        topic: Optional topic name for authoritative level calculation
    
    Returns:
        Tuple of (level_code, level_name, level_emoji)
    """
    if topic:
        return calc_level_by_accuracy(topic, concepts_fallback=concepts)

    # Fallback: mastery-based overview (for display only, not authoritative)
    _, _, pct = calc_mastery_overview(concepts)
    if pct >= 0.9:
        return "L5", "精通 (Mastery)", "[L5]"
    elif pct >= 0.7:
        return "L4", "熟练 (Proficient)", "[L4]"
    elif pct >= 0.4:
        return "L3", "进阶 (Intermediate)", "[L3]"
    elif pct >= 0.2:
        return "L2", "初学 (Beginner)", "[L2]"
    else:
        return "L1", "入门 (Novice)", "[L1]"


# === Commands ===

def cmd_init(topic: str) -> None:
    """
    Initialize a new topic.
    
    Args:
        topic: Topic name to initialize
    """
    try:
        topic = sanitize_topic(topic)
    except SanitizeError as e:
        print(f"Error: {e}")
        return
    ensure_dirs()
    topic_dir = TOPICS_DIR / topic
    if topic_dir.exists():
        print(f"Topic '{topic}' already exists.")
        return
    topic_dir.mkdir(parents=True)
    save_concepts(topic, {})
    # Create notes.md
    (topic_dir / "notes.md").write_text(f"# {topic}\n\n## Notes\n\n")
    # Create progress.md
    (topic_dir / "progress.md").write_text(f"# {topic} - Progress\n\n## Started: {today()}\n\n")
    print(f"[OK] Topic '{topic}' created at {topic_dir}")


def cmd_add(topic: str, concept_name: str) -> None:
    """
    Add a concept to a topic.
    
    Args:
        topic: Topic name
        concept_name: Concept name to add
    """
    try:
        topic = sanitize_topic(topic)
        concept_name = sanitize_concept(concept_name)
    except SanitizeError as e:
        print(f"Error: {e}")
        return
    concepts = load_concepts(topic)
    if concept_name in concepts:
        print(f"Concept '{concept_name}' already exists in '{topic}'.")
        return
    concepts[concept_name] = DEFAULT_CONCEPT.copy()
    concepts[concept_name]["added"] = today()
    concepts[concept_name]["next_review"] = today()  # Due immediately for first review
    save_concepts(topic, concepts)
    print(f"[OK] Added '{concept_name}' to '{topic}'. First review due today.")


def cmd_rate(topic: str, concept_name: str, rating: str) -> None:
    """
    Non-interactively rate a concept and update its SM-2 state.

    This is the safe way for AI assistants to update concept review status
    without needing to call the interactive cmd_review.

    Args:
        topic: Topic name
        concept_name: Concept name to rate
        rating: Review rating ("easy", "good", "hard", "wrong")
    """
    try:
        topic = sanitize_topic(topic)
        concept_name = sanitize_concept(concept_name)
    except SanitizeError as e:
        print(f"Error: {e}")
        return
    if rating not in ("easy", "good", "hard", "wrong"):
        print(f"Error: Invalid rating '{rating}'. Must be 'easy', 'good', 'hard', or 'wrong'")
        return
    concepts = load_concepts(topic)
    if not concepts:
        print(f"Error: Topic '{topic}' does not exist or has no concepts")
        return
    if concept_name not in concepts:
        print(f"Error: Concept '{concept_name}' not found in topic '{topic}'")
        return
    c = concepts[concept_name]
    updated = calc_next_review(c, rating)
    concepts[concept_name] = updated
    save_concepts(topic, concepts)
    # Log the rating action
    append_learning_log("rate", topic, {
        "concept": concept_name,
        "rating": rating
    })
    print(f"[OK] Rated '{concept_name}' as '{rating}'. Next review: {updated['next_review']}")


def cmd_review(topic: str) -> None:
    """
    Start a review session for a topic.
    
    Args:
        topic: Topic name to review
    """
    try:
        topic = sanitize_topic(topic)
    except SanitizeError as e:
        print(f"Error: {e}")
        return
    concepts = load_concepts(topic)
    if not concepts:
        print(f"No concepts in '{topic}'. Add some first: srs.py add {topic} <concept>")
        return

    config = load_config()
    limit = config.get("daily_review_limit", 20)
    burnout_threshold = config.get("burnout_threshold", 3)

    # Find due concepts
    today_str = today()
    due = []
    for name, c in concepts.items():
        if c["next_review"] and c["next_review"] <= today_str:
            due.append((name, c))

    if not due:
        print(f"[OK] No reviews due today for '{topic}'.")
        next_dates = []
        for name, c in concepts.items():
            if c["next_review"]:
                next_dates.append((c["next_review"], name))
        if next_dates:
            next_dates.sort()
            print(f"   Next review: {next_dates[0][0]} ({next_dates[0][1]})")
        return

    due = due[:limit]
    print(f"\n[REVIEW] Review Session: {topic}")
    print(f"   Due today: {len(due)} concept(s)")
    print(f"   Rate each: easy / good / hard / wrong")
    print(f"   Type 'quit' to stop early\n")

    consecutive_wrong = 0
    reviewed = 0

    for name, c in due:
        # Burnout check
        if consecutive_wrong >= burnout_threshold:
            print(f"\n[WARNING] Burnout detected ({consecutive_wrong} consecutive wrong).")
            print(f"   Consider taking a break or switching to easier material.")
            resp = input("   Continue anyway? (y/n): ").strip().lower()
            if resp != "y":
                break
            consecutive_wrong = 0

        mastery = get_mastery_emoji(c["mastery"])
        accuracy = get_accuracy_str(c)
        print(f"\n{'='*50}")
        print(f"  {mastery} {name}")
        print(f"  Reviews: {c['reviews']} | Accuracy: {accuracy} | Interval: {c['interval_days']}d")
        print(f"{'='*50}")

        # In a real session, the AI would ask questions here.
        # For the CLI, we just do the rating.
        print(f"  (In interactive mode, AI助手 would quiz you on this concept)")

        while True:
            rating = input(f"  Rate [easy/good/hard/wrong]: ").strip().lower()
            if rating in ("easy", "good", "hard", "wrong", "quit"):
                break
            print(f"  Invalid. Use: easy, good, hard, wrong, or quit")

        if rating == "quit":
            print("\nSession ended early.")
            break

        # Update concept
        concepts[name] = calc_next_review(c, rating)
        reviewed += 1

        if rating == "wrong":
            consecutive_wrong += 1
        else:
            consecutive_wrong = 0

    save_concepts(topic, concepts)
    print(f"\n[OK] Reviewed {reviewed} concept(s). Progress saved.")


def cmd_due() -> None:
    """Show all due reviews for today."""
    ensure_dirs()
    today_str = today()
    all_due = []

    for topic_dir in TOPICS_DIR.iterdir():
        if not topic_dir.is_dir():
            continue
        # Filter out test/debug/temp directories
        if topic_dir.name.startswith(("test-", "debug-", "temp-")):
            continue
        concepts = load_concepts(topic_dir.name)
        for name, c in concepts.items():
            if c["next_review"] and c["next_review"] <= today_str:
                all_due.append((topic_dir.name, name, c))

    if not all_due:
        print("[OK] No reviews due today!")
        return

    # Sort by next_review (oldest first)
    all_due.sort(key=lambda x: x[2]["next_review"])

    config = load_config()
    limit = config.get("daily_review_limit", 20)
    all_due = all_due[:limit]

    print(f"\n[DUE] Due Reviews ({len(all_due)} total):\n")
    current_topic = None
    for topic, name, c in all_due:
        if topic != current_topic:
            print(f"  [DIR] {topic}")
            current_topic = topic
        mastery = get_mastery_emoji(c["mastery"])
        accuracy = get_accuracy_str(c)
        overdue = calc_overdue(c["next_review"])
        overdue_str = f" ({overdue}d overdue)" if overdue > 0 else ""
        print(f"     {mastery} {name} [acc: {accuracy}, int: {c['interval_days']}d]{overdue_str}")


def cmd_status(topic: str | None = None) -> None:
    """
    Show learning status.
    
    Args:
        topic: Optional topic name to show specific status
    """
    ensure_dirs()

    if topic:
        try:
            topic = sanitize_topic(topic)
        except SanitizeError as e:
            print(f"Error: {e}")
            return
        concepts = load_concepts(topic)
        if not concepts:
            print(f"No concepts in '{topic}'.")
            return

        # Use authoritative level from test_history if available
        level_code, level_name, level_emoji = calc_level(concepts, topic=topic)
        mastered = sum(1 for c in concepts.values() if c["mastery"] == "mastered")
        reviewing = sum(1 for c in concepts.values() if c["mastery"] == "reviewing")
        learning = sum(1 for c in concepts.values() if c["mastery"] == "learning")
        unseen = sum(1 for c in concepts.values() if c["mastery"] == "unseen")
        total = len(concepts)

        print(f"\n[STATUS] {topic} Status:\n")
        print(f"  等级:{level_emoji} {level_code} {level_name}")
        print()
        print(f"  [MASTERED] Mastered:  {mastered}/{total}")
        print(f"  [REVIEWING] Reviewing: {reviewing}/{total}")
        print(f"  [LEARNING] Learning:  {learning}/{total}")
        print(f"  [UNSEEN] Unseen:    {unseen}/{total}")

        print(f"\n  Concepts:")
        for name, c in concepts.items():
            mastery = get_mastery_emoji(c["mastery"])
            accuracy = get_accuracy_str(c)
            print(f"    {mastery} {name:30s} | acc: {accuracy:4s} | int: {c['interval_days']:3d}d | next: {c['next_review']}")
        return

    # Overall status
    print(f"\n[STATUS] Overall Learning Status:\n")

    total_concepts = 0
    total_mastered = 0
    total_due = 0
    today_str = today()

    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        concepts = load_concepts(topic_dir.name)
        if not concepts:
            continue

        mastered = sum(1 for c in concepts.values() if c["mastery"] == "mastered")
        due = sum(1 for c in concepts.values() if c["next_review"] and c["next_review"] <= today_str)
        total = len(concepts)

        total_concepts += total
        total_mastered += mastered
        total_due += due

        status = "[OK]" if mastered == total else "[PROGRESS]"
        print(f"  {status} {topic_dir.name:20s} | {mastered}/{total} mastered | {due} due today")

    if total_concepts > 0:
        pct = total_mastered / total_concepts * 100
        print(f"\n  Total: {total_mastered}/{total_concepts} mastered ({pct:.0f}%)")
        print(f"  Due today: {total_due}")


def cmd_config(key: str | None = None, value: str | None = None) -> None:
    """
    Show or set configuration.
    
    Args:
        key: Configuration key to show or set
        value: Value to set (if key is provided)
    """
    config = load_config()

    if key is None:
        print(f"\n[CONFIG] Config ({CONFIG_FILE}):\n")
        for k, v in config.items():
            print(f"  {k}: {v}")
        return

    if value is None:
        if key in config:
            print(f"  {key}: {config[key]}")
        else:
            print(f"  Key '{key}' not found.")
        return

    # Set value
    if key not in DEFAULT_CONFIG:
        print(f"  Unknown key: {key}")
        print(f"  Valid keys: {', '.join(DEFAULT_CONFIG.keys())}")
        return

    # Type coercion
    default_val = DEFAULT_CONFIG[key]
    converted_value = value
    if isinstance(default_val, int):
        try:
            converted_value = int(value)
        except ValueError:
            print(f"  Error: {key} must be an integer")
            return
    elif isinstance(default_val, float):
        try:
            converted_value = float(value)
        except ValueError:
            print(f"  Error: {key} must be a number")
            return

    config[key] = converted_value
    save_config(config)
    print(f"  [OK] {key} = {converted_value}")


def _cron_exists(name: str) -> bool:
    """
    Check if a cron job with the given name exists.

    Args:
        name: Cron job name to check

    Returns:
        True if the cron job exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False
        data = json.loads(result.stdout)
        # openclaw cron list --json returns {"jobs": [...], ...}
        jobs = data.get("jobs", []) if isinstance(data, dict) else data
        return any(j.get("name") == name for j in jobs)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return False


def _get_user_channel() -> str | None:
    """
    Detect the user's current channel from OpenClaw sessions.

    Returns:
        Channel provider name (e.g., "telegram", "qqbot"), or None if not detected
    """
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        # openclaw sessions --json returns {"sessions": [...], ...}
        sessions = data.get("sessions", []) if isinstance(data, dict) else data
        for session in sessions:
            if not isinstance(session, dict):
                continue
            if session.get("type") == "main":
                origin = session.get("origin", {})
                return origin.get("provider")
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def _delete_cron(name: str) -> bool:
    """Delete a cron job by name. Returns True if deleted."""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "delete", "--name", name],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _recreate_crons_with_channel(channel: str) -> None:
    """Delete existing crons and recreate them with the given channel."""
    config = load_config()
    contract = config.get("learning_contract", {})
    reminder_time = contract.get("time", "09:00")
    hour = reminder_time.split(":")[0]

    # Delete existing crons
    _delete_cron("retaincraft-reminder")
    _delete_cron("retaincraft-weekly-report")

    # Recreate daily reminder
    cron_args = [
        "openclaw", "cron", "add",
        "--name", "retaincraft-reminder",
        "--cron", f"0 {hour} * * *",
        "--tz", "Asia/Shanghai",
        "--session", "isolated",
        "--channel", channel,
        "--message", f"执行: python3 {SCRIPTS_DIR / 'srs.py'} reminder",
        "--announce"
    ]
    try:
        subprocess.run(cron_args, capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Recreate weekly report
    cron_args = [
        "openclaw", "cron", "add",
        "--name", "retaincraft-weekly-report",
        "--cron", "0 20 * * 0",
        "--tz", "Asia/Shanghai",
        "--session", "isolated",
        "--channel", channel,
        "--message", f"执行: python3 {SCRIPTS_DIR / 'srs.py'} weekly-report",
        "--announce"
    ]
    try:
        subprocess.run(cron_args, capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def cmd_setup_reminder() -> None:
    """Setup learning reminder and weekly report cron jobs."""
    config = load_config()
    contract = config.get("learning_contract", {})
    reminder_time = contract.get("time", "09:00")

    # Validate time format (HH:MM)
    import re as _re
    if not _re.match(r'^\d{2}:\d{2}$', reminder_time):
        print(f"[WARN] Invalid reminder time format: '{reminder_time}'. Expected HH:MM (e.g., '09:00').")
        print("       Using default: 09:00")
        reminder_time = "09:00"

    hour = reminder_time.split(":")[0]

    # Detect user channel
    user_channel = _get_user_channel()

    # Setup daily reminder
    if _cron_exists("retaincraft-reminder"):
        print("[OK] Learning reminder cron already exists.")
    else:
        cron_args = [
            "openclaw", "cron", "add",
            "--name", "retaincraft-reminder",
            "--cron", f"0 {hour} * * *",
            "--tz", "Asia/Shanghai",
            "--session", "isolated",
            "--message", f"执行: python3 {SCRIPTS_DIR / 'srs.py'} reminder",
            "--announce"
        ]
        if user_channel:
            cron_args.extend(["--channel", user_channel])

        try:
            result = subprocess.run(cron_args, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"[OK] Learning reminder cron created (daily at {reminder_time}).")
                if user_channel:
                    print(f"     Channel: {user_channel}")
            else:
                print(f"[WARN] Failed to create reminder cron: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[WARN] Failed to create reminder cron: {e}")

    # Setup weekly report
    if _cron_exists("retaincraft-weekly-report"):
        print("[OK] Weekly report cron already exists.")
    else:
        cron_args = [
            "openclaw", "cron", "add",
            "--name", "retaincraft-weekly-report",
            "--cron", "0 20 * * 0",
            "--tz", "Asia/Shanghai",
            "--session", "isolated",
            "--message", f"执行: python3 {SCRIPTS_DIR / 'srs.py'} weekly-report",
            "--announce"
        ]
        if user_channel:
            cron_args.extend(["--channel", user_channel])

        try:
            result = subprocess.run(cron_args, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("[OK] Weekly report cron created (Sunday at 20:00).")
            else:
                print(f"[WARN] Failed to create weekly report cron: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[WARN] Failed to create weekly report cron: {e}")


def cmd_check_reminder() -> None:
    """Check the status of learning reminders."""
    print("\n[CHECK-REMINDER] Reminder Status:\n")

    # Check daily reminder
    if _cron_exists("retaincraft-reminder"):
        config = load_config()
        contract = config.get("learning_contract", {})
        reminder_time = contract.get("time", "09:00")
        channel = _get_user_channel() or "auto-detect"
        print(f"  ✅ Learning reminder: ENABLED")
        print(f"     Time: {reminder_time}")
        print(f"     Channel: {channel}")
    else:
        print(f"  ⚠️  Learning reminder: NOT ENABLED")
        print(f"     Run 'srs.py setup-reminder' to enable")

    # Check weekly report
    if _cron_exists("retaincraft-weekly-report"):
        print(f"  ✅ Weekly report: ENABLED")
        print(f"     Schedule: Sunday at 20:00")
    else:
        print(f"  ⚠️  Weekly report: NOT ENABLED")
        print(f"     Run 'srs.py setup-reminder' to enable")


def cmd_switch_channel() -> None:
    """List available notification channels and switch the active one."""
    current = _get_user_channel()
    print(f"\n[SWITCH-CHANNEL] Current channel: {current or 'not detected'}\n")

    # List available channels from config
    config = load_config()
    channels = config.get("reminder_channels", [])

    if not channels:
        print("  No channels configured. Add channels to config.json:")
        print('  "reminder_channels": [')
        print('    {"type": "telegram", "target": "-1001234567890"},')
        print('    {"type": "qqbot", "target": "group123"}')
        print('  ]')
        return

    print("  Available channels:")
    for i, ch in enumerate(channels, 1):
        marker = " (current)" if ch["type"] == current else ""
        print(f"    {i}. {ch['type']} - {ch['target']}{marker}")

    # Prompt user to select a channel
    print()
    try:
        choice = input("  Enter channel number to switch (or press Enter to cancel): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return

    if not choice:
        print("  Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(channels):
            print(f"  Invalid choice: {choice}. Must be 1-{len(channels)}.")
            return
    except ValueError:
        print(f"  Invalid input: {choice}. Must be a number.")
        return

    selected = channels[idx]
    config["active_channel"] = selected["type"]
    save_config(config)

    # Recreate cron jobs with the new channel
    print(f"\n  Switching to: {selected['type']} - {selected['target']}")
    _recreate_crons_with_channel(selected["type"])
    print(f"  [OK] Channel switched to {selected['type']}.")


def cmd_reminder() -> None:
    """Generate today's learning plan with forgetting risk analysis."""
    ensure_dirs()
    config = load_config()
    contract = config.get("learning_contract", {})

    # Calculate forgetting risk
    last_time = get_last_learning_time()
    now = datetime.now()
    days_since = (now - last_time).days if last_time else 999

    # Forgetting risk based on Ebbinghaus (1885), validated by Murre & Dros (2015)
    if days_since >= 7:
        risk = "critical"
        risk_msg = f"你已经 {days_since} 天没学习了。知识基本回到起点，建议从最简单的概念重新开始。"
    elif days_since >= 2:
        risk = "high"
        forgetting_rates = {2: 72, 3: 73, 4: 74, 5: 74, 6: 75}
        forgetting_pct = forgetting_rates.get(days_since, 75)
        risk_msg = f"你已经 {days_since} 天没学习了。遗忘率已达约{forgetting_pct}%，建议今天只复习，不学新内容。"
    elif days_since == 1:
        risk = "low"
        risk_msg = "昨天没学习，今天复习一下。24 小时是遗忘拐点。"
    else:
        risk = "none"
        risk_msg = ""

    # Get due concepts across all topics
    today_str = today()
    topics_due = []
    for topic_dir in sorted(TOPICS_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        concepts = load_concepts(topic_dir.name)
        if not concepts:
            continue

        due_concepts = []
        for name, c in concepts.items():
            if c["next_review"] and c["next_review"] <= today_str:
                overdue = calc_overdue(c["next_review"])
                due_concepts.append({
                    "name": name,
                    "status": c["mastery"],
                    "overdue_days": overdue
                })

        if due_concepts:
            # Sort by overdue days (descending)
            due_concepts.sort(key=lambda x: -x["overdue_days"])
            topics_due.append({
                "name": topic_dir.name,
                "concepts": due_concepts,
                "count": len(due_concepts)
            })

    # Build output
    output = {
        "date": today_str,
        "risk": risk,
        "risk_msg": risk_msg,
        "days_since_learning": days_since,
        "topics": topics_due,
        "total_due": sum(t["count"] for t in topics_due)
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_weekly_report() -> None:
    """Generate weekly learning report data."""
    log = load_learning_log()
    now = datetime.now()

    # Filter logs for the past 7 days
    week_ago = now - timedelta(days=7)
    week_log = [
        entry for entry in log
        if datetime.fromisoformat(entry["timestamp"]) >= week_ago
    ]

    # Calculate statistics
    learning_days = len(set(
        entry["timestamp"][:10] for entry in week_log
    ))

    rate_actions = [e for e in week_log if e["action"] == "rate"]
    test_actions = [e for e in week_log if e["action"] == "record-test"]

    topics_covered = list(set(entry["topic"] for entry in week_log))

    # Calculate average accuracy from tests
    avg_accuracy = 0
    if test_actions:
        accuracies = [e.get("accuracy", 0) for e in test_actions]
        avg_accuracy = sum(accuracies) / len(accuracies)

    # Detect level changes
    level_changes = {}
    for topic in topics_covered:
        level_code, level_name, level_emoji = calc_level_by_accuracy(topic)
        level_changes[topic] = f"{level_code} {level_name}"

    # Check burnout status
    burnout_status = {}
    for topic in topics_covered:
        try:
            burnout = check_burnout(topic)
            burnout_status[topic] = burnout.get("risk", "unknown")
        except Exception:
            burnout_status[topic] = "unknown"

    # Build report
    report = {
        "period": {
            "start": week_ago.strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d")
        },
        "learning_days": learning_days,
        "total_actions": len(week_log),
        "rate_actions": len(rate_actions),
        "test_actions": len(test_actions),
        "topics_covered": topics_covered,
        "avg_accuracy": avg_accuracy,
        "level_changes": level_changes,
        "burnout_status": burnout_status
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    """Main entry point for the CLI."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "init":
        if len(args) < 2:
            print("Usage: srs.py init <topic>")
            return
        cmd_init(args[1])

    elif cmd == "add":
        if len(args) < 3:
            print("Usage: srs.py add <topic> <concept>")
            return
        cmd_add(args[1], args[2])

    elif cmd == "review":
        if len(args) < 2:
            print("Usage: srs.py review <topic>")
            return
        cmd_review(args[1])

    elif cmd == "rate":
        if len(args) < 4:
            print("Usage: srs.py rate <topic> <concept> <rating>")
            return
        cmd_rate(args[1], args[2], args[3])

    elif cmd == "due":
        cmd_due()

    elif cmd == "status":
        topic = args[1] if len(args) > 1 else None
        cmd_status(topic)

    elif cmd == "record-test":
        if len(args) < 4:
            print("Usage: srs.py record-test <topic> <total> <correct>")
            return
        try:
            total = int(args[2])
            correct = int(args[3])
        except ValueError:
            print("Error: total and correct must be integers")
            return
        try:
            result = record_test(args[1], total, correct)
            print(f"[OK] Recorded test for '{args[1]}': {correct}/{total} ({result['accuracy']:.0%})")
            level_code, level_name, level_emoji = calc_level_by_accuracy(args[1])
            print(f"   Level: {level_emoji} {level_code} {level_name}")
        except ValueError as e:
            print(f"[ERROR] Input error: {e}")
            return

    elif cmd == "test-history":
        topic = args[1] if len(args) > 1 else None
        history = load_test_history()
        if topic:
            tests = history.get(topic, [])
            if not tests:
                print(f"No test history for '{topic}'.")
                return
            print(f"\n[HISTORY] Test History: {topic}\n")
            for i, t in enumerate(tests, 1):
                print(f"  {i}. {t['timestamp'][:16]} | {t['correct']}/{t['total']} ({t['accuracy']:.0%})")
            level_code, level_name, level_emoji = calc_level_by_accuracy(topic)
            print(f"\n  Level: {level_emoji} {level_code} {level_name}")
        else:
            if not history:
                print("No test history.")
                return
            print(f"\n[HISTORY] Test History:\n")
            for topic, tests in history.items():
                level_code, level_name, level_emoji = calc_level_by_accuracy(topic)
                print(f"  [DIR] {topic}: {len(tests)} tests | {level_emoji} {level_code} {level_name}")

    elif cmd == "record-simulation":
        if len(args) < 4:
            print("Usage: srs.py record-simulation <topic> <scenario> <score> [--rounds N]")
            return
        try:
            score = int(args[3])
        except ValueError:
            print("Error: score must be an integer")
            return
        rounds = 3
        if "--rounds" in args:
            rounds_idx = args.index("--rounds")
            if rounds_idx + 1 < len(args):
                try:
                    rounds = int(args[rounds_idx + 1])
                except ValueError:
                    print("Error: rounds must be an integer")
                    return
        result = record_simulation(args[1], args[2], score, rounds)
        print(f"[OK] Recorded simulation for '{args[1]}': {args[2]} | Score: {score}/100 | Rounds: {rounds}")

    elif cmd == "simulation-history":
        topic = args[1] if len(args) > 1 else None
        history = load_simulation_history()
        if topic:
            simulations = history.get(topic, [])
            if not simulations:
                print(f"No simulation history for '{topic}'.")
                return
            print(f"\n[HISTORY] Simulation History: {topic}\n")
            for i, s in enumerate(simulations, 1):
                print(f"  {i}. {s['timestamp'][:16]} | {s['scenario']} | Score: {s['score']}/100 | Rounds: {s['rounds']}")
        else:
            if not history:
                print("No simulation history.")
                return
            print(f"\n[HISTORY] Simulation History:\n")
            for topic, simulations in history.items():
                print(f"  [DIR] {topic}: {len(simulations)} simulations")

    elif cmd == "profile":
        if len(args) > 1 and args[1] == "--update":
            # Update profile for all topics
            ensure_dirs()
            topics = [d.name for d in TOPICS_DIR.iterdir() if d.is_dir()]
            if not topics:
                print("No topics found.")
                return
            for topic in topics:
                update_profile(topic)
            print(f"[OK] Profile updated for {len(topics)} topic(s).")
        elif len(args) > 1 and args[1] == "--compare":
            if len(args) < 3:
                print("Usage: srs.py profile --compare <job_title>")
                return
            result = compare_profile_with_job(args[2])
            print(f"\n[PROFILE] Profile Comparison: {args[2]}\n")
            print(f"  当前最高等级: {result['current_level']}")
            print(f"  总学习时长: {result['total_hours']:.1f} 小时")
            if result.get('mastered_skills'):
                skills = ', '.join(result['mastered_skills'][:5])
                print(f"  掌握技能: {skills}")
            if result.get('weaknesses'):
                weaknesses = ', '.join(result['weaknesses'][:5])
                print(f"  薄弱环节: {weaknesses}")
            print(f"  [TIP] {result['suggestion']}")
        else:
            profile = load_profile()
            print(f"\n[PROFILE] User Profile:\n")
            print(f"  Goal: {profile['goal'] or 'Not set'}")
            print(f"  Started: {profile['started']}")
            print(f"  Total Hours: {profile['total_hours']:.1f}")
            print(f"  Last Updated: {profile['last_updated'][:16]}")
            if profile['topics']:
                print(f"\n  Topics:")
                for topic, data in profile['topics'].items():
                    status = "[OK]" if data['status'] == 'completed' else "[PROGRESS]"
                    print(f"    {status} {topic}: {data['level']} | {data['concepts_mastered']}/{data['concepts_total']} mastered | {data['test_avg']:.0f}% avg")
            if profile['strengths']:
                print(f"\n  Strengths: {', '.join(profile['strengths'][:5])}")
            if profile['weaknesses']:
                print(f"  Weaknesses: {', '.join(profile['weaknesses'][:5])}")

    elif cmd == "check-session":
        topic = args[1] if len(args) > 1 else None
        result = check_session(topic)
        if result["status"] == "no_history":
            print(f"[INFO] {result['message']}")
        else:
            threshold = result["stale_minutes_threshold"]
            print(f"\n[CHECK-SESSION] Session Integrity Check (stale > {threshold} min)\n")
            for f in result["findings"]:
                status_icon = "[STALE]" if f["stale"] else "[OK]"
                acc = f["last_accuracy"]
                gap = f["gap_minutes"]
                print(f"  {status_icon} {f['topic']:20s} | last: {f['last_record'][:16]} | acc: {acc:.0%} | {gap:.0f} min ago")
            if result["stale_count"] > 0:
                print(f"\n  [WARNING] {result['stale_count']} topic(s) have stale records.")
                print("  If a module test was conducted without record-test, the level will not update.")
            else:
                print(f"\n  [OK] All records are fresh (within {threshold} minutes).")

    elif cmd == "check-burnout":
        if len(args) < 2:
            print("Usage: srs.py check-burnout <topic> [--window N]")
            return
        topic = args[1]
        window = 5
        if "--window" in args:
            idx = args.index("--window")
            if idx + 1 < len(args):
                try:
                    window = int(args[idx + 1])
                except ValueError:
                    print("Error: window must be an integer")
                    return
        try:
            result = check_burnout(topic, window)
        except SanitizeError as e:
            print(f"Error: {e}")
            return
        if result["status"] == "no_data":
            print(f"[INFO] {result['message']}")
        else:
            risk_map = {"low": "[LOW]", "medium": "[MEDIUM]", "high": "[HIGH]"}
            print(f"\n[CHECK-BURNOUT] Burnout Risk Analysis: {topic}\n")
            print(f"  Risk Level:   {risk_map.get(result['risk'], result['risk'])}")
            print(f"  Trend:        {result['trend']}")
            print(f"  Avg Accuracy: {result['avg_accuracy']:.0%} (last {result['recent_tests']} tests)")
            print(f"  Consecutive below 50%: {result['consecutive_below_50']}")
            if result["suggestions"]:
                print(f"\n  Suggestions:")
                for s in result["suggestions"]:
                    print(f"    - {s}")

    elif cmd == "config":
        key = args[1] if len(args) > 1 else None
        value = args[2] if len(args) > 2 else None
        if key == "set" and len(args) >= 4:
            cmd_config(args[2], args[3])
        else:
            cmd_config(key, value)

    elif cmd == "setup-reminder":
        cmd_setup_reminder()

    elif cmd == "reminder":
        cmd_reminder()

    elif cmd == "weekly-report":
        cmd_weekly_report()

    elif cmd == "check-reminder":
        cmd_check_reminder()

    elif cmd == "switch-channel":
        cmd_switch_channel()

    else:
        print(f"Unknown command: {cmd}")
        print("Run 'srs.py help' for usage.")


if __name__ == "__main__":
    main()
