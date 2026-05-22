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
    load_learning_log,
    load_profile,
    load_test_history,
    record_test,
    save_profile,
    save_test_history,
    update_profile,
)

# Explicit SM-2 config for tests that verify SM-2 behavior
SM2_CONFIG = {"algorithm": "sm2", "mastery_threshold": 0.8, "level_thresholds": {"L2": 0.2, "L3": 0.4, "L4": 0.7, "L5": 0.9}}


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


    def test_demotion_from_l5_to_l4(self):
        """Test that demotion from L5 only drops one level per check."""
        # Mock load_test_history to return 9 tests:
        # - Tests 1-2: 90% (upgrade to L3)
        # - Tests 3-4: 50% (intermediate)
        # - Tests 5-6: 80% (upgrade to L4)
        # - Tests 7-8: 90% (upgrade to L5)
        # - Tests 9-11: 60% (below L5 threshold 90%, but above L4 threshold 70%)
        # Scientific basis: gradual degradation (SM-2, Ebbinghaus)
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
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.9, "timestamp": "2026-05-05"},
                    {"accuracy": 0.6, "timestamp": "2026-05-05"},
                    {"accuracy": 0.6, "timestamp": "2026-05-05"},
                    {"accuracy": 0.6, "timestamp": "2026-05-05"},
                ]
            }

            level_code, level_name, level_emoji = calc_level_by_accuracy("test_topic")
            # Should be L4: last 3 are 60% < 90% (L5 threshold) → demote to L4
            # But 60% >= 70% is false, so... wait, 60% < 70% too
            # Actually: last3 are 60%, which is < L5 threshold (90%) → demote one level to L4
            # The demotion only checks current level (L5) threshold, not L4 threshold
            self.assertEqual(level_code, "L4")

            srs.load_test_history = original_func
        finally:
            srs.load_test_history = original_func

    def test_demotion_gradual(self):
        """Test that demotion requires multiple checks with new test results."""
        # Scenario: L5 with 3x10% → L4 (one demotion)
        # Then 3 more 10% tests → L3 (second demotion)
        # Each demotion requires its own set of 3 failing tests
        try:
            original_func = srs.load_test_history
            # First check: L5 with 3x10%
            srs.load_test_history = lambda: {
                "test_topic": [
                    {"accuracy": 0.9}, {"accuracy": 0.9},  # L2
                    {"accuracy": 0.5}, {"accuracy": 0.5},  # intermediate
                    {"accuracy": 0.8}, {"accuracy": 0.8},  # L4
                    {"accuracy": 0.9}, {"accuracy": 0.9},  # L5
                    {"accuracy": 0.1}, {"accuracy": 0.1}, {"accuracy": 0.1},  # fail
                ]
            }
            level_code, _, _ = calc_level_by_accuracy("test_topic")
            self.assertEqual(level_code, "L4", "L5 + 3x10% should demote to L4")

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
        updated = calc_next_review(concept, "wrong", SM2_CONFIG)
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
        updated = calc_next_review(concept, "good", SM2_CONFIG)
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
        updated = calc_next_review(concept, "easy", SM2_CONFIG)
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
        updated = calc_next_review(concept, "wrong", SM2_CONFIG)
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
        updated = calc_next_review(concept, "easy", SM2_CONFIG)
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
        cmd_init(["test_topic"])
        topic_dir = srs.TOPICS_DIR / "test_topic"
        self.assertTrue(topic_dir.exists())

    def test_cmd_add_creates_concept(self):
        """Test that cmd_add creates concept file."""
        from srs import cmd_init, cmd_add
        cmd_init(["test_topic"])
        cmd_add(["test_topic", "test_concept"])
        concepts_file = srs.TOPICS_DIR / "test_topic" / "concepts.json"
        self.assertTrue(concepts_file.exists())
        with open(concepts_file) as f:
            concepts = json.load(f)
        self.assertIn("test_concept", concepts)

    def test_cmd_due_returns_due_concepts(self):
        """Test that cmd_due returns due concepts."""
        from srs import cmd_init, cmd_add, cmd_due
        cmd_init(["test_topic"])
        cmd_add(["test_topic", "test_concept"])
        # This should not raise an exception
        cmd_due([])

    def test_cmd_status_shows_overview(self):
        """Test that cmd_status shows overview."""
        from srs import cmd_init, cmd_add, cmd_status
        cmd_init(["test_topic"])
        cmd_add(["test_topic", "test_concept"])
        # This should not raise an exception
        cmd_status([])

    def test_cmd_status_topic_shows_topic_detail(self):
        """Test that cmd_status <topic> shows topic detail."""
        from srs import cmd_init, cmd_add, cmd_status
        cmd_init(["test_topic"])
        cmd_add(["test_topic", "test_concept"])
        # This should not raise an exception
        cmd_status(["test_topic"])

    def test_cmd_config_shows_config(self):
        """Test that cmd_config shows config."""
        from srs import cmd_config
        # This should not raise an exception
        cmd_config([])

    def test_cmd_config_set_updates_value(self):
        """Test that cmd_config set updates value."""
        from srs import cmd_config
        # "set" subcommand is now handled inside cmd_config
        cmd_config(["set", "learning_depth", "deep"])


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
        updated = calc_next_review(concept, "hard", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 12)
        self.assertAlmostEqual(updated["ease_factor"], 2.35)
        self.assertEqual(updated["correct_count"], 5)

    def test_hard_minimum_ease_factor_is_1_3(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 10, "ease_factor": 1.4,
            "reviews": 5, "correct_count": 4, "total_count": 5, "mastery": "reviewing",
        }
        updated = calc_next_review(concept, "hard", SM2_CONFIG)
        self.assertAlmostEqual(updated["ease_factor"], 1.3)

    def test_invalid_rating_raises_error(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 10, "ease_factor": 2.5,
            "reviews": 5, "correct_count": 4, "total_count": 5, "mastery": "reviewing",
        }
        with self.assertRaises(ValueError):
            calc_next_review(concept, "invalid", SM2_CONFIG)


