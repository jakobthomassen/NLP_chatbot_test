# chat_logic.py
"""
This is the main logic file to be imported by test_chat.py
Uses spaCy (to find) + parse() (for absolute) + search_dates() (for relative)
"""

import re
import dateparser
from dateparser.search import search_dates 
import spacy # https://spacy.io/
from datetime import datetime

# --- !! SET TO TRUE TO SEE DEBUGGING !! ---
DEBUG = True
# -----------------------------------------------

# --- Load NLP Model ---
try:
    nlp = spacy.load("en_core_web_sm")
    if DEBUG: print("[INFO] spaCy model 'en_core_web_sm' loaded.")
except IOError:
    print("\n--- ERROR ---")
    print("spaCy model 'en_core_web_sm' not found.")
    print("Please run: python -m spacy download en_core_web_sm")
    print("-------------\n")
    exit()
# ----------------------


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

def extract_date(text):
    """
    Uses spaCy for NER to find the *text* of a date,
    then tries parse() and search_dates() to parse it.
    """
    if DEBUG: print(f"\n[DEBUG DATE] Received raw text: '{text}'")
    
    doc = nlp(text)
    if DEBUG: print(f"[DEBUG DATE] spaCy Entities found: {[(ent.text, ent.label_) for ent in doc.ents]}")

    frozen_now = datetime.now()
    if DEBUG: print(f"[DEBUG DATE] Relative base (frozen time): {frozen_now}")

    # Define settings once
    parser_settings = {
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': frozen_now
    }

    for ent in doc.ents:
        if ent.label_ == "DATE":
            date_text = ent.text
            if DEBUG: print(f"[DEBUG DATE] Found 'DATE' entity: '{date_text}'")
            
            # --- THIS IS THE FIX ---
            # Strategy 1: Try dateparser.parse()
            # This is good for absolute dates (e.g., "Dec 10th")
            parsed_date = dateparser.parse(date_text, settings=parser_settings)
            
            if parsed_date:
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                if DEBUG: print(f"[DEBUG DATE] -> parse() SUCCESS. Returning: {formatted_date}\n")
                return formatted_date

            # Strategy 2: Fallback to dateparser.search_dates()
            # This is good for relative dates (e.g., "next saturday")
            if DEBUG: print(f"[DEBUG DATE] -> parse() failed. Trying search_dates()...")
            search_results = search_dates(date_text, settings=parser_settings)
            
            if DEBUG: print(f"[DEBUG DATE] -> search_dates() result: {search_results}")

            if search_results:
                parsed_date = search_results[0][1] # Get the datetime object
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                if DEBUG: print(f"[DEBUG DATE] -> search_dates() SUCCESS. Returning: {formatted_date}\n")
                return formatted_date
            
            if DEBUG: print(f"[DEBUG DATE] -> All parsers FAILED for '{date_text}'")
    
    if DEBUG: print("[DEBUG DATE] No 'DATE' entity found or parsed. Returning None.\n")
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
        return "When is the event? (e.allg., 'next Saturday', 'Dec 20th')"
    return None # All details are filled