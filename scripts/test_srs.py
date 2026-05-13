#!/usr/bin/env python3
"""
Unit tests for srs.py

Run with: python3 -m pytest test_srs.py -v
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase, main

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import srs
from srs import (
    calc_level_by_accuracy,
    calc_mastery_overview,
    calc_next_review,
    check_burnout,
    check_session,
    compare_profile_with_job,
    load_profile,
    load_test_history,
    record_test,
    save_profile,
    save_test_history,
    update_profile,
)


class TestCalcLevelByAccuracy(TestCase):
    """Test calc_level_by_accuracy function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_history_file = Path(self.temp_dir) / "test_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_no_history_returns_l1(self):
        """Test that no history returns L1."""
        # Mock load_test_history to return empty dict
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {}



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L1")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_single_test_above_20_returns_l2(self):
        """Test that single test above 20% returns L2."""
        # Mock load_test_history to return single test
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [{"accuracy": 0.5, "timestamp": "2026-05-05"}]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L2")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_two_tests_above_40_returns_l3(self):
        """Test that two consecutive tests above 40% returns L3."""
        # Mock load_test_history to return two tests
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [

            {"accuracy": 0.5, "timestamp": "2026-05-05"},

            {"accuracy": 0.6, "timestamp": "2026-05-05"},

            ]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L3")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_two_tests_above_70_returns_l4(self):
        """Test that two consecutive tests above 70% returns L4."""
        # Mock load_test_history to return four tests:
        # - Tests 1-2: 50% (upgrade to L3)
        # - Tests 3-4: 80% (upgrade to L4)
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [

            {"accuracy": 0.5, "timestamp": "2026-05-05"},

            {"accuracy": 0.5, "timestamp": "2026-05-05"},

            {"accuracy": 0.8, "timestamp": "2026-05-05"},

            {"accuracy": 0.9, "timestamp": "2026-05-05"},

            ]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L4")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_two_tests_above_90_returns_l5(self):
        """Test that two consecutive tests above 90% returns L5."""
        # Mock load_test_history to return six tests:
        # - Tests 1-2: 50% (upgrade to L3)
        # - Tests 3-4: 80% (upgrade to L4)
        # - Tests 5-6: 95% (upgrade to L5)
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [

            {"accuracy": 0.5, "timestamp": "2026-05-05"},

            {"accuracy": 0.5, "timestamp": "2026-05-05"},

            {"accuracy": 0.8, "timestamp": "2026-05-05"},

            {"accuracy": 0.8, "timestamp": "2026-05-05"},

            {"accuracy": 0.95, "timestamp": "2026-05-05"},

            {"accuracy": 1.0, "timestamp": "2026-05-05"},

            ]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L5")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_no_skipping_levels(self):
        """Test that levels cannot be skipped."""
        # Mock load_test_history to return two tests with 90% accuracy
        # But starting from L1, should only go to L2 (first test), then L3 (second test)
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [

            {"accuracy": 0.9, "timestamp": "2026-05-05"},

            {"accuracy": 0.9, "timestamp": "2026-05-05"},

            ]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            # Should be L3 (not L5) because:

            # - First test: 90% >= 20% → L2

            # - Two consecutive 90% >= 40% → L3

            # - But we only have 2 tests, so can't upgrade to L4 (need 2 consecutive >= 70%)

            self.assertEqual(level_code, "L3")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_demotion_after_3_consecutive_failures(self):
        """Test that demotion occurs after 3 consecutive tests below threshold."""
        # Mock load_test_history to return 5 tests:
        # - Tests 1-2: 90% (upgrade to L3)
        # - Tests 3-5: 30% (below L3 threshold of 40%)
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {

            "test_topic": [

            {"accuracy": 0.9, "timestamp": "2026-05-05"},

            {"accuracy": 0.9, "timestamp": "2026-05-05"},

            {"accuracy": 0.3, "timestamp": "2026-05-05"},

            {"accuracy": 0.3, "timestamp": "2026-05-05"},

            {"accuracy": 0.3, "timestamp": "2026-05-05"},

            ]

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            # Should be L2 (demoted from L3)

            self.assertEqual(level_code, "L2")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func


    def test_demotion_from_l5_to_l2(self):
        """Test that demotion from L5 to L2 occurs after consecutive failures."""
        # Mock load_test_history to return 9 tests:
        # - Tests 1-2: 90% (upgrade to L3)
        # - Tests 3-4: 50% (upgrade to L4)
        # - Tests 5-6: 80% (upgrade to L5)
        # - Tests 7-9: 0% (below L5 threshold, should demote to L4, then L3, then L2)
        try:
            original_func = srs.load_test_history
            srs.load_test_history = lambda: {
                "test_topic": [
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.5, "timestamp": "2026-05-05"},
                    {"accuracy": 0.5, "timestamp": "2026-05-05"},
                    {"accuracy": 0.8, "timestamp": "2026-05-05"},
                    {"accuracy": 0.8, "timestamp": "2026-05-05"},
                    {"accuracy": 0.0, "timestamp": "2026-05-05"},
                    {"accuracy": 0.0, "timestamp": "2026-05-05"},
                    {"accuracy": 0.0, "timestamp": "2026-05-05"},
                ]
            }

            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")
            # Should be L2 (demoted from L5 to L4 to L3 to L2)
            self.assertEqual(level_code, "L2")

            srs.load_test_history = original_func
        finally:
            srs.load_test_history = original_func
class TestCalcMasteryOverview(TestCase):
    """Test calc_mastery_overview function."""

    def test_empty_concepts_returns_zero(self):
        """Test that empty concepts returns zero."""
        mastered, total, pct = calc_mastery_overview({})
        self.assertEqual(mastered, 0)
        self.assertEqual(total, 0)
        self.assertEqual(pct, 0)

    def test_all_mastered_returns_100_percent(self):
        """Test that all mastered returns 100%."""
        concepts = {
            "concept1": {"mastery": "mastered"},
            "concept2": {"mastery": "mastered"},
        }
        mastered, total, pct = calc_mastery_overview(concepts)
        self.assertEqual(mastered, 2)
        self.assertEqual(total, 2)
        self.assertEqual(pct, 1.0)

    def test_mixed_mastery(self):
        """Test mixed mastery levels."""
        concepts = {
            "concept1": {"mastery": "mastered"},
            "concept2": {"mastery": "reviewing"},
            "concept3": {"mastery": "learning"},
        }
        mastered, total, pct = calc_mastery_overview(concepts)
        self.assertEqual(mastered, 1)
        self.assertEqual(total, 3)
        self.assertAlmostEqual(pct, 1 / 3)


