# Research — 17 October 2026

User: Audio archivists checking how a CUE sheet would divide an uncompressed disc image.

Pain: A split plan should explain recorded gaps and account for every source frame before any encoder runs.

Smallest useful capability: Partition local CUE/WAVE source sample frames into track, recorded-pregap and unassigned intervals.

Acceptance: Prove exact contiguous frame coverage, explicit INDEX00 gaps and leading findings, stereo byte offsets, source-byte preservation, RIFF validation, and rejection of unrepresentable frame boundaries and unsafe paths.

Demand is inferred from the workflow and adjacent public evidence, not a verified request for this product. Discovery path: descriptive GitHub topics, a runnable invented example and the chronological portfolio index. No unsolicited outreach or activity manipulation.

## Current alternatives

Live GitHub repository search, sorted **Most stars**, query `audio CD image` and the related broad queries recorded in [provenance](RESEARCH_PROVENANCE.json). Highest-star relevant comparable found in this inspected scope: **flacon/flacon**. This is not an exhaustive global ranking.

| Repository | Stars observed | Last push observed (UTC) | Archived | API license classification |
| --- | ---: | --- | --- | --- |
| [flacon/flacon](https://github.com/flacon/flacon) | 546 | 2026-10-13T15:50:26Z | False | LGPL-2.1 |
| [ftrvxmtrx/split2flac](https://github.com/ftrvxmtrx/split2flac) | 259 | 2020-05-08T20:11:32Z | True | NOASSERTION |
| [jeanslack/FFcuesplitter](https://github.com/jeanslack/FFcuesplitter) | 98 | 2026-10-13T07:50:11Z | False | GPL-3.0 |

Flacon already extracts and tags tracks from disc images. FFcuesplitter supports broader audio formats and text encodings. split2flac is archived and its README points to a replacement; it is a historical alternative, not presented as maintained. Flacon cue.cpp already treats INDEX00 and INDEX01. Our read-only sample accounting intentionally omits splitting and compressed formats.

Flacon or FFcuesplitter for actual extraction; inspect the CUE manually before choosing an encoder.

Current README, selected source semantics and up to five issue/PR records were read. Exact observation times, source blob identities, queries and public issue URLs are in provenance. API NOASSERTION means unclassified license, not permission to copy. No third-party implementation or fixtures are bundled.

Our small Python wheel installs with one command after checkout and includes a direct example. Established alternatives have broader APIs, formats, documentation, examples and support communities. Competitor installations, time to first useful result, reliability, support response and performance were not measured. Our example only proves our documented behavior. Stars inform discovery, not quality or performance.

Portfolio distinction: The existing medialoom repository catalogs media metadata. This tool reads CUE index semantics and actual RIFF binary data to construct a complete source-frame partition, rather than another catalog.

No technical performance benchmark, speed/memory superiority or exhaustive feature-gap claim is made. Standard file formats and algorithms are not inventions of this project. Source references informed semantic review; implementation, prose and invented fixtures are original. No copied branding or sample user data is included.
