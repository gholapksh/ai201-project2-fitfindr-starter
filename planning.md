# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Tool 1 searches the mock listings dataset and returns items that match the user's description, size, and price, constraints. It scores matches by comparing the description against item titles, style tags, and category fields.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): A natural language description of the item the user wants(e.g. "vintage graphic tee", "oversized denim jacket")
- `size` (str or None): Clothing size to filter by (e.g.,"M","L","XS"). If None, size is not filtered.
- `max_price` (float or None): Maximum price in dollars. If None, no price ceiling is applied.


**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of dictionaries, where each dictionary is a listing with fields: id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Returns an empty list [] if no matches are found. Never raises an exception.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
The agent sets session["error"] to a message like: "No listings found for '[description]' in size[size] under $[max price]. Try a broader descriThe agent return immediately, it does not call suggest_outfit with an empty result.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a specific thrifted item and the user's current wardrobe, calls the Groq LLM to generate one or more complete outfit combinations using pieces the user already owns. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A single listing dict returned by search_listings (same fields: title, category, style_tags, colors, etc.)
- `wardrobe` (dict): The user's wardrobe in the schema defined by wardrobe_schema.json - contains an items list, each with fields like type, color, style, description

**What it returns:**
<!-- Describe the return value -->
A non-empty string containing outfit suggestion(s) with styling notes- e.g.,"Pair this faded band tee with your wide-leg jeans and chunky white sneakers for a 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape." Returns and error message string (not an exception) if the LLM call fails.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---
If wardrobe["items"] is empty, the LLM is still called but prompted for general styling advice: "No wardrobe items provided - here are general styling suggestions for this piece." If the LLM call throws an exception, returns: "Outfit suggestion unavailable right now. Try again in a moment."
### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given an outfit suggestion and the thrifted item, calls the Groq LLM to generate a short casual shareable caption - the kind someone would post on Instagram or TikTok with their outfit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string returned by suggest_outfit
- `new_item`(dict): The listing dict for the thrifted item (used for price, platform, title context)

