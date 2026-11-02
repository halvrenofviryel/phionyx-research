# Component licenses and data handling

The new K5 wrapper/test/document files follow this repository's AGPL-3.0 license;
a full copy is provided as `licenses/K5-AGPL-3.0.txt`. The packet is an aggregation
of separate components. **No dependency or AIREP component is relicensed.**

The exact AIREP source bundle preserves its root Apache-2.0 code license,
CC-BY-4.0 specification/schema text and original notices/license-scope files.
Copies of the two root license texts are under `licenses/`. Frozen K2's contract
and README retain their own licensing notices. Original authorship/copyright
and upstream source identities remain in the Git objects and dependency metadata.

[DEPENDENCY_ARTIFACTS.json](DEPENDENCY_ARTIFACTS.json) lists every dependency
artifact used by the replay: 46 K3 wheels plus nine Python wheels and five Node
tarballs from K2's frozen release. It records exact archive hashes, versions,
URLs where originally supplied, source commit/path otherwise, package-declared
license metadata, and byte-identical extracted license/notice/METADATA copies.
The original archives are also retained intact. Metadata statements are recorded
as declarations, not a new legal determination or endorsement.

Python, Node, Git, the operating system and libc are external system
prerequisites. Their binaries are not redistributed by this packet. The
clean-room test uses installed standard runtimes; it does not package the
author's home, credential file, pip cache or private environment.

No real user records or private answers are needed. Inputs are the published
synthetic AIREP reference vectors and controlled local file operations. K2 uses
explicitly public, insecure fixture signing seeds. They are reproducibility
data, never operational credentials. K3 generates ephemeral signing keys in
memory and saves only public test bindings. Neither experiment needs an API key,
account login, paid model call or private repository access.

Historical frozen logs contain original execution paths, repository author
metadata, and timestamps. These are preserved for exact provenance and are not
required paths or identities for a new run. The publication reviewer must inspect
the full inventory/diffs and decide whether to publish this unchanged evidence
or prepare a separately pinned derivative; do not silently edit the frozen data.

For submissions, use synthetic inputs and public test keys. Do not send access
tokens, private production keys, personal records or confidential logs. Redact
before submitting, describe the transformation, and hash the submitted bytes;
do not claim they are the original unredacted artifacts. The packet performs no
automatic transfer. Permission to cite is false in the blank template until the
submitter explicitly grants it.