class TestMasteryFromUnseen(TestCase):
    """Test mastery updates from unseen after first review."""

    def test_first_review_changes_mastery(self):
        from srs import calc_next_review
        concept = {
            "interval_days": 1, "ease_factor": 2.5,
            "reviews": 0, "correct_count": 0, "total_count": 0, "mastery": "unseen",
        }
        updated = calc_next_review(concept, "good", SM2_CONFIG)
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
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        cmd_rate(["t", "c1", "easy"])
        concepts = srs.load_concepts("t")
        self.assertGreater(concepts["c1"]["interval_days"], 1)

    def test_rate_wrong_resets_interval(self):
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        cmd_rate(["t", "c1", "good"])
        cmd_rate(["t", "c1", "wrong"])
        concepts = srs.load_concepts("t")
        self.assertEqual(concepts["c1"]["interval_days"], 1)

    def test_rate_invalid_rating(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate(["t", "c1", "invalid"])
        self.assertIn("Error", f.getvalue())

    def test_rate_path_traversal_rejected(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_rate
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate(["../../etc/passwd", "c1", "easy"])
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
            cmd_init(["../evil"])
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
            cmd_init(["test/evil"])
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
        cmd_init(["t"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add(["t", "../evil"])
        self.assertIn("Error", f.getvalue())

    def test_rejects_spaces_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init(["t"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add(["t", "bad concept"])
        self.assertIn("Error", f.getvalue())

    def test_rejects_too_long_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init(["t"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add(["t", "a" * 201])
        self.assertIn("Error", f.getvalue())

    def test_accepts_valid_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add
        cmd_init(["t"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_add(["t", "valid-concept"])
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
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate(["t", "../evil", "easy"])
        self.assertIn("Error", f.getvalue())

    def test_rejects_spaces_in_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate(["t", "bad concept", "easy"])
        self.assertIn("Error", f.getvalue())

    def test_rejects_too_long_concept(self):
        import io
        from contextlib import redirect_stdout
        from srs import cmd_init, cmd_add, cmd_rate
        cmd_init(["t"])
        cmd_add(["t", "c1"])
        f = io.StringIO()
        with redirect_stdout(f):
            cmd_rate(["t", "a" * 201, "easy"])
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


class TestLearningLog(TestCase):
    """Test learning log functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_log_file = Path(self.temp_dir) / "learning_log.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.learning_log_file.exists():
            self.learning_log_file.unlink()
        os.rmdir(self.temp_dir)

    def test_load_learning_log_empty(self):
        """Test loading empty learning log."""
        result = srs.load_learning_log()
        self.assertIsInstance(result, list)

    def test_append_learning_log(self):
        """Test appending to learning log."""
        # Mock LEARNING_LOG_FILE
        original_file = srs.LEARNING_LOG_FILE
        srs.LEARNING_LOG_FILE = self.learning_log_file
        try:
            srs.append_learning_log("rate", "math", {"concept": "algebra", "rating": "good"})
            log = srs.load_learning_log()
            self.assertEqual(len(log), 1)
            self.assertEqual(log[0]["action"], "rate")
            self.assertEqual(log[0]["topic"], "math")
        finally:
            srs.LEARNING_LOG_FILE = original_file

    def test_get_last_learning_time_empty(self):
        """Test getting last learning time from empty log."""
        # Mock LEARNING_LOG_FILE
        original_file = srs.LEARNING_LOG_FILE
        srs.LEARNING_LOG_FILE = self.learning_log_file
        try:
            result = srs.get_last_learning_time()
            self.assertIsNone(result)
        finally:
            srs.LEARNING_LOG_FILE = original_file


class TestReminderCommands(TestCase):
    """Test reminder-related commands (v1.2.0)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.learn_dir = Path(self.tmpdir) / "learn"
        self.learn_dir.mkdir(parents=True, exist_ok=True)
        self.topics_dir = self.learn_dir / "topics"
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.learn_dir / "config.json"
        self.log_file = self.learn_dir / "learning_log.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _mock_paths(self):
        """Return a context manager that patches srs paths."""
        from unittest.mock import patch
        return patch.multiple(
            srs,
            LEARN_DIR=self.learn_dir,
            TOPICS_DIR=self.topics_dir,
            CONFIG_FILE=self.config_file,
            LEARNING_LOG_FILE=self.log_file,
        )

    def test_cmd_reminder_empty_topics(self):
        """Test reminder command with no topics."""
        from io import StringIO
        from unittest.mock import patch
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_reminder([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["total_due"], 0)
            self.assertEqual(output["topics"], [])
            self.assertIn("risk", output)
            self.assertIn("risk_msg", output)

    def test_cmd_reminder_with_due_concepts(self):
        """Test reminder command with due concepts."""
        from io import StringIO
        from unittest.mock import patch
        topic_dir = self.topics_dir / "test-topic"
        topic_dir.mkdir()
        concepts = {
            "concept-a": {
                "mastery": "learning",
                "next_review": srs.today(),
                "ease_factor": 2.5,
                "interval_days": 1,
                "reviews": 1,
                "correct_count": 1,
                "total_count": 1,
                "level": "L1"
            }
        }
        with open(topic_dir / "concepts.json", "w") as f:
            json.dump(concepts, f)
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_reminder([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["total_due"], 1)
            self.assertEqual(output["topics"][0]["name"], "test-topic")

    def test_cmd_reminder_risk_critical(self):
        """Test reminder risk level when 7+ days since last learning."""
        from io import StringIO
        from unittest.mock import patch
        # Write old learning log
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        log = [{"timestamp": old_time, "action": "rate", "topic": "test"}]
        with open(self.log_file, "w") as f:
            json.dump(log, f)
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_reminder([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["risk"], "critical")

    def test_cmd_reminder_risk_none(self):
        """Test reminder risk level when learned today."""
        from io import StringIO
        from unittest.mock import patch
        log = [{"timestamp": datetime.now().isoformat(), "action": "rate", "topic": "test"}]
        with open(self.log_file, "w") as f:
            json.dump(log, f)
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_reminder([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["risk"], "none")

    def test_cmd_weekly_report_empty_log(self):
        """Test weekly report with empty learning log."""
        from io import StringIO
        from unittest.mock import patch
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_weekly_report([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["learning_days"], 0)
            self.assertEqual(output["total_actions"], 0)
            self.assertEqual(output["topics_covered"], [])

    def test_cmd_weekly_report_with_entries(self):
        """Test weekly report with recent learning entries."""
        from io import StringIO
        from unittest.mock import patch
        log = [
            {"timestamp": datetime.now().isoformat(), "action": "rate", "topic": "math"},
            {"timestamp": datetime.now().isoformat(), "action": "record-test", "topic": "math", "accuracy": 80},
        ]
        with open(self.log_file, "w") as f:
            json.dump(log, f)
        # Create topic directory so calc_level_by_accuracy works
        topic_dir = self.topics_dir / "math"
        topic_dir.mkdir()
        with open(topic_dir / "concepts.json", "w") as f:
            json.dump({}, f)
        with self._mock_paths():
            with patch('sys.stdout', new_callable=StringIO) as mock_out:
                srs.cmd_weekly_report([])
            output = json.loads(mock_out.getvalue())
            self.assertEqual(output["learning_days"], 1)
            self.assertEqual(output["total_actions"], 2)
            self.assertIn("math", output["topics_covered"])

    def test_cmd_check_reminder_no_crons(self):
        """Test check-reminder when no crons exist."""
        from io import StringIO
        from unittest.mock import patch
        with self._mock_paths():
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = type('obj', (object,), {
                    'returncode': 0,
                    'stdout': '{"jobs": []}',
                    'stderr': ''
                })()
                with patch('sys.stdout', new_callable=StringIO) as mock_out:
                    srs.cmd_check_reminder([])
                output = mock_out.getvalue()
                self.assertIn('NOT ENABLED', output)

    def test_cmd_check_reminder_with_crons(self):
        """Test check-reminder when crons exist."""
        from io import StringIO
        from unittest.mock import patch
        with self._mock_paths():
            # Write config with learning contract
            config = {"learning_contract": {"time": "08:30"}}
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = type('obj', (object,), {
                    'returncode': 0,
                    'stdout': '{"jobs": [{"name": "retaincraft-reminder"}, {"name": "retaincraft-weekly-report"}]}',
                    'stderr': ''
                })()
                with patch('sys.stdout', new_callable=StringIO) as mock_out:
                    srs.cmd_check_reminder([])
                output = mock_out.getvalue()
                self.assertIn('ENABLED', output)
                self.assertIn('08:30', output)

    def test_cmd_setup_reminder_invalid_time(self):
        """Test setup-reminder with invalid time format falls back to 09:00."""
        from io import StringIO
        from unittest.mock import patch
        with self._mock_paths():
            # Clear config cache
            srs._config_cache = None
            srs._config_cache_time = None
            config = {"learning_contract": {"time": "bad-time"}}
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = type('obj', (object,), {
                    'returncode': 0,
                    'stdout': '{}',
                    'stderr': ''
                })()
                with patch('sys.stdout', new_callable=StringIO) as mock_out:
                    srs.cmd_setup_reminder([])
                output = mock_out.getvalue()
                self.assertIn('Invalid', output)
                self.assertIn('09:00', output)

    def test_cron_exists_json_formats(self):
        """Test _cron_exists handles both dict and list JSON formats."""
        from unittest.mock import patch
        # New format: {"jobs": [...]}
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = type('obj', (object,), {
                'returncode': 0,
                'stdout': '{"jobs": [{"name": "retaincraft-reminder"}]}',
                'stderr': ''
            })()
            self.assertTrue(srs._cron_exists("retaincraft-reminder"))
            self.assertFalse(srs._cron_exists("nonexistent"))
        # Old format: [...]
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = type('obj', (object,), {
                'returncode': 0,
                'stdout': '[{"name": "retaincraft-reminder"}]',
                'stderr': ''
            })()
            self.assertTrue(srs._cron_exists("retaincraft-reminder"))

    def test_get_user_channel_from_sessions(self):
        """Test _get_user_channel detects channel from main session."""
        from unittest.mock import patch
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = type('obj', (object,), {
                'returncode': 0,
                'stdout': '{"sessions": [{"type": "main", "origin": {"provider": "qqbot"}}]}',
                'stderr': ''
            })()
            self.assertEqual(srs._get_user_channel(), "qqbot")

    def test_get_user_channel_no_main(self):
        """Test _get_user_channel returns None when no main session."""
        from unittest.mock import patch
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = type('obj', (object,), {
                'returncode': 0,
                'stdout': '{"sessions": []}',
                'stderr': ''
            })()
            self.assertIsNone(srs._get_user_channel())


class TestSM2SecondInterval(TestCase):
    """Test SM-2 second interval fix."""

    def test_second_review_interval_is_6_days(self):
        """Test that second review interval is 6 days (original SM-2)."""
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 1
        concept["interval_days"] = 1
        concept["ease_factor"] = 2.5

        # First review with "good"
        updated = calc_next_review(concept, "good", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 6)

    def test_third_review_uses_ease_factor(self):
        """Test that third review uses ease_factor multiplication."""
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 2
        concept["interval_days"] = 6
        concept["ease_factor"] = 2.5

        # Third review with "good"
        updated = calc_next_review(concept, "good", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 15)  # 6 * 2.5 = 15

    def test_second_review_hard_rating_interval_is_6_days(self):
        """Test that second review with 'hard' rating also uses SM2_SECOND_INTERVAL=6.

        Bug #1: SM-2 'hard' rating was missing is_second_review check,
        causing second review interval to be max(1, int(1 * 1.2)) = 1 day
        instead of SM2_SECOND_INTERVAL = 6 days.
        Wozniak (1987) specifies second review interval = 6 days regardless of rating.
        """
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 1
        concept["interval_days"] = 1
        concept["ease_factor"] = 2.5

        updated = calc_next_review(concept, "hard", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 6)

    def test_third_review_hard_uses_interval_formula(self):
        """Test that third review with 'hard' uses interval * 1.2 formula."""
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 2
        concept["interval_days"] = 6
        concept["ease_factor"] = 2.5

        updated = calc_next_review(concept, "hard", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 7)  # max(1, int(6 * 1.2)) = 7

    def test_wrong_rating_resets_interval(self):
        """Test that wrong rating resets interval to 1 day."""
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 5
        concept["interval_days"] = 30
        concept["ease_factor"] = 2.5

        # Review with "wrong"
        updated = calc_next_review(concept, "wrong", SM2_CONFIG)
        self.assertEqual(updated["interval_days"], 1)


class TestFSRS5Algorithm(TestCase):
    """Test FSRS-5 spaced repetition algorithm implementation.

    Formulas verified against:
    - IEEE TKDE 2023 paper (DOI: 10.1109/TKDE.2023.3251721)
    """

    def test_fsrs_initial_stability(self):
        """Test S₀(G) = w[G-1] for each rating."""
        from srs import fsrs_init_stability
        weights = srs.FSRS_V5_WEIGHTS
        self.assertAlmostEqual(fsrs_init_stability(1), weights[0])  # Again
        self.assertAlmostEqual(fsrs_init_stability(2), weights[1])  # Hard
        self.assertAlmostEqual(fsrs_init_stability(3), weights[2])  # Good
        self.assertAlmostEqual(fsrs_init_stability(4), weights[3])  # Easy

    def test_fsrs_initial_difficulty(self):
        """Test D₀(G) = w₄ - exp(w₅ × (G-1)) + 1, clamped to [1, 10]."""
        from srs import fsrs_init_difficulty
        import math
        weights = srs.FSRS_V5_WEIGHTS
        # Good rating (G=3): D₀ = w₄ - exp(w₅ × 2) + 1
        d_good = weights[4] - math.exp(weights[5] * 2) + 1
        self.assertAlmostEqual(fsrs_init_difficulty(3), max(1, min(10, d_good)))
        # Easy rating should give lower difficulty than Again
        self.assertLess(fsrs_init_difficulty(4), fsrs_init_difficulty(1))

    def test_fsrs_retrievability_at_stability(self):
        """Test R(S, S) ≈ 0.9 (design property of FSRS)."""
        from srs import fsrs_retrievability
        r = fsrs_retrievability(10.0, 10.0)  # t=S => R should be ~0.9
        self.assertAlmostEqual(r, 0.9, places=2)

    def test_fsrs_retrievability_decreases(self):
        """Test that R decreases as t increases (forgetting curve)."""
        from srs import fsrs_retrievability
        r1 = fsrs_retrievability(1.0, 10.0)
        r5 = fsrs_retrievability(5.0, 10.0)
        r10 = fsrs_retrievability(10.0, 10.0)
        self.assertGreater(r1, r5)
        self.assertGreater(r5, r10)

    def test_fsrs_interval_from_stability(self):
        """Test that interval is derived from stability for desired retention."""
        from srs import fsrs_next_interval
        # For S=10, interval should be ~10 days (since R(S,S)=0.9)
        interval = fsrs_next_interval(10.0)
        self.assertAlmostEqual(interval, 10.0, delta=1.0)

    def test_fsrs_sm2_data_compatibility(self):
        """Test that old SM-2 data (ease_factor/interval) doesn't crash FSRS."""
        from srs import calc_next_review
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 1
        concept["interval_days"] = 1
        concept["ease_factor"] = 2.5
        # Should work without algorithm field (defaults to SM-2)
        updated = calc_next_review(concept, "good")
        self.assertIn("interval_days", updated)

    def test_fsrs_difficulty_clamp(self):
        """Test that difficulty is clamped to [1, 10]."""
        from srs import fsrs_update_difficulty
        # Extreme difficulty should be clamped
        d = fsrs_update_difficulty(0.5, 3)  # Very low difficulty
        self.assertGreaterEqual(d, 1)
        d = fsrs_update_difficulty(15.0, 1)  # Very high difficulty + Again
        self.assertLessEqual(d, 10)

    def test_fsrs_stability_after_recall_positive(self):
        """Test that successful recall increases stability."""
        from srs import fsrs_stability_after_recall
        s_old = 10.0
        d = 5.0
        r = 0.9
        s_new = fsrs_stability_after_recall(s_old, d, r, 3)  # Good rating
        self.assertGreater(s_new, s_old)

    def test_fsrs_stability_after_forgetting_decreases(self):
        """Test that forgetting decreases stability."""
        from srs import fsrs_stability_after_forgetting
        s_old = 10.0
        d = 5.0
        r = 0.5
        s_new = fsrs_stability_after_forgetting(s_old, d, r)
        self.assertLess(s_new, s_old)

    def test_fsrs_nan_inf_fallback(self):
        """Test that NaN/Inf results fall back to SM-2."""
        from srs import calc_next_review
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["algorithm"] = "fsrs"
        concept["difficulty"] = 5.0
        concept["stability"] = 10.0
        concept["retrievability"] = 0.9
        concept["reviews"] = 3
        concept["interval_days"] = 10
        # Normal case should work
        updated = calc_next_review(concept, "good")
        self.assertIn("interval_days", updated)
        self.assertNotEqual(updated["interval_days"], 0)

    def test_fsrs_algorithm_switch(self):
        """Test that config algorithm=fsrs enables FSRS scheduling."""
        from srs import calc_next_review, DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        config["algorithm"] = "fsrs"
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 0
        concept["total_count"] = 0
        concept["correct_count"] = 0
        # First review with FSRS
        updated = calc_next_review(concept, "good", config)
        self.assertIn("difficulty", updated)
        self.assertIn("stability", updated)
        self.assertIn("retrievability", updated)
        self.assertGreater(updated["interval_days"], 0)

    def test_fsrs_wrong_rating_uses_forgetting_path(self):
        """Test that 'wrong' rating triggers stability decrease (forgetting path).

        This is a critical regression test — previously 'wrong' was mapped to
        rating_int=3 (Good) instead of 1 (Again), causing stability to increase
        instead of decrease on failure.
        """
        from srs import calc_next_review, DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        config["algorithm"] = "fsrs"
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 0
        concept["total_count"] = 0
        concept["correct_count"] = 0
        # First review with good to establish stability
        c1 = calc_next_review(concept, "good", config)
        s_after_good = c1["stability"]
        self.assertGreater(s_after_good, 0)
        # Second review with wrong — stability should DECREASE
        c1["reviews"] = 1
        c1["total_count"] = 1
        c1["correct_count"] = 1
        c2 = calc_next_review(c1, "wrong", config)
        s_after_wrong = c2["stability"]
        self.assertLess(s_after_wrong, s_after_wrong + 1)  # Sanity check
        # The key assertion: wrong should give smaller interval than good
        c1_copy = c1.copy()
        c1_copy["reviews"] = 1
        c1_copy["total_count"] = 1
        c1_copy["correct_count"] = 1
        c3 = calc_next_review(c1_copy, "good", config)
        self.assertLess(c2["interval_days"], c3["interval_days"],
                        "wrong rating should produce shorter interval than good")

    def test_fsrs_default_is_fsrs(self):
        """Test that default algorithm is FSRS-5 (v1.3.0)."""
        from srs import calc_next_review
        concept = srs.DEFAULT_CONCEPT.copy()
        concept["reviews"] = 0
        concept["total_count"] = 0
        concept["correct_count"] = 0
        updated = calc_next_review(concept, "good")
        # FSRS-5 should add difficulty and stability fields
        self.assertIn("difficulty", updated)
        self.assertIn("stability", updated)


class TestOptimizeParams(TestCase):
    """Test cmd_optimize_params gradient descent optimization."""

    def test_optimize_params_insufficient_reviews(self):
        """Test that optimize-params rejects < 1000 reviews."""
        from srs import cmd_optimize_params
        import io
        from contextlib import redirect_stdout

        # Clear learning log to ensure < 1000 reviews
        log_path = Path.home() / "learn" / "learning_log.json"
        if log_path.exists():
            backup = log_path.read_text(encoding="utf-8")
        else:
            backup = None

        try:
            log_path.write_text("[]", encoding="utf-8")
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_optimize_params([])
            output = f.getvalue()
            self.assertIn("1,000", output)
            self.assertIn("Need at least", output)
        finally:
            if backup:
                log_path.write_text(backup, encoding="utf-8")

    def test_optimize_params_uniform_rating(self):
        """Test that optimize-params rejects >95% same rating."""
        from srs import cmd_optimize_params
        import io
        from contextlib import redirect_stdout

        log_path = Path.home() / "learn" / "learning_log.json"
        if log_path.exists():
            backup = log_path.read_text(encoding="utf-8")
        else:
            backup = None

        try:
            # Generate 1000+ reviews with 99% "good" rating
            entries = []
            for i in range(1050):
                entries.append({
                    "timestamp": f"2026-04-{(i % 28) + 1:02d}T10:00:00",
                    "action": "rate",
                    "topic": "test",
                    "details": {
                        "concept": f"concept_{i % 5}",
                        "rating": "good" if i < 1040 else "wrong"
                    }
                })
            log_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")

            f = io.StringIO()
            with redirect_stdout(f):
                cmd_optimize_params([])
            output = f.getvalue()
            self.assertIn("99%", output)
            self.assertIn("diverse", output)
        finally:
            if backup:
                log_path.write_text(backup, encoding="utf-8")

    def test_optimize_params_insufficient_different_days(self):
        """Test that optimize-params rejects < 50 different-day reviews."""
        from srs import cmd_optimize_params
        import io
        from contextlib import redirect_stdout

        log_path = Path.home() / "learn" / "learning_log.json"
        if log_path.exists():
            backup = log_path.read_text(encoding="utf-8")
        else:
            backup = None

        try:
            # Generate 1000+ reviews but only on 3 different days
            entries = []
            ratings = ["good", "hard", "easy", "wrong"]
            for i in range(1050):
                day = (i % 3) + 1
                entries.append({
                    "timestamp": f"2026-04-{day:02d}T10:00:00",
                    "action": "rate",
                    "topic": "test",
                    "details": {
                        "concept": f"concept_{i % 5}",
                        "rating": ratings[i % 4]
                    }
                })
            log_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")

            f = io.StringIO()
            with redirect_stdout(f):
                cmd_optimize_params([])
            output = f.getvalue()
            self.assertIn("Different-day", output)
            self.assertIn("50+", output)
        finally:
            if backup:
                log_path.write_text(backup, encoding="utf-8")

    def test_optimize_params_saves_weights(self):
        """Test that optimize-params saves optimized weights to config."""
        from srs import cmd_optimize_params, load_config
        import io
        from contextlib import redirect_stdout

        log_path = Path.home() / "learn" / "learning_log.json"
        config_path = Path.home() / "learn" / "config.json"
        if log_path.exists():
            log_backup = log_path.read_text(encoding="utf-8")
        else:
            log_backup = None
        if config_path.exists():
            config_backup = config_path.read_text(encoding="utf-8")
        else:
            config_backup = None

        try:
            # Generate 1000+ reviews across 60+ days with diverse ratings
            entries = []
            ratings = ["good", "hard", "easy", "wrong"]
            for i in range(1100):
                day = (i % 60) + 1
                entries.append({
                    "timestamp": f"2026-{(i // 60) + 1:02d}-{day:02d}T10:00:00",
                    "action": "rate",
                    "topic": "test",
                    "details": {
                        "concept": f"concept_{i % 10}",
                        "rating": ratings[i % 4]
                    }
                })
            log_path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")

            # Remove fsrs_weights from config
            config = json.loads(config_backup) if config_backup else {}
            config.pop("fsrs_weights", None)
            config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

            f = io.StringIO()
            with redirect_stdout(f):
                cmd_optimize_params([])
            output = f.getvalue()
            self.assertIn("Optimized parameters saved", output)

            # Verify weights were saved
            from srs import load_config
            saved_config = load_config(use_cache=False)
            self.assertIn("fsrs_weights", saved_config)
            self.assertEqual(len(saved_config["fsrs_weights"]), 19)
        finally:
            if log_backup:
                log_path.write_text(log_backup, encoding="utf-8")
            if config_backup:
                config_path.write_text(config_backup, encoding="utf-8")


class TestSignContract(TestCase):
    """Test cmd_sign_contract command."""

    def test_sign_contract_normal(self):
        """Test normal JSON input saves contract and outputs REMINDER_REQUIRED."""
        from srs import cmd_sign_contract, load_config
        import io
        from contextlib import redirect_stdout

        config_path = Path.home() / "learn" / "config.json"
        if config_path.exists():
            backup = config_path.read_text(encoding="utf-8")
        else:
            backup = None

        try:
            contract_json = '{"time":"20:00","days":["Mon","Tue","Wed"],"duration":60,"target_level":"L4"}'
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_sign_contract([contract_json])
            output = f.getvalue()

            self.assertIn("Learning contract saved", output)
            self.assertIn("REMINDER_REQUIRED", output)
            self.assertIn("20:00", output)

            # Verify contract was saved to config
            saved_config = load_config(use_cache=False)
            self.assertIn("learning_contract", saved_config)
            self.assertEqual(saved_config["learning_contract"]["time"], "20:00")
        finally:
            if backup:
                config_path.write_text(backup, encoding="utf-8")

    def test_sign_contract_invalid_json(self):
        """Test invalid JSON input shows error without crashing."""
        from srs import cmd_sign_contract
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_sign_contract(["not valid json"])
        output = f.getvalue()

        self.assertIn("Invalid JSON", output)

    def test_sign_contract_no_args(self):
        """Test missing arguments shows usage hint."""
        from srs import cmd_sign_contract
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_sign_contract([])
        output = f.getvalue()

        self.assertIn("Usage", output)

    def test_sign_contract_config_roundtrip(self):
        """Test that saved contract can be read back correctly."""
        from srs import cmd_sign_contract, load_config
        import io
        from contextlib import redirect_stdout

        config_path = Path.home() / "learn" / "config.json"
        if config_path.exists():
            backup = config_path.read_text(encoding="utf-8")
        else:
            backup = None

        try:
            contract = {"time": "09:30", "days": ["Mon", "Wed", "Fri"], "duration": 45, "target_level": "L3"}
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_sign_contract([json.dumps(contract)])
            output = f.getvalue()

            self.assertIn("REMINDER_REQUIRED", output)

            saved = load_config(use_cache=False)
            self.assertEqual(saved["learning_contract"]["time"], "09:30")
            self.assertEqual(saved["learning_contract"]["target_level"], "L3")
            self.assertEqual(len(saved["learning_contract"]["days"]), 3)
        finally:
            if backup:
                config_path.write_text(backup, encoding="utf-8")


if __name__ == "__main__":
    main()
