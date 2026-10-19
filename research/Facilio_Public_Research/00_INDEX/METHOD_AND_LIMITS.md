# Method, provenance and limits

Research date: **17 October 2026** (user timezone Asia/Qatar). Individual retrieval timestamps are UTC. Source publication/update dates are retained when explicitly exposed. HTTP Last-Modified describes server metadata and is not treated as publication date.

## Acquisition boundary

- Official Facilio Help and developer sitemaps, their public navigation links, selected official product/platform/AI/release pages, the public video library and its linked landing pages.
- Ordinary unauthenticated HTTP reads only. No accounts, form submissions, invitations, trial signup, tenant browsing, API calls, CLI installation, network interception or application binaries.
- A descriptive research user agent was used. Robots files were retrieved before collection for each downloaded host. The collector conservatively applied the union of all listed Disallow rules, even bot-specific exclusions; it did not switch identities to use an Allow rule.
- Authentication, access denial, inaccessible robots files and excluded paths were not worked around. Cross-host redirects were not automatically followed. Responses exceeding the collector’s 16 MB per-item limit would be logged as failures.
- Documentation/category paths excluded by the conservative robots policy were not collected by the crawler. Direct article URLs already exposed by public sitemaps/navigation were collected when independently allowed. No excluded category content was used to reconstruct a hidden page.
- The public Swagger shell links a static OpenAPI YAML file. The static host returned 403 for robots.txt; the file remains a **link-only, unverified reference**. No specification endpoint inventory is claimed.
- Embedded videos are represented by their public landing page, date/duration metadata and player/direct-media links. Video binaries and full transcripts are not packaged. Playback was not verified.

The crawler used bounded concurrency, request spacing, caching and no automatic retries of access denials. Normal URL encoding repaired malformed links containing spaces; these were transport formatting corrections, not alternate routes around restrictions. Original errors remain in the access log, with subsequent successful captures separately recorded.

## What is in the folder

**RESEARCH.md files** are reviewed topic syntheses. **Source capsules** form the broad catalog: selected high-value sources contain reviewed paraphrases; the remaining capsules transparently identify automatically generated scope summaries and topic cues. The broad catalog should not be mistaken for hundreds of individually hand-validated workflow analyses.

Every capsule retains the source URL, title, UTC retrieval time, exposed source date/version, response hash and local image relationships through the manifests. Clean prose summaries replace copied page bodies. The folder contains no scraped raw page HTML or reproduced full documentation. GALLERY.html is an original offline browsing aid.

Image files are original publicly embedded UI references, including screenshots, diagrams, illustrations and animations. The gallery’s topic association comes from source-page context. It is not a verified pixel-level classification of every image. A representative set was visually inspected; their exact entries appear in VISUAL_QA.md. Third-party-hosted image references may remain link-only.

## Deduplication

URL fragments are removed. Exact duplicate extracted article bodies share one capsule with URL aliases. The classic video library also presents the same clip under different tour navigation paths; pages sharing the same public clip identifier share a source capsule, with that deduplication basis labeled separately. Alias titles, retrieval dates and available source dates are retained in URL_ALIASES.json. Identical image bytes share one file using a SHA-256 filename, even if different original URLs refer to them. Distinct versions and non-identical images remain separate. Similar titles do not justify merging different workflows, such as general maintenance and field-service work orders.

SOURCE_MANIFEST records response hashes for provenance, not retained raw HTML. IMAGE_MANIFEST records image hashes and source associations. ACCESS_LOG includes attempted reads and errors; EXCLUSIONS_AND_FAILURES lists non-200/skipped events. Earlier failures may have later successful equivalents. Browser-search discovery is not an additional exhaustive crawl log.

## Evidence interpretation

- **Documentation:** what an official guide says or illustrates. It does not establish runtime behavior, tenant availability or implementation quality.
- **Marketing/demo landing page:** vendor positioning and illustrated scenarios. Performance, autonomy and security claims are not independently validated.
- **Release note:** date-specific change evidence. It may supersede an older screenshot but does not prove that all editions expose the change.
- **Atlas opportunity:** an independent design hypothesis. Public Atlas documentation informs the baseline; your version and code were not inspected.

The collection is broad within the enumerated public sources, not a claim to mirror every Facilio property or every historical UI. Unknowns include full contract/invoice administration UX, exact current API schemas, edition licensing, live mobile synchronization, production performance and the current configuration of any customer tenant.

Public screenshots and source pages retain their respective owners’ rights. Use them for reference and independent product analysis; this archive provides no license to redistribute vendor assets inside an Atlas product. Do not reproduce vendor prose, artwork, trademarks or proprietary code when implementing your own design.
