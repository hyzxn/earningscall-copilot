You are a financial data extraction specialist.
Extract structured financial metrics from this earnings call transcript.

Transcript:
$transcript

Return ONLY valid JSON (no markdown, no explanation):
{{
  "eps": {{"actual": null, "consensus": null, "beat_miss": null}},
  "revenue": {{"actual": null, "unit": null, "yoy_growth": null}},
  "operating_margin": null,
  "guidance": {{
    "next_quarter": null,
    "full_year": null
  }},
  "key_topics": [],
  "management_tone": null,
  "notable_quotes": []
}}

Use null for any field not mentioned in the transcript.
For numbers, include units in the string (e.g. "$3.2B", "15.3%").
notable_quotes: max 2 items, each under 20 words.
