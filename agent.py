"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    import re

    session = _new_session(query, wardrobe)

    # Step 2: Parse query for description, size, max_price
    # Extract size (XS/S/M/L/XL/XXL or number sizes like 8/10)
    size_match = re.search(r'\bsize\s+(\w+)\b|\b(XS|S|M|L|XL|XXL|[0-9]{1,2}W?)\b', query, re.IGNORECASE)
    size = size_match.group(1) or size_match.group(2) if size_match else None

    # Extract max price
    price_match = re.search(r'under\s+\$?(\d+\.?\d*)', query, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None

    # Description: strip out size/price phrases to get the core item description
    description = re.sub(r'(size\s+\w+|under\s+\$?\d+\.?\d*|i\'m looking for|looking for|find me|help me find)', '', query, flags=re.IGNORECASE).strip()
    description = re.sub(r'\s+', ' ', description).strip()

    session["parsed"] = {"description": description, "size": size, "max_price": max_price}

    # Step 3: Search listings
    results = search_listings(description, size=size, max_price=max_price)
    session["search_results"] = results

    if not results:
        size_str = f" in size {size}" if size else ""
        price_str = f" under ${max_price}" if max_price else ""
        session["error"] = (
            f"No listings found for '{description}'{size_str}{price_str}. "
            f"Try a broader description, a different size, or a higher budget."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit

    if outfit.startswith("Outfit suggestion unavailable"):
        session["error"] = outfit
        return session

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(outfit, session["selected_item"])

    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
