"""Keep the original review seal verifiable after publication wording changes."""

import unittest
from pathlib import Path
from unittest.mock import patch

import verify_review


class ReviewSnapshotTests(unittest.TestCase):
    def test_updated_documents_preserve_historical_inventory(self):
        result = verify_review.check()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["inventoried_git_files_checked"]["U1"], 256)
        self.assertEqual(result["snapshot_commit"], verify_review.REVIEW_SNAPSHOT_COMMIT)
        self.assertIn("Historical", result["record_scope"])

    def test_changing_frozen_review_json_is_rejected(self):
        with patch.object(Path, "read_bytes", return_value=b"{}\n"):
            with self.assertRaisesRegex(AssertionError, "must remain unchanged"):
                verify_review.check()

    def test_corrupt_original_metadata_bytes_are_rejected(self):
        real_git = verify_review.git
        for name in ("PUBLICATION_REVIEW.md", "PUBLICATION_PR_DRAFT.md"):
            target = verify_review.REVIEW_SNAPSHOT_COMMIT + ":docs/" + name

            def corrupt_snapshot(*args):
                if args == ("show", target):
                    return b"corrupt original metadata\n"
                return real_git(*args)

            with self.subTest(document=name):
                with patch.object(verify_review, "git", side_effect=corrupt_snapshot):
                    with self.assertRaises(AssertionError):
                        verify_review.check()


if __name__ == "__main__":
    unittest.main()
