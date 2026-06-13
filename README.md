# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Given a natural language query, FitFindr searches mock thrift listings, suggests outfits using the user's existing wardrobe, and generates a shareable fit card caption.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Run the app:
```bash
python app.py
```

Then open http://127.0.0.1:7860 in your browser.

---

## Tool Inventory

### `search_listings(description: str, size: str | None, max_price: float | None) → list[dict]`
Searches the mock listings dataset for items matching the user's description, optional size, and optional price ceiling. Loads all listings, filters by price and size, then scores each remaining item by keyword overlap across title, description, category, style_tags, and brand. Returns a list of matching listing dicts sorted by relevance score (highest first). Returns an empty list if nothing matches — never raises an exception.

Each returned dict contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`
Calls the Groq LLM (llama-3.3-70b-versatile) to suggest 1–2 complete outfit combinations. If the wardrobe has items, the prompt includes the user's actual pieces by name, category, colors, and style tags, and asks the LLM to build outfits using specific wardrobe pieces. If the wardrobe is empty, the prompt asks for general styling advice instead. Returns a non-empty string in both cases.

### `create_fit_card(outfit: str, new_item: dict) → str`
Calls the Groq LLM to generate a 2–3 sentence Instagram/TikTok-style caption for the outfit. The prompt includes the item name, price, platform, and outfit description, and instructs the LLM to write in a casual, authentic OOTD voice (no hashtags, no product-description tone). Temperature is set to 0.95 to ensure varied output across runs.

---

## How the Planning Loop Works

The planning loop in `run_agent()` follows this conditional logic — it does not call all three tools unconditionally:

1. Parse the user's query with regex to extract a description (core item keywords), size (e.g. "M", "size 8"), and max price (e.g. "under $30").
2. Call `search_listings()` with the parsed parameters.
3. **Branch:** If results is empty, set `session["error"]` to a descriptive message and return immediately. `suggest_outfit` and `create_fit_card` are never called.
4. If results are found, set `session["selected_item"] = results[0]` (top match by relevance score).
5. Call `suggest_outfit()` with the selected item and the user's wardrobe.
6. If the outfit suggestion starts with "Outfit suggestion unavailable", set `session["error"]` and return early.
7. Call `create_fit_card()` with the outfit suggestion and selected item.
8. Return the completed session.

---

## State Management

All state lives in a single `session` dict created at the start of `run_agent()` and passed through each step. No tool receives the full session — each gets only the specific values it needs.

| Key | Set when | Used by |
|-----|----------|---------|
| `session["query"]` | Start | Logging/display |
| `session["parsed"]` | After query parsing | Passed into search_listings |
| `session["search_results"]` | After search_listings | Branch check |
| `session["selected_item"]` | After branch check | suggest_outfit, create_fit_card |
| `session["outfit_suggestion"]` | After suggest_outfit | create_fit_card |
| `session["fit_card"]` | After create_fit_card | Returned to UI |
| `session["error"]` | On any early exit | Returned to UI |

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match query | Sets `session["error"]`: "No listings found for '[description]' in size [size] under $[price]. Try a broader description, a different size, or a higher budget." Returns immediately — does not call subsequent tools. Example tested: "designer ballgown size XXS under $5" → returned error message, fit_card stayed None. |
| `suggest_outfit` | Wardrobe is empty | Still calls the LLM with a prompt asking for general styling advice. Returns a non-empty string with outfit ideas that don't reference specific wardrobe pieces. Never crashes or returns empty string. |
| `create_fit_card` | outfit string is empty | Guards before calling LLM: returns "Can't generate a fit card without an outfit — something went wrong upstream." No LLM call is made. |

---

## Spec Reflection

**One way the spec helped:** Writing the planning loop in plain conditional logic in `planning.md` before touching `agent.py` made the branching structure clear before any code existed. The spec said "if results is empty, return early" — which translated directly into the if-not-results block in `run_agent()`.

**One way implementation diverged:** The spec assumed wardrobe items would have `type`, `description`, and `style` fields based on the schema preview. The actual `wardrobe_schema.json` uses `name`, `category`, and `style_tags` instead. The `suggest_outfit` prompt had to be rewritten after discovering this at runtime — the planning.md field assumptions were wrong.

---

## AI Usage

**Instance 1 — search_listings implementation:** I gave Claude the Tool 1 spec block from planning.md (inputs, return value, failure mode, field list) and asked it to implement `search_listings()` using `load_listings()`. The generated code used `item.get("brand", "")` for all fields, which failed at runtime because some listings have explicit `null` values for brand that override the default. I overrode the fix to use `item.get("brand") or ""` instead, which handles None correctly.

**Instance 2 — planning loop implementation:** I gave Claude the full agent diagram and Planning Loop section from planning.md and asked it to implement `run_agent()`. The generated code correctly branched on empty results and stored values in the session dict. I verified it did not call all three tools unconditionally before using it, then tested the no-results branch manually with the ballgown query.