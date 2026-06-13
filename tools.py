"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()
    keywords = [w.lower() for w in description.split() if len(w) > 2]

    results = []
    for item in listings:
        # Filter by price
        if max_price is not None and item.get("price", 0) > max_price:
            continue
        # Filter by size (case-insensitive)
        if size is not None:
            item_size = item.get("size", "").lower()
            if size.lower() not in item_size:
                continue

        # Score by keyword overlap across title, description, style_tags, category
        searchable = " ".join([
            item.get("title") or "",
            item.get("description") or "",
            item.get("category") or "",
            " ".join(item.get("style_tags") or []),
            item.get("brand") or "",
        ]).lower()

        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    try:
        client = _get_groq_client()
        wardrobe_items = wardrobe.get("items", [])

        if not wardrobe_items:
            prompt = f"""A user just thrifted this item:
- Title: {new_item.get('title')}
- Category: {new_item.get('category')}
- Style tags: {', '.join(new_item.get('style_tags', []))}
- Colors: {', '.join(new_item.get('colors', []))}
- Condition: {new_item.get('condition')}

They haven't shared their wardrobe. Give 1-2 general outfit suggestions — what kinds of pieces pair well with this item, what vibe it suits, and any specific styling tips."""
        else:
            wardrobe_lines = "\n".join(
                f"- {w.get('name', 'item')} [{w.get('category', '')}] — colors: {', '.join(w.get('colors') or [])} — tags: {', '.join(w.get('style_tags') or [])}"
                + (f" ({w['notes']})" if w.get('notes') else "")
                for w in wardrobe_items
            )
            prompt = f"""A user just thrifted this item:
- Title: {new_item.get('title')}
- Category: {new_item.get('category')}
- Style tags: {', '.join(new_item.get('style_tags', []))}
- Colors: {', '.join(new_item.get('colors', []))}
- Condition: {new_item.get('condition')}

Their current wardrobe includes:
{wardrobe_lines}

Suggest 1-2 complete outfits using the new item and specific pieces from their wardrobe. Include styling tips (how to wear it, what to tuck, layer, etc.)."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Outfit suggestion unavailable right now. ({e})"
   
# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "Can't generate a fit card without an outfit — something went wrong upstream."

    try:
        client = _get_groq_client()
        prompt = f"""Write a 2-3 sentence Instagram/TikTok caption for this thrifted outfit.

Item: {new_item.get('title')} — ${new_item.get('price')} from {new_item.get('platform')}
Outfit: {outfit}

Rules:
- Casual, authentic tone — like a real person posting their OOTD, not a product description
- Mention the item name, price, and platform naturally (once each)
- Capture the specific vibe of the outfit
- Can include 1-2 relevant emojis
- Do NOT use hashtags"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.95,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Fit card unavailable. Here's the outfit instead: {outfit}"