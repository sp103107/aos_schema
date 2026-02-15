import unittest

from aos_runtime.io_utils import read_json
from aos_runtime.runner import run_envelope


class TestEnvelopeRuns(unittest.TestCase):
    def test_foreman_example_runs(self):
        env = read_json("examples/envelopes/foreman_task.json")
        response, record = run_envelope(env)
        self.assertEqual(response["status"], "SUCCESS")
        self.assertIn("duration_ms", record)

    def test_sorcerer_example_runs(self):
        env = read_json("examples/envelopes/sorcerer_task.json")
        response, record = run_envelope(env)
        self.assertEqual(response["status"], "SUCCESS")
        self.assertTrue(len(response["artifacts"]) >= 1)


if __name__ == "__main__":
    unittest.main()
