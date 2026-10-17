# cue-sample-plan

Partition local CUE/WAVE source sample frames into track, recorded-pregap and unassigned intervals.

For: Audio archivists checking how a CUE sheet would divide an uncompressed disc image. A split plan should explain recorded gaps and account for every source frame before any encoder runs.

## Quickstart

Python 3.10 or newer; no runtime packages or network access. The wheel build needs setuptools from the normal Python package registry.

```sh
git clone https://github.com/nripankadas07/cue-sample-plan.git
cd cue-sample-plan
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/cue-sample-plan --make-example example-work
.venv/bin/cue-sample-plan example-work/example.cue
```

The generator writes invented silence into a new directory. The plan exits 0 and covers [0,44100) track 1, [44100,88200) recorded pregap, and [88200,176400) track 2. Planning does not modify source files.

Windows equivalents use `.venv\Scripts\python.exe` and `.venv\Scripts\cue-sample-plan.exe`; Windows/macOS are not executed by this release’s Linux CI.

## Contract

UTF-8 CUE with quoted basename-only FILE WAVE, consecutive AUDIO tracks and INDEX 01 plus optional preceding INDEX 00. Actual little-endian RIFF/WAVE PCM or IEEE_FLOAT metadata determines sample rate, frame alignment, data bounds and byte offsets. CUE indices are 75 frames/second and must map to integer sample-frame boundaries exactly. A sample frame contains all channels. Intervals use exclusive ends and cover each source frame exactly once, including explicit unassigned leading audio findings. SHA256 identifies source bytes.

JSON goes to stdout. Exit 0 means a valid report without findings; exit 1 means a valid report with the documented findings; exit 2 means invalid input or an I/O failure, with an error on stderr and no partial report. `--help` describes options. Review outputs before sharing them; they may contain input identifiers.

## Limits

CUE 64 KiB, 16 local files, 99 tracks, 64 MiB per WAVE/128 MiB aggregate. No symlinks or path traversal, compressed audio, RF64/RIFX/extensible WAVE, synthetic PREGAP/POSTGAP, extra indices, copying, transcoding, resampling, tags or audio quality assessment. Unknown RIFF chunks are counted. --make-example only creates a new directory and refuses overwrite.

## Verify

```sh
python3 -m unittest -v test_behavior
python3 -m compileall -q .
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 -m venv /tmp/cue-sample-plan-check
/tmp/cue-sample-plan-check/bin/python -m pip install --no-deps dist/*.whl
python3 verify_installed.py /tmp/cue-sample-plan-check/bin/python
```

Installed-command checks run outside the checkout. See [validation](VALIDATION.md), [research](RESEARCH.md), [contributing](CONTRIBUTING.md), [support](SUPPORT.md) and [security](SECURITY.md).

Original implementation and invented fixtures developed with AI assistance. MIT license. No production adoption, competitor feature-absence or performance-superiority claim.
