# Archive validation

Checked 2026-10-17 after final collection and index generation.

- Source manifest: 858 records; each has an existing local capsule.
- Generated source files: 858; matched against the manifest to detect stale duplicates.
- Local Markdown/HTML links checked: 17,067.
- Unique original image files hashed and matched: 1,995.
- Image container/XML verification: see IMAGE_DIMENSIONS.json; this is structural validation, not visual review of every image.
- All packaged JSON registers parsed successfully if no errors are listed below.
- Public video player/direct source links were extracted from landing pages; playback and remote link availability were not tested.
- External links are provenance references. Access denials and partial coverage remain documented, not treated as validation failures.
- ZIP CRC integrity and packaged-file hashes are checked during packaging. SHA256SUMS.txt records the final files, excluding itself.

## Result

PASS — no broken internal links, missing source/image files, image hash mismatches or JSON/image-container errors detected.

The offline index and image-gallery scripts also passed JavaScript syntax checks.
