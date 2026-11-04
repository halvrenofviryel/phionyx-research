# Release plan — `control-evidence-study-v1.0.0`

This record is preparation metadata. It does not assert that the tag, GitHub
release or Zenodo deposit exists.

## Intended assets

- `control-evidence-study-v1.0.0.tar.gz`
- `control-evidence-study-v1.0.0.tar.gz.sha256`
- `control-evidence-study-v1.0.0.manifest.json`

## Required publication order

1. Merge the documentation/release-preparation PR with all checks passing.
2. Build from the exact clean commit intended for the tag.
3. Verify the archive on a fresh extraction path.
4. Create the annotated tag `control-evidence-study-v1.0.0` at that exact commit.
5. Create a GitHub release and attach the three generated assets.
6. Deposit the same archive and metadata in Zenodo.
7. Record the assigned version DOI in the study citation files in a follow-up PR.

The GitHub release and Zenodo deposit are public actions requiring owner approval.
The builder performs none of them.
