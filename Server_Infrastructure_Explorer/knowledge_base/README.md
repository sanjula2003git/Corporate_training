# Local knowledge base · Server Infrastructure 5.1

Collected and reviewed on 8 September 2026. Covers all 13 lesson topics.

## Saved files

- `knowledge.json`: 54 searchable notes and 13 source records with URLs, review dates, collection timestamps and download status.
- `Collected_Knowledge.md`: readable notes organized by topic with source links.

Eight sources were downloaded directly, including one PDF. Five sources were readable through web lookup but did not provide usable content to the Python downloader. Those entries are marked `web_verified_fetch_unavailable`, not reported as successful scrapes. The downloaded HTML sources retain brief excerpts and checksums. PDF content was reviewed through web document extraction; the full PDF is not bundled.

The corpus consists of original, reviewed paraphrases and brief excerpts, not copied full articles. Source claims were selected conservatively: broad vendor claims that a form factor is always faster, cheaper or hot-swappable were not generalized. Manufacturer-specific configurations remain identified by model. This is a compact starting collection, not exhaustive server documentation.

## How chat uses it

`knowledge.py` reads the JSON and ranks notes by query terms, topic aliases and the selected lesson. It returns matching passages with source links. Explicitly naming another component permits cross-topic retrieval. Follow-up requests avoid notes already shown when possible. When there is no matching material, chat says so instead of inventing an answer.

Without an AI key, the chat displays retrieved notes; search itself does not generate new explanations or infer student preferences. With AI enabled, retrieved notes accompany the lesson and learner preferences in the model request, and the response includes links to retrieved sources. The Groq tutor needs a valid Groq API key. Its optional Compound web lookup requests fresh information for each question; live lookup results are used for that answer rather than automatically added to the reviewed corpus. Search and browsing the collection work offline.

## Review or refresh

From the app directory, run `python build_knowledge.py` with network access to recheck the fixed public source list and rebuild the files. The collector does not crawl arbitrary links, execute webpage scripts, bypass access blocks or send student chat to websites. It keeps original review dates: refreshing checks page availability; it does not automatically re-review or update the paraphrases. Review the sources and edit the notes in `build_knowledge.py` when content changes, then rebuild.

The app reads the JSON on each search, so updated notes become available on the next question. Use the sidebar’s **Collected web knowledge** to browse topics, search and download the data.