**What it returns:**
<!-- Describe the return value -->
A short string (1-3 sentences, casual tone, may include an emoji) suitable as a social captikon. Each call should produce meaningfully different output. Returns an error message string if outfit is empty or the LLM call fails.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---
If outfit is an empty string, returns: "Can't generate a fit card without an outfit - something went wrong upstream." If the LLM call fails, returns: "Fit card unavailable. Here's the outfit suggestion instead: [outfit]"

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---
1. Call search_listings(description, size, max_price)
2. If results == []: set session["error] to the no-results message, set session["fit_card"] = None, return session immediately. Do not proceed.
3. If results is a non-empty: set session["selected_item"] = results[0] (top match).
4. Call suggest_outfit(session["selected_item"], wardrobe).
5. If the return value starts with "Outfit suggestions unavailable":set session["error"] to that message, return session. Do not proceed. 
6. Set session["outfit_suggestion"] to the return string.
7. Call create_fit_card(session["outfit_suggestion"], session["selected_item"])
8. Set session["fit_card] to the returned string
9. Return session

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---
All state lives in a session dictionary that is created at the start of run_agent() and passed through each step. Fields:
- session["query"] - the original user query string
- session["selected_item"] - the listing dict chosen from search results (set after step 1)
- session["outfit_suggestion"] - the string returned by suggest_outfit (see after step 2)
- session["fit_card"] - the caption string from create_fit_card (set after step 3)
- session["error"] - an error message string if any tool fails; None otherwise

No tool recieves the raw session dictionary - each tool gets only the specific values it needs, extracted from the session before the call. The session is what run_agent() returns to handle_query() in app.py.
## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool            | Failure mode | Agent response |
|-----------------|--------------|----------------|
| search_listings | No results match the query |Sets session["error"]: No listings found for '[description]' in size[size] under $[max_price]. Try broadening your descriptioin, adjusting the size, or raising your budget." Returns early - does not call subsequent tools.|
| suggest_outfit  | Wardrobe is empty |Calls LLM anyway with a prompt that says no wardrobe is available, asks for general styling advice for the item. Returns general suggestion as a suggestions as a string rather than failing.|
| create_fit_card | Outfit input is missing or incomplete |Returns the string: "Can't generate a fit card without an outfit - something went wrong upstream." Does not call the LLM.|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

User query (description, size, max_price, wardrobe)
    │
    ▼
Planning Loop (run_agent)
    │
    ├─► search_listings(description, size, max_price)
    │       │
    │       ├── results == [] ──► session["error"] = "No listings found..." ──► RETURN session
    │       │
    │       └── results non-empty
    │               │
    │           session["selected_item"] = results[0]
    │               │
    ├─► suggest_outfit(selected_item, wardrobe)
    │       │
    │       ├── LLM error ──► session["error"] = "Outfit suggestion unavailable..." ──► RETURN session
    │       │
    │       └── success
    │               │
    │           session["outfit_suggestion"] = "..."
    │               │
    └─► create_fit_card(outfit_suggestion, selected_item)
            │
            ├── outfit == "" ──► session["fit_card"] = "Can't generate fit card..."
            │
            └── success
                    │
                session["fit_card"] = "..."
                    │
                    ▼
              RETURN session

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
- search_listings: Give Claude the Tool 1 spec block above (inputs, return value, failure mode) plus the field list from listings.json. Ask it to implement search_listings() using load_listings() from utils/data_loader.py, filtering by size (exact match, skip if None), price (<=max_price, skip if None), and description (keyword match against title, description, style_tags). Verify the generated code handles all three filter conditions and returns [] on no match. Test with 3 queries: one that should returns [] on no match. Test with 3 queries: one that should return results, one with an impossible price, one with an impossible size.

- suggest_outfit: Give Claude the Tool 2 spec block and the wardrobe_schema.json structure. Ask it to implement suggest_outfit() calling Groq's llama-3.3-70b-versatile with a prompt that includes the item's title/style_tags/colors and the wardrobe items' type/color/style. Verify it handles empty wardrobe without crashing and that the LLM exception is caught.

- create_fit_card: Give Claude the Tool 3 spec block. Ask it to implement create_fit_card() with a prompt that asks for a casual 1-3 sentence Instagram-style caption using the item title, price, platform, and outfit description. Set temperature to 0.9+ to ensure output varies. Verify it guards against empty outfit string before calling the LLM.
**Milestone 4 — Planning loop and state management:**

--- c
Give Claude the full Architecture diagram above and the Planning Loop section. Ask it to implement run_agent(query, size, max_price, wardrobe) in agent.py following the numbered steps exactly - specifically that it brances on results == [] and does not call all three tools unconditionally. Verify the generate code: (1) checks results before proceeding, (2) stores values in the session dictionary at each step, (3) passes only the needed values into each tool call (not the whole session). Test the branch path by passing an impossible query and confirming session["fit_card"] is None.

## A Complete Interaction (Step by Step)

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent parses the query using regex to extract: description = "vintage graphic tee", size = None (no size specified), max_price = 30.0. It calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`. The function loads all 40 listings, filters out anything over $30, scores each remaining item by keyword overlap against "vintage", "graphic", "tee" across title, style_tags, category, and description fields. Returns a sorted list of matches. The agent sets `session["selected_item"] = results[0]` — the top result, e.g. "Y2K Baby Tee — Butterfly Print, $18, depop, size S/M, excellent condition."

**Step 2:**
The agent calls `suggest_outfit(session["selected_item"], wardrobe)`. The wardrobe has 10 items including baggy straight-leg jeans, chunky white sneakers, black combat boots, and a vintage denim jacket. The LLM receives a prompt with the item's style tags (y2k, vintage, graphic tee, cottagecore) and colors (white, pink, purple) alongside the wardrobe pieces. It returns two complete outfit suggestions referencing specific wardrobe items by name. The agent stores this in `session["outfit_suggestion"]`.

**Step 3:**
The agent calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])`. The LLM receives the outfit description plus item context (title, $18, depop) and generates a 2-3 sentence casual Instagram-style caption. Temperature is 0.95 so output varies each run. The result is stored in `session["fit_card"]`.

**Final output to user:**
Three panels populate in the Gradio UI:
- **🛍️ Top listing found:** "Y2K Baby Tee — Butterfly Print / Brand: None / Price: $18.0 / Platform: depop / Size: S/M / Condition: excellent / Colors: white, pink, purple / Style tags: y2k, vintage, graphic tee, cottagecore / Super cute early 2000s baby tee with butterfly graphic..."
- **👗 Outfit idea:** Two complete outfit suggestions using the user's actual wardrobe pieces — baggy jeans, chunky sneakers, combat boots, denim jacket — with specific styling tips.
- **✨ Your fit card:** A casual caption like "thrifted this y2k butterfly tee off depop for $18 and it was literally made for my baggy jeans 🦋 obsessed with this whole look"