# Working notes

Scratch notes while building this — mostly things I noticed or want to check.

## Observations

- gpt-4o-mini wraps SQL in ```sql fences about half the time even when told
  not to. Handled in `generate_sql` by stripping them, feels hacky but works.
- The judge is strict about empty results. Sometimes an empty result IS the
  right answer (e.g. "bookings in Chennai" — we don't operate there). It
  burns a retry on those. Not sure yet if that's a bug or a feature.
- Keyword fallback in the router misfires on "Loads of bookings happened in
  Delhi" (sends it to ETL because of "Loads"). Funny, but the LLM router
  gets it right, so low priority.

## Questions I still have

- Is 2 retries the right number? More retries = slower answers.
- Should the ETL agent ask before overwriting a table? Probably yes for
  anything that already has data in it.

## Ideas

- Cache the schema info — it doesn't change between questions in a session.
- Try a local model via Ollama for the router only (it's a simple task,
  doesn't need a big model).