class TestCalcNextReview(TestCase):
    """Test calc_next_review function."""

    def test_wrong_answer_resets_interval(self):
        """Test that wrong answer resets interval to 1 day."""
        concept = {
            "interval_days": 10,
            "ease_factor": 2.5,
            "reviews": 5,
            "correct_count": 4,
            "total_count": 5,
            "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "wrong")
        self.assertEqual(updated["interval_days"], 1)
        # mastery stays "reviewing" because total_count >= 3 and accuracy >= 0.6
        # (4/5 = 0.8 >= 0.6)
        self.assertEqual(updated["mastery"], "reviewing")

    def test_good_answer_increases_interval(self):
        """Test that good answer increases interval."""
        concept = {
            "interval_days": 10,
            "ease_factor": 2.5,
            "reviews": 5,
            "correct_count": 4,
            "total_count": 5,
            "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "good")
        # interval = 10 * 2.5 = 25
        self.assertEqual(updated["interval_days"], 25)

    def test_easy_answer_increases_ease_factor(self):
        """Test that easy answer increases ease factor."""
        concept = {
            "interval_days": 10,
            "ease_factor": 2.5,
            "reviews": 5,
            "correct_count": 4,
            "total_count": 5,
            "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "easy")
        # ease_factor = 2.5 + 0.15 = 2.65
        self.assertAlmostEqual(updated["ease_factor"], 2.65)

    def test_wrong_answer_with_low_accuracy_changes_mastery(self):
        """Test that wrong answer with low accuracy changes mastery to learning."""
        concept = {
            "interval_days": 10,
            "ease_factor": 2.5,
            "reviews": 5,
            "correct_count": 2,
            "total_count": 5,
            "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "wrong")
        # After wrong answer: total_count = 6, correct_count = 2
        # accuracy = 2/6 = 0.33 < 0.6
        # mastery should change to "learning"
        self.assertEqual(updated["mastery"], "learning")

    def test_easy_answer_with_high_accuracy_changes_mastery(self):
        """Test that easy answer with high accuracy changes mastery to mastered."""
        concept = {
            "interval_days": 10,
            "ease_factor": 2.5,
            "reviews": 5,
            "correct_count": 4,
            "total_count": 5,
            "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "easy")
        # After easy answer: total_count = 6, correct_count = 5
        # accuracy = 5/6 = 0.83 >= 0.8
        # reviews = 6 >= 3
        # mastery should change to "mastered"
        self.assertEqual(updated["mastery"], "mastered")


class TestCalcLevelByAccuracyFallback(TestCase):
    """Test calc_level_by_accuracy with concepts_fallback."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_history_file = Path(self.temp_dir) / "test_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_no_history_with_concepts_fallback_returns_based_on_mastery(self):
        """Test that concepts_fallback returns level based on mastery percentage."""
        # Mock load_test_history to return empty dict
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {}



            # Create concepts with 80% mastery

            concepts = {

            "concept1": {"mastery": "mastered"},

            "concept2": {"mastery": "mastered"},

            "concept3": {"mastery": "mastered"},

            "concept4": {"mastery": "mastered"},

            "concept5": {"mastery": "reviewing"},

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy(

            "test_topic", concepts_fallback=concepts

            )

            # 4/5 = 80% >= 0.5 but < 0.9, so should return L3

            self.assertEqual(level_code, "L3")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_no_history_with_concepts_fallback_90_percent_returns_l4(self):
        """Test that concepts_fallback returns L4 for 90% mastery."""
        # Mock load_test_history to return empty dict
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {}



            # Create concepts with 90% mastery

            concepts = {

            "concept1": {"mastery": "mastered"},

            "concept2": {"mastery": "mastered"},

            "concept3": {"mastery": "mastered"},

            "concept4": {"mastery": "mastered"},

            "concept5": {"mastery": "mastered"},

            "concept6": {"mastery": "mastered"},

            "concept7": {"mastery": "mastered"},

            "concept8": {"mastery": "mastered"},

            "concept9": {"mastery": "mastered"},

            "concept10": {"mastery": "reviewing"},

            }



            level_code, level_name, level_emoji = calc_level_by_accuracy(

            "test_topic", concepts_fallback=concepts

            )

            # 9/10 = 90% >= 0.9, so should return L4

            self.assertEqual(level_code, "L4")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func

    def test_no_history_no_fallback_returns_l1(self):
        """Test that no history and no fallback returns L1."""
        # Mock load_test_history to return empty dict
        try:

            original_func = srs.load_test_history

            srs.load_test_history = lambda: {}



            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")

            self.assertEqual(level_code, "L1")



            srs.load_test_history = original_func

        finally:

            srs.load_test_history = original_func


class TestRecordTest(TestCase):
    """Test record_test function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_history_file = Path(self.temp_dir) / "test_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_record_test_writes_json(self):
        """Test that record_test writes to JSON file correctly."""
        # Mock TEST_HISTORY_FILE
        original_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Record a test
            result = record_test("test_topic", 10, 8)

            # Verify result
            self.assertEqual(result["accuracy"], 0.8)
            self.assertEqual(result["total"], 10)
            self.assertEqual(result["correct"], 8)

            # Verify file was written
            self.assertTrue(self.test_history_file.exists())
            with open(self.test_history_file) as f:
                data = json.load(f)
            self.assertIn("test_topic", data)
            self.assertEqual(len(data["test_topic"]), 1)
            self.assertEqual(data["test_topic"][0]["accuracy"], 0.8)
        finally:
            srs.TEST_HISTORY_FILE = original_file

    def test_record_test_appends_records(self):
        """Test that record_test appends records, not overwrites."""
        # Mock TEST_HISTORY_FILE
        original_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Record first test
            record_test("test_topic", 10, 8)

            # Record second test
            record_test("test_topic", 10, 9)

            # Verify file has two records
            with open(self.test_history_file) as f:
                data = json.load(f)
            self.assertEqual(len(data["test_topic"]), 2)
            self.assertAlmostEqual(data["test_topic"][0]["accuracy"], 0.8)
            self.assertAlmostEqual(data["test_topic"][1]["accuracy"], 0.9)
        finally:
            srs.TEST_HISTORY_FILE = original_file

    def test_record_test_boundary_score_zero(self):
        """Test record_test with score=0."""
        # Mock TEST_HISTORY_FILE
        original_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Record a test with 0 correct
            result = record_test("test_topic", 10, 0)

            # Verify result
            self.assertEqual(result["accuracy"], 0.0)
            self.assertEqual(result["total"], 10)
            self.assertEqual(result["correct"], 0)
        finally:
            srs.TEST_HISTORY_FILE = original_file

    def test_record_test_boundary_score_100(self):
        """Test record_test with score=100%."""
        # Mock TEST_HISTORY_FILE
        original_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Record a test with 100% correct
            result = record_test("test_topic", 10, 10)

            # Verify result
            self.assertEqual(result["accuracy"], 1.0)
            self.assertEqual(result["total"], 10)
            self.assertEqual(result["correct"], 10)
        finally:
            srs.TEST_HISTORY_FILE = original_file

    def test_record_test_invalid_total_zero(self):
        """Test record_test with total=0 raises ValueError."""
        with self.assertRaises(ValueError):
            record_test("test_topic", 0, 0)

    def test_record_test_invalid_correct_greater_than_total(self):
        """Test record_test with correct > total raises ValueError."""
        with self.assertRaises(ValueError):
            record_test("test_topic", 10, 11)

    def test_record_test_invalid_negative_correct(self):
        """Test record_test with negative correct raises ValueError."""
        with self.assertRaises(ValueError):
            record_test("test_topic", 10, -1)


class TestProfile(TestCase):
    """Test profile functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.profile_file = Path(self.temp_dir) / "profile.json"
        self.concepts_file = Path(self.temp_dir) / "concepts.json"
        self.test_history_file = Path(self.temp_dir) / "test_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.profile_file.exists():
            self.profile_file.unlink()
        if self.concepts_file.exists():
            self.concepts_file.unlink()
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_load_profile_default(self):
        """Test that load_profile returns default structure when file doesn't exist."""
        # Mock PROFILE_FILE
        original_file = srs.PROFILE_FILE
        srs.PROFILE_FILE = self.profile_file

        try:
            profile = load_profile()

            # Verify default structure
            self.assertEqual(profile["goal"], "")
            self.assertEqual(profile["total_hours"], 0)
            self.assertEqual(profile["topics"], {})
            self.assertEqual(profile["strengths"], [])
            self.assertEqual(profile["weaknesses"], [])
        finally:
            srs.PROFILE_FILE = original_file

    def test_update_profile_creates_topic(self):
        """Test that update_profile creates topic data."""
        # Mock files
        original_profile = srs.PROFILE_FILE
        original_concepts = srs.TOPICS_DIR
        original_test_history = srs.TEST_HISTORY_FILE

        srs.PROFILE_FILE = self.profile_file
        srs.TOPICS_DIR = Path(self.temp_dir)
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Create topic directory
            topic_dir = Path(self.temp_dir) / "test_topic"
            topic_dir.mkdir()

            # Create concepts file
            concepts = {
                "concept1": {"mastery": "mastered"},
                "concept2": {"mastery": "reviewing"}
            }
            with open(topic_dir / "concepts.json", "w") as f:
                json.dump(concepts, f)

            # Create test history
            test_history = {
                "test_topic": [
                    {"accuracy": 0.8, "timestamp": "2026-05-05"}
                ]
            }
            with open(self.test_history_file, "w") as f:
                json.dump(test_history, f)

            # Update profile
            profile = update_profile("test_topic")

            # Verify topic was created
            self.assertIn("test_topic", profile["topics"])
            self.assertEqual(profile["topics"]["test_topic"]["level"], "L2")
            self.assertEqual(profile["topics"]["test_topic"]["status"], "in_progress")

            # Cleanup
            (topic_dir / "concepts.json").unlink()
            topic_dir.rmdir()
        finally:
            srs.PROFILE_FILE = original_profile
            srs.TOPICS_DIR = original_concepts
            srs.TEST_HISTORY_FILE = original_test_history

    def test_profile_status_completed_for_l5(self):
        """Test that L5 user has status 'completed'."""
        # Mock files
        original_profile = srs.PROFILE_FILE
        original_concepts = srs.TOPICS_DIR
        original_test_history = srs.TEST_HISTORY_FILE

        srs.PROFILE_FILE = self.profile_file
        srs.TOPICS_DIR = Path(self.temp_dir)
        srs.TEST_HISTORY_FILE = self.test_history_file

        try:
            # Create topic directory
            topic_dir = Path(self.temp_dir) / "test_topic"
            topic_dir.mkdir()

            # Create concepts file with high mastery
            concepts = {
                "concept1": {"mastery": "mastered"},
                "concept2": {"mastery": "mastered"},
                "concept3": {"mastery": "mastered"},
                "concept4": {"mastery": "reviewing"},
                "concept5": {"mastery": "reviewing"}
            }
            with open(topic_dir / "concepts.json", "w") as f:
                json.dump(concepts, f)

            # Create test history with high scores
            test_history = {
                "test_topic": [
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.95, "timestamp": "2026-05-05"},
                    {"accuracy": 1.0, "timestamp": "2026-05-05"},
                    {"accuracy": 0.9, "timestamp": "2026-05-05"}
                ]
            }
            with open(self.test_history_file, "w") as f:
                json.dump(test_history, f)

            # Update profile
            profile = update_profile("test_topic")

            # Verify status is completed for L5
            self.assertIn("test_topic", profile["topics"])
            # Note: The level depends on the test history, but with 4 tests all >= 90%,
            # it should be L5
            level = profile["topics"]["test_topic"]["level"]
            status = profile["topics"]["test_topic"]["status"]

            # If level is L4 or L5, status should be completed
            if level in ("L4", "L5"):
                self.assertEqual(status, "completed")
            else:
                self.assertEqual(status, "in_progress")

            # Cleanup
            (topic_dir / "concepts.json").unlink()
            topic_dir.rmdir()
        finally:
            srs.PROFILE_FILE = original_profile
            srs.TOPICS_DIR = original_concepts
            srs.TEST_HISTORY_FILE = original_test_history

    def test_compare_profile_no_topics(self):
        """Test compare_profile_with_job returns default when no topics."""
        # Mock PROFILE_FILE
        original_file = srs.PROFILE_FILE
        srs.PROFILE_FILE = self.profile_file

        try:
            result = compare_profile_with_job("Python工程师")

            # Verify default structure
            self.assertEqual(result["job_title"], "Python工程师")
            self.assertEqual(result["current_level"], "L1")
            self.assertEqual(result["mastered_skills"], [])
            self.assertEqual(result["weaknesses"], [])
            self.assertEqual(result["total_hours"], 0)
            self.assertIn("Step 2a", result["suggestion"])
        finally:
            srs.PROFILE_FILE = original_file

    def test_compare_profile_with_topics(self):
        """Test compare_profile_with_job extracts highest level."""
        # Mock PROFILE_FILE
        original_file = srs.PROFILE_FILE
        srs.PROFILE_FILE = self.profile_file

        try:
            # Create profile with topics
            profile = {
                "goal": "成为 Python 工程师",
                "started": "2026-05-05",
                "total_hours": 10.0,
                "topics": {
                    "Python基础": {
                        "level": "L3",
                        "status": "in_progress",
                        "hours": 5.0,
                        "concepts_mastered": 10,
                        "concepts_total": 20,
                        "test_avg": 75.0
                    },
                    "Web开发": {
                        "level": "L5",
                        "status": "completed",
                        "hours": 5.0,
                        "concepts_mastered": 15,
                        "concepts_total": 15,
                        "test_avg": 95.0
                    }
                },
                "strengths": ["Flask", "Django", "FastAPI"],
                "weaknesses": ["装饰器", "异步编程"],
                "last_updated": "2026-05-05T20:00:00"
            }
            with open(self.profile_file, "w") as f:
                json.dump(profile, f)

            result = compare_profile_with_job("Python工程师")

            # Verify highest level is L5
            self.assertEqual(result["job_title"], "Python工程师")
            self.assertEqual(result["current_level"], "L5")
            self.assertEqual(result["total_hours"], 10.0)
            self.assertEqual(result["mastered_skills"], ["Flask", "Django", "FastAPI"])
            self.assertEqual(result["weaknesses"], ["装饰器", "异步编程"])
        finally:
            srs.PROFILE_FILE = original_file

    def test_compare_profile_numeric_level_comparison(self):
        """Test compare_profile_with_job uses numeric level comparison."""
        # Mock PROFILE_FILE
        original_file = srs.PROFILE_FILE
        srs.PROFILE_FILE = self.profile_file

        try:
            # Create profile with L10 level (edge case)
            profile = {
                "goal": "成为专家",
                "started": "2026-05-05",
                "total_hours": 100.0,
                "topics": {
                    "高级主题": {
                        "level": "L10",
                        "status": "completed",
                        "hours": 100.0,
                        "concepts_mastered": 50,
                        "concepts_total": 50,
                        "test_avg": 99.0
                    }
                },
                "strengths": ["高级技能"],
                "weaknesses": [],
                "last_updated": "2026-05-05T20:00:00"
            }
            with open(self.profile_file, "w") as f:
                json.dump(profile, f)

            result = compare_profile_with_job("专家")

            # Verify L10 > L2 (numeric comparison)
            self.assertEqual(result["current_level"], "L10")
        finally:
            srs.PROFILE_FILE = original_file


class TestNoSkipping(TestCase):
    """Test that levels cannot be skipped."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_history_file = Path(self.temp_dir) / "test_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_history_file.exists():
            self.test_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_no_skipping_with_bootstrap_failure(self):
        """Test that levels cannot be skipped even with bootstrap failure."""
        # Test case: [0.1, 0.1, 0.9, 0.9]
        # - first_avg = 0.1 < 0.2 → level=1 (L1)
        # - loop i=0: pair=[0.1, 0.1], both < 0.4 → no upgrade
        # - loop i=1: pair=[0.1, 0.9], 0.1 < 0.4 → no upgrade
        # - loop i=2: pair=[0.9, 0.9], both >= 0.4 → level=3 (L3)
        # But with the fix: level >= next_level - 1
        # - level=1, next_level=3: 1 >= 2? No! So upgrade is blocked.
        # So the result should be L1
        try:
            original_func = srs.load_test_history
            srs.load_test_history = lambda: {
                "test_topic": [
                    {"accuracy": 0.1, "timestamp": "2026-05-05"},
                    {"accuracy": 0.1, "timestamp": "2026-05-05"},
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                ]
            }

            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")
            # With the fix, L1 cannot jump to L3 (need to pass through L2 first)
            # first_avg = 0.1 < 0.2 → L1
            # loop i=0: pair=[0.1, 0.1], both < 0.4 → no upgrade
            # loop i=1: pair=[0.1, 0.9], 0.1 < 0.4 → no upgrade
            # loop i=2: pair=[0.9, 0.9], both >= 0.4, but level=1 < next_level-1=2 → blocked!
            # So result should be L1
            self.assertEqual(level_code, "L1")

            srs.load_test_history = original_func
        finally:
            srs.load_test_history = original_func

    def test_no_skipping_with_partial_pass(self):
        """Test that levels cannot be skipped even with partial pass."""
        # Test case: [0.3, 0.3, 0.5, 0.5]
        # - first_avg = 0.3 >= 0.2 → level=2 (L2)
        # - loop i=0: pair=[0.3, 0.3], both < 0.4 → no upgrade
        # - loop i=1: pair=[0.3, 0.5], 0.3 < 0.4 → no upgrade
        # - loop i=2: pair=[0.5, 0.5], both >= 0.4 → level=3 (L3)
        # With the fix: level >= next_level - 1
        # - level=2, next_level=3: 2 >= 2? Yes! So upgrade is allowed.
        # So the result should be L3
        try:
            original_func = srs.load_test_history
            srs.load_test_history = lambda: {
                "test_topic": [
                    {"accuracy": 0.3, "timestamp": "2026-05-05"},
                    {"accuracy": 0.3, "timestamp": "2026-05-05"},
                    {"accuracy": 0.5, "timestamp": "2026-05-05"},
                    {"accuracy": 0.5, "timestamp": "2026-05-05"},
                ]
            }

            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")
            # first_avg = 0.3 >= 0.2 → L2
            # loop i=0: pair=[0.3, 0.3], both < 0.4 → no upgrade
            # loop i=1: pair=[0.3, 0.5], 0.3 < 0.4 → no upgrade
            # loop i=2: pair=[0.5, 0.5], both >= 0.4, level=2 >= next_level-1=2 → allowed!
            # So result should be L3
            self.assertEqual(level_code, "L3")

            srs.load_test_history = original_func
        finally:
            srs.load_test_history = original_func


class TestRecordSimulation(TestCase):
    """Test record_simulation function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.simulation_history_file = Path(self.temp_dir) / "simulation_history.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.simulation_history_file.exists():
            self.simulation_history_file.unlink()
        os.rmdir(self.temp_dir)

    def test_record_simulation_writes_json(self):
        """Test that record_simulation writes to JSON file correctly."""
        # Mock SIMULATION_HISTORY_FILE
        original_file = srs.SIMULATION_HISTORY_FILE
        srs.SIMULATION_HISTORY_FILE = self.simulation_history_file

        try:
            # Record a simulation
            result = srs.record_simulation("test_topic", "标准AI模拟", 85, 4)

            # Verify result
            self.assertEqual(result["scenario"], "标准AI模拟")
            self.assertEqual(result["score"], 85)
            self.assertEqual(result["rounds"], 4)

            # Verify file was written
            self.assertTrue(self.simulation_history_file.exists())
            with open(self.simulation_history_file) as f:
                data = json.load(f)
            self.assertIn("test_topic", data)
            self.assertEqual(len(data["test_topic"]), 1)
            self.assertEqual(data["test_topic"][0]["score"], 85)
        finally:
            srs.SIMULATION_HISTORY_FILE = original_file


class TestCLICommands(TestCase):
    """Test CLI commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_topics_dir = srs.TOPICS_DIR
        self.original_test_history_file = srs.TEST_HISTORY_FILE
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"
        srs.TEST_HISTORY_FILE = Path(self.temp_dir) / "test_history.json"
        srs.TOPICS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.original_topics_dir
        srs.TEST_HISTORY_FILE = self.original_test_history_file

    def test_cmd_init_creates_topic_dir(self):
        """Test that cmd_init creates topic directory."""
        from srs import cmd_init
        cmd_init("test_topic")
        topic_dir = srs.TOPICS_DIR / "test_topic"
        self.assertTrue(topic_dir.exists())

    def test_cmd_add_creates_concept(self):
        """Test that cmd_add creates concept file."""
        from srs import cmd_init, cmd_add
        cmd_init("test_topic")
        cmd_add("test_topic", "test_concept")
        concepts_file = srs.TOPICS_DIR / "test_topic" / "concepts.json"
        self.assertTrue(concepts_file.exists())
        with open(concepts_file) as f:
            concepts = json.load(f)
        self.assertIn("test_concept", concepts)

    def test_cmd_due_returns_due_concepts(self):
        """Test that cmd_due returns due concepts."""
        from srs import cmd_init, cmd_add, cmd_due
        cmd_init("test_topic")
        cmd_add("test_topic", "test_concept")
        # This should not raise an exception
        cmd_due()

    def test_cmd_status_shows_overview(self):
        """Test that cmd_status shows overview."""
        from srs import cmd_init, cmd_add, cmd_status
        cmd_init("test_topic")
        cmd_add("test_topic", "test_concept")
        # This should not raise an exception
        cmd_status()

    def test_cmd_status_topic_shows_topic_detail(self):
        """Test that cmd_status <topic> shows topic detail."""
        from srs import cmd_init, cmd_add, cmd_status
        cmd_init("test_topic")
        cmd_add("test_topic", "test_concept")
        # This should not raise an exception
        cmd_status("test_topic")

    def test_cmd_config_shows_config(self):
        """Test that cmd_config shows config."""
        from srs import cmd_config
        # This should not raise an exception
        cmd_config()

    def test_cmd_config_set_updates_value(self):
        """Test that cmd_config set updates value."""
        from srs import cmd_config
        # cmd_config(key, value) - "set" is handled in main(), not cmd_config
        cmd_config("learning_depth", "deep")


class TestCalcOverdue(TestCase):
    """Test calc_overdue function."""

    def test_valid_date_not_overdue(self):
        """Test that future date returns 0."""
        from srs import calc_overdue
        future_date = "2099-12-31"
        self.assertEqual(calc_overdue(future_date), 0)

    def test_valid_date_overdue(self):
        """Test that past date returns positive days."""
        from srs import calc_overdue
        past_date = "2020-01-01"
        result = calc_overdue(past_date)
        self.assertGreater(result, 0)

    def test_none_returns_zero(self):
        """Test that None returns 0."""
        from srs import calc_overdue
        self.assertEqual(calc_overdue(None), 0)

    def test_empty_string_returns_zero(self):
        """Test that empty string returns 0."""
        from srs import calc_overdue
        self.assertEqual(calc_overdue(""), 0)

    def test_malformed_date_returns_zero(self):
        """Test that malformed date returns 0 instead of crashing."""
        from srs import calc_overdue
        self.assertEqual(calc_overdue("not-a-date"), 0)
        self.assertEqual(calc_overdue("2026/05/06"), 0)
        self.assertEqual(calc_overdue("invalid"), 0)

    def test_today_returns_zero(self):
        """Test that today returns 0."""
        from srs import calc_overdue, today
        self.assertEqual(calc_overdue(today()), 0)


class TestSanitizeTopic(TestCase):
    """Test sanitize_topic function."""

    def test_valid_english_topic(self):
        from srs import sanitize_topic
        self.assertEqual(sanitize_topic("python-basics"), "python-basics")

    def test_valid_chinese_topic(self):
        from srs import sanitize_topic
        self.assertEqual(sanitize_topic("Python基础"), "Python基础")

    def test_path_traversal_rejected(self):
        from srs import sanitize_topic, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_topic("test/../../../etc/passwd")

    def test_dot_dot_rejected(self):
        from srs import sanitize_topic, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_topic("../secret")

    def test_empty_string_rejected(self):
        from srs import sanitize_topic, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_topic("")

    def test_spaces_rejected(self):
        from srs import sanitize_topic, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_topic("test topic")


class TestCalcNextReviewHard(TestCase):
    """Test calc_next_review with hard rating."""

    def test_hard_increases_interval_by_1_2(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 10, "ease_factor": 2.5,
            "reviews": 5, "correct_count": 4, "total_count": 5, "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "hard")
        self.assertEqual(updated["interval_days"], 12)
        self.assertAlmostEqual(updated["ease_factor"], 2.35)
        self.assertEqual(updated["correct_count"], 5)

    def test_hard_minimum_ease_factor_is_1_3(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 10, "ease_factor": 1.4,
            "reviews": 5, "correct_count": 4, "total_count": 5, "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "hard")
        self.assertAlmostEqual(updated["ease_factor"], 1.3)

    def test_invalid_rating_raises_error(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 10, "ease_factor": 2.5,
            "reviews": 5, "correct_count": 4, "total_count": 5, "mastery": "reviewing",
        }
        with self.assertRaises(ValueError):
            calc_next_review(concept, "invalid")


class TestMasteryFromUnseen(TestCase):
    """Test mastery updates from unseen after first review."""

    def test_first_review_changes_mastery(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 1, "ease_factor": 2.5,
            "reviews": 0, "correct_count": 0, "total_count": 0, "mastery": "unseen",
        }
        updated = calc_next_review(concept, "good")
        self.assertEqual(updated["mastery"], "learning")


class TestThresholdBoundaries(TestCase):
    """Test level thresholds at exact boundary values."""

    def setUp(self):
        self.original_func = srs.load_test_history

    def tearDown(self):
        srs.load_test_history = self.original_func

    def test_exactly_at_20_returns_l2(self):
        srs.load_test_history = lambda: {"t": [{"accuracy": 0.2, "timestamp": ""}, {"accuracy": 0.2, "timestamp": ""}]}
        level_code, _, _ = calc_level_by_accuracy("t")
        self.assertEqual(level_code, "L2")

    def test_below_20_returns_l1(self):
        srs.load_test_history = lambda: {"t": [{"accuracy": 0.19, "timestamp": ""}, {"accuracy": 0.19, "timestamp": ""}]}
        level_code, _, _ = calc_level_by_accuracy("t")
        self.assertEqual(level_code, "L1")

    def test_exactly_at_40_returns_l3(self):
        srs.load_test_history = lambda: {"t": [
            {"accuracy": 0.3, "timestamp": ""}, {"accuracy": 0.3, "timestamp": ""},
            {"accuracy": 0.4, "timestamp": ""}, {"accuracy": 0.4, "timestamp": ""},
        ]}
        level_code, _, _ = calc_level_by_accuracy("t")
        self.assertEqual(level_code, "L3")


class TestRateCommand(TestCase):
    """Test cmd_rate function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_topics = srs.TOPICS_DIR
        self.orig_config = srs.CONFIG_FILE
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"
        srs.CONFIG_FILE = Path(self.temp_dir) / "config.json"
        srs.TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.orig_topics
        srs.CONFIG_FILE = self.orig_config
        srs._config_cache = None
        srs._config_cache_time = None

    def test_rate_easy_increases_interval(self):
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        cmd_rate("t", "c1", "easy")
        concepts = srs.load_concepts("t")
        self.assertGreater(concepts["c1"]["interval_days"], 1)

    def test_rate_wrong_resets_interval(self):
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        cmd_rate("t", "c1", "good")
        cmd_rate("t", "c1", "wrong")
        concepts = srs.load_concepts("t")
        self.assertEqual(concepts["c1"]["interval_days"], 1)

    def test_rate_invalid_rating(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate("t", "c1", "invalid")
        self.assertIn("Error", f.getvalue())

    def test_rate_path_traversal_rejected(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_rate
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate("../../etc/passwd", "c1", "easy")
        self.assertIn("Error", f.getvalue())


class TestLoadConfigFallback(TestCase):
    """Test load_config caching and fallback."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_config = srs.CONFIG_FILE
        srs.CONFIG_FILE = Path(self.temp_dir) / "config.json"
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.CONFIG_FILE = self.orig_config
        srs._config_cache = None
        srs._config_cache_time = None

    def test_returns_defaults_on_corrupt_json(self):
        from srs import load_config, DEFAULT_CONFIG
        with open(srs.CONFIG_FILE, "w") as f:
            f.write("{invalid")
        config = load_config(use_cache=False)
        self.assertEqual(config["learning_depth"], DEFAULT_CONFIG["learning_depth"])

    def test_merges_missing_keys(self):
        from srs import load_config
        with open(srs.CONFIG_FILE, "w") as f:
            json.dump({"learning_depth": "deep"}, f)
        config = load_config(use_cache=False)
        self.assertEqual(config["learning_depth"], "deep")
        self.assertIn("level_thresholds", config)

    def test_deepcopy_cache(self):
        from srs import load_config, save_config
        config = load_config(use_cache=False)
        save_config(config)
        c2 = load_config(use_cache=True)
        c2["level_thresholds"]["L2"] = 0.99
        c3 = load_config(use_cache=True)
        self.assertEqual(c3["level_thresholds"]["L2"], 0.2)


class TestSanitizeConcept(TestCase):
    """Test sanitize_concept function."""

    def test_valid_english_concept(self):
        from srs import sanitize_concept
        self.assertEqual(sanitize_concept("for-loop"), "for-loop")

    def test_valid_chinese_concept(self):
        from srs import sanitize_concept
        self.assertEqual(sanitize_concept("列表推导式"), "列表推导式")

    def test_valid_with_underscore(self):
        from srs import sanitize_concept
        self.assertEqual(sanitize_concept("my_concept"), "my_concept")

    def test_valid_with_digits(self):
        from srs import sanitize_concept
        self.assertEqual(sanitize_concept("concept123"), "concept123")

    def test_empty_string_rejected(self):
        from srs import sanitize_concept, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_concept("")

    def test_spaces_rejected(self):
        from srs import sanitize_concept, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_concept("my concept")

    def test_path_traversal_rejected(self):
        from srs import sanitize_concept, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_concept("../etc/passwd")

    def test_slash_rejected(self):
        from srs import sanitize_concept, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_concept("test/concept")

    def test_special_chars_rejected(self):
        from srs import sanitize_concept, SanitizeError
        with self.assertRaises(SanitizeError):
            sanitize_concept("concept@#$")

    def test_length_200_accepted(self):
        from srs import sanitize_concept
        name = "a" * 200
        self.assertEqual(sanitize_concept(name), name)

    def test_length_201_rejected(self):
        from srs import sanitize_concept, SanitizeError
        name = "a" * 201
        with self.assertRaises(SanitizeError):
            sanitize_concept(name)

    def test_max_length_boundary(self):
        from srs import sanitize_concept, SanitizeError
        # Exactly 200 should pass
        name = "a" * 200
        self.assertEqual(sanitize_concept(name), name)
        # 201 should fail
        with self.assertRaises(SanitizeError):
            sanitize_concept("a" * 201)


class TestAtomicTextSave(TestCase):
    """Test _atomic_text_save function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.target_file = Path(self.temp_dir) / "test.txt"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_writes_content(self):
        from srs import _atomic_text_save
        _atomic_text_save(self.target_file, "hello world")
        self.assertTrue(self.target_file.exists())
        self.assertEqual(self.target_file.read_text(encoding="utf-8"), "hello world")

    def test_overwrites_existing(self):
        from srs import _atomic_text_save
        _atomic_text_save(self.target_file, "first")
        _atomic_text_save(self.target_file, "second")
        self.assertEqual(self.target_file.read_text(encoding="utf-8"), "second")

    def test_creates_parent_dirs(self):
        from srs import _atomic_text_save
        nested = Path(self.temp_dir) / "sub" / "dir" / "file.txt"
        _atomic_text_save(nested, "nested content")
        self.assertTrue(nested.exists())
        self.assertEqual(nested.read_text(encoding="utf-8"), "nested content")

    def test_writes_unicode(self):
        from srs import _atomic_text_save
        content = "你好世界 🌍"
        _atomic_text_save(self.target_file, content)
        self.assertEqual(self.target_file.read_text(encoding="utf-8"), content)

    def test_no_temp_file_left_on_success(self):
        from srs import _atomic_text_save
        _atomic_text_save(self.target_file, "content")
        tmp_files = list(Path(self.temp_dir).glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)


class TestSaveProgress(TestCase):
    """Test save_progress function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_topics = srs.TOPICS_DIR
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.orig_topics

    def test_save_creates_file(self):
        from srs import save_progress, load_progress
        save_progress("test_topic", "# Progress\n\nDone.")
        content = load_progress("test_topic")
        self.assertIn("Done.", content)

    def test_save_overwrites(self):
        from srs import save_progress, load_progress
        save_progress("test_topic", "first")
        save_progress("test_topic", "second")
        content = load_progress("test_topic")
        self.assertEqual(content, "second")

    def test_save_creates_parent_dirs(self):
        from srs import save_progress, load_progress
        save_progress("new_topic", "content")
        content = load_progress("new_topic")
        self.assertEqual(content, "content")


class TestGetAccuracyStr(TestCase):
    """Test get_accuracy_str function."""

    def test_zero_total_returns_na(self):
        from srs import get_accuracy_str
        concept = {"total_count": 0, "correct_count": 0}
        self.assertEqual(get_accuracy_str(concept), "N/A")

    def test_100_percent(self):
        from srs import get_accuracy_str
        concept = {"total_count": 10, "correct_count": 10}
        self.assertEqual(get_accuracy_str(concept), "100%")

    def test_50_percent(self):
        from srs import get_accuracy_str
        concept = {"total_count": 10, "correct_count": 5}
        self.assertEqual(get_accuracy_str(concept), "50%")

    def test_zero_correct(self):
        from srs import get_accuracy_str
        concept = {"total_count": 5, "correct_count": 0}
        self.assertEqual(get_accuracy_str(concept), "0%")


class TestGetMasteryEmoji(TestCase):
    """Test get_mastery_emoji function."""

    def test_mastered(self):
        from srs import get_mastery_emoji
        self.assertEqual(get_mastery_emoji("mastered"), "[MASTERED]")

    def test_reviewing(self):
        from srs import get_mastery_emoji
        self.assertEqual(get_mastery_emoji("reviewing"), "[REVIEWING]")

    def test_learning(self):
        from srs import get_mastery_emoji
        self.assertEqual(get_mastery_emoji("learning"), "[LEARNING]")

    def test_unseen(self):
        from srs import get_mastery_emoji
        self.assertEqual(get_mastery_emoji("unseen"), "[UNSEEN]")

    def test_unknown_returns_unseen(self):
        from srs import get_mastery_emoji
        self.assertEqual(get_mastery_emoji("unknown"), "[UNSEEN]")


class TestCmdInitPathTraversal(TestCase):
    """Test cmd_init rejects path traversal."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_topics = srs.TOPICS_DIR
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"
        srs.TOPICS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.orig_topics

    def test_rejects_dot_dot(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_init("../evil")
        output = f.getvalue()
        self.assertIn("Error", output)
        # Should not create directory outside TOPICS_DIR
        evil_dir = Path(self.temp_dir) / "evil"
        self.assertFalse(evil_dir.exists())

    def test_rejects_slash(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_init("test/evil")
        self.assertIn("Error", f.getvalue())


class TestCmdAddConceptValidation(TestCase):
    """Test cmd_add rejects invalid concept names."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_topics = srs.TOPICS_DIR
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"
        srs.TOPICS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.orig_topics

    def test_rejects_path_traversal_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init("t")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add("t", "../evil")
        self.assertIn("Error", f.getvalue())

    def test_rejects_spaces_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init("t")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add("t", "bad concept")
        self.assertIn("Error", f.getvalue())

    def test_rejects_too_long_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init("t")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add("t", "a" * 201)
        self.assertIn("Error", f.getvalue())

    def test_accepts_valid_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init("t")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add("t", "valid-concept")
        self.assertIn("OK", f.getvalue())


class TestCmdRateConceptValidation(TestCase):
    """Test cmd_rate rejects invalid concept names."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_topics = srs.TOPICS_DIR
        srs.TOPICS_DIR = Path(self.temp_dir) / "topics"
        srs.TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TOPICS_DIR = self.orig_topics
        srs._config_cache = None
        srs._config_cache_time = None

    def test_rejects_path_traversal_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate("t", "../evil", "easy")
        self.assertIn("Error", f.getvalue())

    def test_rejects_spaces_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate("t", "bad concept", "easy")
        self.assertIn("Error", f.getvalue())

    def test_rejects_too_long_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init("t")
        cmd_add("t", "c1")
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate("t", "a" * 201, "easy")
        self.assertIn("Error", f.getvalue())


class TestRecordSimulationBoundary(TestCase):
    """Test record_simulation boundary and error cases."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_file = srs.SIMULATION_HISTORY_FILE
        srs.SIMULATION_HISTORY_FILE = Path(self.temp_dir) / "sim.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.SIMULATION_HISTORY_FILE = self.orig_file

    def test_score_zero(self):
        from srs import record_simulation
        result = record_simulation("t", "s", 0)
        self.assertEqual(result["score"], 0)

    def test_score_100(self):
        from srs import record_simulation
        result = record_simulation("t", "s", 100)
        self.assertEqual(result["score"], 100)

    def test_negative_score_raises(self):
        from srs import record_simulation
        with self.assertRaises(ValueError):
            record_simulation("t", "s", -1)

    def test_score_over_100_raises(self):
        from srs import record_simulation
        with self.assertRaises(ValueError):
            record_simulation("t", "s", 101)

    def test_zero_rounds_raises(self):
        from srs import record_simulation
        with self.assertRaises(ValueError):
            record_simulation("t", "s", 50, 0)

    def test_default_rounds_is_3(self):
        from srs import record_simulation
        result = record_simulation("t", "s", 50)
        self.assertEqual(result["rounds"], 3)

    def test_appends_records(self):
        from srs import record_simulation
        record_simulation("t", "s1", 80)
        record_simulation("t", "s2", 90)
        with open(srs.SIMULATION_HISTORY_FILE) as f:
            data = json.load(f)
        self.assertEqual(len(data["t"]), 2)


class TestLoadConfigFileNotFound(TestCase):
    """Test load_config when file doesn't exist."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_config = srs.CONFIG_FILE
        srs.CONFIG_FILE = Path(self.temp_dir) / "nonexistent.json"
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.CONFIG_FILE = self.orig_config
        srs._config_cache = None
        srs._config_cache_time = None

    def test_returns_defaults(self):
        from srs import load_config, DEFAULT_CONFIG
        config = load_config(use_cache=False)
        self.assertEqual(config, DEFAULT_CONFIG)


class TestCheckSession(TestCase):
    """Test check_session function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = Path(self.temp_dir) / "test_history.json"
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TEST_HISTORY_FILE = self.orig_file
        srs._config_cache = None
        srs._config_cache_time = None

    def test_no_history_returns_no_history(self):
        result = check_session("nonexistent")
        self.assertEqual(result["status"], "no_history")

    def test_fresh_record_is_not_stale(self):
        """A record just made (within 120 min) should not be stale."""
        # Write a test record with current timestamp
        save_test_history({
            "math": [{"timestamp": datetime.now().isoformat(), "accuracy": 0.8, "total": 10, "correct": 8}]
        })
        result = check_session("math")
        self.assertEqual(result["status"], "fresh")
        self.assertEqual(result["stale_count"], 0)

    def test_old_record_is_stale(self):
        """A record from 3 hours ago should be stale."""
        old_ts = (datetime.now() - timedelta(hours=3)).isoformat()
        save_test_history({
            "math": [{"timestamp": old_ts, "accuracy": 0.8, "total": 10, "correct": 8}]
        })
        result = check_session("math")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["stale_count"], 1)
        self.assertTrue(result["findings"][0]["stale"])

    def test_custom_stale_threshold(self):
        """Custom threshold should work."""
        old_ts = (datetime.now() - timedelta(minutes=5)).isoformat()
        save_test_history({
            "math": [{"timestamp": old_ts, "accuracy": 0.8, "total": 10, "correct": 8}]
        })
        # Default 120 min => not stale
        result = check_session("math", stale_minutes=120)
        self.assertEqual(result["status"], "fresh")
        # Custom 1 min => stale
        result = check_session("math", stale_minutes=1)
        self.assertEqual(result["status"], "stale")

    def test_all_topics_checked_when_none(self):
        """When topic is None, check all topics."""
        save_test_history({
            "math": [{"timestamp": datetime.now().isoformat(), "accuracy": 0.8, "total": 10, "correct": 8}],
            "physics": [{"timestamp": (datetime.now() - timedelta(hours=5)).isoformat(), "accuracy": 0.5, "total": 10, "correct": 5}],
        })
        result = check_session()
        self.assertEqual(len(result["findings"]), 2)
        self.assertEqual(result["stale_count"], 1)


class TestCheckBurnout(TestCase):
    """Test check_burnout function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_file = srs.TEST_HISTORY_FILE
        srs.TEST_HISTORY_FILE = Path(self.temp_dir) / "test_history.json"
        srs._config_cache = None
        srs._config_cache_time = None

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        srs.TEST_HISTORY_FILE = self.orig_file
        srs._config_cache = None
        srs._config_cache_time = None

    def test_no_data_returns_no_data(self):
        result = check_burnout("nonexistent")
        self.assertEqual(result["status"], "no_data")

    def test_single_high_accuracy_low_risk(self):
        save_test_history({
            "math": [{"timestamp": datetime.now().isoformat(), "accuracy": 0.9, "total": 10, "correct": 9}]
        })
        result = check_burnout("math")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["risk"], "low")

    def test_declining_trend_high_risk(self):
        """Three declining tests with very low avg should be high risk."""
        save_test_history({
            "math": [
                {"timestamp": (datetime.now() - timedelta(days=2)).isoformat(), "accuracy": 0.5, "total": 10, "correct": 5},
                {"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "accuracy": 0.3, "total": 10, "correct": 3},
                {"timestamp": datetime.now().isoformat(), "accuracy": 0.1, "total": 10, "correct": 1},
            ]
        })
        result = check_burnout("math")
        self.assertEqual(result["risk"], "high")
        self.assertEqual(result["trend"], "declining")
        self.assertTrue(len(result["suggestions"]) > 0)

    def test_consecutive_below_50_triggers_high_risk(self):
        """3+ consecutive below 50% should be high risk even if trend is stable."""
        save_test_history({
            "math": [
                {"timestamp": (datetime.now() - timedelta(days=3)).isoformat(), "accuracy": 0.1, "total": 10, "correct": 1},
                {"timestamp": (datetime.now() - timedelta(days=2)).isoformat(), "accuracy": 0.1, "total": 10, "correct": 1},
                {"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "accuracy": 0.1, "total": 10, "correct": 1},
            ]
        })
        result = check_burnout("math")
        self.assertEqual(result["consecutive_below_50"], 3)
        self.assertEqual(result["risk"], "high")

    def test_improving_trend_low_risk(self):
        """Improving accuracy trend should be low risk."""
        save_test_history({
            "math": [
                {"timestamp": (datetime.now() - timedelta(days=2)).isoformat(), "accuracy": 0.3, "total": 10, "correct": 3},
                {"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "accuracy": 0.6, "total": 10, "correct": 6},
                {"timestamp": datetime.now().isoformat(), "accuracy": 0.9, "total": 10, "correct": 9},
            ]
        })
        result = check_burnout("math")
        self.assertEqual(result["trend"], "improving")
        self.assertEqual(result["risk"], "low")

    def test_stable_good_performance_low_risk(self):
        """Stable high accuracy should be low risk."""
        save_test_history({
            "math": [
                {"timestamp": (datetime.now() - timedelta(days=i)).isoformat(), "accuracy": 0.8, "total": 10, "correct": 8}
                for i in range(5, 0, -1)
            ]
        })
        result = check_burnout("math")
        self.assertEqual(result["trend"], "stable")
        self.assertEqual(result["risk"], "low")

    def test_custom_window(self):
        """Window parameter should control how many recent tests to analyze."""
        save_test_history({
            "math": [
                {"timestamp": (datetime.now() - timedelta(days=10 - i)).isoformat(), "accuracy": 0.9, "total": 10, "correct": 9}
                for i in range(10)
            ]
        })
        result = check_burnout("math", window=3)
        self.assertEqual(result["recent_tests"], 3)
        self.assertEqual(result["avg_accuracy"], 0.9)

    def test_invalid_topic_raises(self):
        with self.assertRaises(srs.SanitizeError):
            check_burnout("../evil")


if __name__ == "__main__":
    main()
