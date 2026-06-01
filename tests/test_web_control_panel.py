from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest import mock
import uuid

import web_control_panel as panel


class WebControlPanelExecutionTests(unittest.TestCase):
    def test_missing_cli_path_returns_failure_instead_of_success(self) -> None:
        with mock.patch("web_control_panel.shutil.which", return_value=None):
            with mock.patch("web_control_panel.KNOWN_CLI_PATHS", {"claude": []}):
                result = panel.resolve_cli_path("claude")

        self.assertIsNone(result)

    def test_calculator_request_creates_artifact_and_verified_status(self) -> None:
        root = panel.LOCAL_DIR / "test-runs" / uuid.uuid4().hex
        try:
            root.mkdir(parents=True)
            task_dir = root / "task"
            target_repo = root / "계산기"
            task_dir.mkdir()
            (task_dir / "artifacts").mkdir()
            (task_dir / "log.md").write_text("# Log\n", encoding="utf-8")

            result = panel.run_development_task(
                {
                    "request": "계산기 만들어줘",
                    "taskPath": str(task_dir),
                    "targetRepo": str(target_repo),
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["status"], "completed")
            self.assertTrue((target_repo / "index.html").exists())
            self.assertTrue((target_repo / "app.js").exists())
            status = json.loads((task_dir / "artifacts" / "run-status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "completed")
            self.assertIn("검증 통과", status["message"])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
