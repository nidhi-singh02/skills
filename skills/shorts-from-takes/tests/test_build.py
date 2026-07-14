import importlib.util
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
BUILD_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build.py"
SPEC = importlib.util.spec_from_file_location("shorts_from_takes_build", BUILD_PATH)
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


def base_config(**overrides):
    return build.deep_merge(build.DEFAULTS, overrides)


class ConfigTests(unittest.TestCase):
    def test_deep_merge_keeps_nested_quality_defaults(self):
        cfg = base_config(quality_checks={"freeze_frames": {"severity": "error"}})

        self.assertEqual(cfg["quality_checks"]["freeze_frames"]["severity"], "error")
        self.assertEqual(cfg["quality_checks"]["freeze_frames"]["min_duration"], 1.5)
        self.assertEqual(cfg["quality_checks"]["black_frames"]["severity"], "error")

    def test_segment_speed_override_preserves_global_default(self):
        cfg = base_config(speed=1.1)

        self.assertEqual(build.segment_speed({"_i": 0}, cfg), 1.1)
        self.assertEqual(build.segment_speed({"_i": 1, "speed": 1.25}, cfg), 1.25)

    def test_resolve_transitions_supports_new_and_legacy_options(self):
        cfg = base_config(
            xfade=0.2,
            xfade_type="fade",
            xfade_types=["wipeleft", "slideup"],
            transitions=[{"duration": 0.12}, {"type": "fade", "duration": 0.3}],
        )

        self.assertEqual(
            build.resolve_transitions(cfg, 3),
            [
                {"type": "wipeleft", "duration": 0.12},
                {"type": "fade", "duration": 0.3},
            ],
        )

    def test_ideal_duration_uses_each_segment_speed_and_join_duration(self):
        cfg = base_config(speed=1.0)
        segments = [
            {"src": "a.mp4", "start": 0, "end": 10, "speed": 2.0},
            {"src": "b.mp4", "start": 2, "end": 8},
        ]
        transitions = [{"type": "fade", "duration": 0.25}]

        self.assertAlmostEqual(
            build.ideal_timeline_duration(segments, transitions, cfg), 10.75)

    def test_validate_spec_rejects_duplicate_and_missing_segment_indices(self):
        cfg = base_config()
        segments = [
            {"_i": 0, "src": "a.mp4", "start": 0, "end": 1},
            {"_i": 1, "src": "b.mp4", "start": 0, "end": 1},
        ]

        with self.assertRaisesRegex(build.RenderConfigError, "every segment exactly once"):
            build.validate_spec(cfg, segments, [[0, 0]])


class QualityEventTests(unittest.TestCase):
    def test_parse_black_events(self):
        log = (
            "[blackdetect] black_start:0.25 black_end:0.75 black_duration:0.5\n"
            "[blackdetect] black_start:9 black_end:9.4 black_duration:0.4\n"
        )

        self.assertEqual(
            build.parse_black_events(log),
            [(0.25, 0.75, 0.5), (9.0, 9.4, 0.4)],
        )

    def test_parse_freeze_events_including_eof_hold(self):
        log = (
            "lavfi.freezedetect.freeze_start: 1.5\n"
            "lavfi.freezedetect.freeze_duration: 2\n"
            "lavfi.freezedetect.freeze_end: 3.5\n"
            "lavfi.freezedetect.freeze_start: 8\n"
        )

        self.assertEqual(
            build.parse_freeze_events(log, 10.0),
            [(1.5, 3.5, 2.0), (8.0, 10.0, 2.0)],
        )

    def test_unexpected_events_respects_allow_ranges(self):
        events = [(1.0, 2.0, 1.0), (8.0, 10.0, 2.0)]

        self.assertEqual(build.unexpected_events(events, [[7.9, 10.0]]), [events[0]])


if __name__ == "__main__":
    unittest.main()
