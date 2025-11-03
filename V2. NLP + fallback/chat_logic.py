# chat_logic.py
"""
This is the main logic file to be imported by test_chat.py
This version uses a "fallback" strategy for complex dates.
"""

import re
import dateparser
from dateparser.search import search_dates
from datetime import datetime

# --- !! SET TO TRUE TO SEE DEBUGGING !! ---
DEBUG = True
# -----------------------------------------------

# --- Entity Extraction Functions ---

def extract_event_type(text):
    text = text.lower()
    known_types = [
        "skateboard", "snowboard", "bmx", 
        "music festival", "film festival", "debate"
    ]
    
    found_types = []
    for event_type in known_types:
        if event_type in text:
            negation_match = re.search(r"(not|don't like|no)\s+(.{{0,10}})?{0}".format(re.escape(event_type)), text)
            if not negation_match:
                found_types.append(event_type)

    if len(found_types) == 1:
        return found_types[0]
    return None

def extract_contestant_count(text):
    text = text.lower()
    match = re.search(r"(\d+)\s*(contestants|participants|people|peple|entries|to compete|will compete)", text)
    if match:
        return int(match.group(1))
    
    match_num_only = re.search(r"^(\d+)$", text.strip())
    if match_num_only:
        return int(match_num_only.group(1))
    return None

def extract_scoring(text):
    text = text.lower()
    if DEBUG: print(f"\n[DEBUG SCORING] Received text: '{text}'")

    # Finds "judges" or "final say" *UNLESS* it's like "10 judges".
    has_judges_match = re.search(r"(judges|final say)", text)
    is_numeric_judges = re.search(r"\d+\s+judges", text)
    has_judges = bool(has_judges_match and not is_numeric_judges)
    has_audience = "audience" in text
    
    if DEBUG: print(f"[DEBUG SCORING] has_judges_match: {bool(has_judges_match)}")
    if DEBUG: print(f"[DEBUG SCORING] is_numeric_judges: {bool(is_numeric_judges)}")
    if DEBUG: print(f"[DEBUG SCORING] -> has_judges: {has_judges}")
    if DEBUG: print(f"[DEBUG SCORING] -> has_audience: {has_audience}")

    if (has_judges and has_audience) or "both" in text:
        if DEBUG: print("[DEBUG SCORING] -> Returning: 'both'\n")
        return "both"
    if has_judges:
        if DEBUG: print("[DEBUG SCORING] -> Returning: 'judges'\n")
        return "judges"
    if has_audience:
        if DEBUG: print("[DEBUG SCORING] -> Returning: 'audience'\n")
        return "audience"
        
    if DEBUG: print("[DEBUG SCORING] -> Returning: None\n")
    return None

# --- NEW FALLBACK FUNCTION ---
def extract_date_fallback(original_text, settings):
    """
    A fallback function to find complex relative dates.
    It looks for date keywords and searches a small window around them.
    """
    if DEBUG: print("[DEBUG DATE] -> Main search failed. Trying fallback...")
    
    text = original_text.lower()
    # Keywords that hint at a date but might be missed by the main parser
    date_keywords = [
        'christmas', 'easter', 'new year', 'weekend', 'saturday', 
        'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
        'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
    ]
    
    for keyword in date_keywords:
        if keyword in text:
            # Find the position of the keyword
            pos = text.find(keyword)
            
            # Extract a window of text (e.g., 30 chars before, 30 after)
            start = max(0, pos - 30)
            end = min(len(text), pos + 30)
            window = text[start:end]
            
            if DEBUG: print(f"[DEBUG DATE FALLBACK] Found keyword '{keyword}'. Searching window: '{window}'")
            
            search_results = search_dates(window, settings=settings)
            
            if search_results:
                if DEBUG: print(f"[DEBUG DATE FALLBACK] -> search_dates SUCCESS: {search_results}")
                return search_results[0][1] # Return the datetime object

    if DEBUG: print("[DEBUG DATE FALLBACK] -> Fallback failed.")
    return None

def extract_date(text):
    """
    Uses dateparser.search_dates.
    We aggressively clean the text of known "noise numbers"
    (like contestant counts) before passing to the parser.
    """
    if DEBUG: print(f"\n[DEBUG DATE] Received raw text: '{text}'")
    
    clean_text = text.lower()
    
    # 1. Remove contestant count phrases
    clean_text = re.sub(
        r"(\d+)\s*(contestants|participants|people|peple|entries|to compete|will compete)",
        " ", clean_text, flags=re.IGNORECASE
    )
    if DEBUG: print(f"[DEBUG DATE] After contestant clean: '{clean_text}'")
            
    # 2. Remove "X judges" phrases
    clean_text = re.sub(r"(\d+)\s+judges", " ", clean_text, flags=re.IGNORECASE)
    if DEBUG: print(f"[DEBUG DATE] After judges clean: '{clean_text}'")
    
    # 3. Define parser settings
    parser_settings = {
        'PREFER_DATES_FROM': 'future',
        # Get "now" from freezegun-patched datetime
        'RELATIVE_BASE': datetime.now() 
    }
    
    # 4. Now search the cleaned text
    search_results = search_dates(
        clean_text, 
        languages=['en'],
        settings=parser_settings
    )
    
    if DEBUG: print(f"[DEBUG DATE] search_dates result: {search_results}")
    
    if search_results:
        # Find the first date that isn't just a number
        for date_text, parsed_date in search_results:
            if DEBUG: print(f"[DEBUG DATE] Checking result: ('{date_text}', {parsed_date})")
            
            is_digit = date_text.strip().isdigit()
            if DEBUG: print(f"[DEBUG DATE] -> is_digit: {is_digit}")
            
            if not is_digit:
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                if DEBUG: print(f"[DEBUG DATE] -> Found valid date. Returning: {formatted_date}\n")
                return formatted_date
        
        if DEBUG: print("[DEBUG DATE] All results were digits. Trying fallback...")

    # --- FALLBACK LOGIC ---
    # If search_results was None or all were digits, try fallback
    
    # We pass the *original* text to the fallback
    fallback_date = extract_date_fallback(text, parser_settings)
    
    if fallback_date:
        formatted_date = fallback_date.strftime("%Y-%m-%d")
        if DEBUG: print(f"[DEBUG DATE] -> Fallback SUCCESS. Returning: {formatted_date}\n")
        return formatted_date

    if DEBUG: print("[DEBUG DATE] -> All methods failed. Returning None.\n")
    return None

# --- Main Chat Logic (for testing) ---

def update_details_and_get_feedback(text, event_details):
    # This is a simplified version for testing,
    # as we don't need the feedback messages.
    
    if event_details["event_type"] is None:
        event_details["event_type"] = extract_event_type(text)

    if event_details["contestant_count"] is None:
        event_details["contestant_count"] = extract_contestant_count(text)

    if event_details["scoring"] is None:
        event_details["scoring"] = extract_scoring(text)

    if event_details["date"] is None:
        event_details["date"] = extract_date(text)

def get_next_question(event_details):
    """Determines the next question to ask based on missing info."""
    if event_details["event_type"] is None:
        return "What type of event are you hosting? (e.g., skateboard, music festival)"
    if event_details["contestant_count"] is None:
        return "How many contestants will there be?"
    if event_details["scoring"] is None:
        return "How will scoring work? (judges, audience, or both)"
    if event_details["date"] is None:
        return "When is the event? (e.g., 'next Saturday', 'Dec 20th')"
    return None # All details are filled