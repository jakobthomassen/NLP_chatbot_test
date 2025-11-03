# Old chat logic.

import re
import dateparser
from dateparser.search import search_dates # <-- New import
from datetime import datetime

# --- !! SET TO TRUE TO SEE DATE DEBUGGING !! ---
DEBUG = True

# Entity Extraction Functions

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
    has_judges = "judges" in text or "final say" in text
    has_audience = "audience" in text

    if (has_judges and has_audience) or "both" in text:
        return "both"
    if has_judges:
        return "judges"
    if has_audience:
        return "audience"
    return None

def extract_date(text):
    """
    Uses dateparser.search.search_dates to find dates inside
    a string containing other "noise" text.
    """
    if DEBUG: print(f"\n[DEBUG DATE] Received raw text: '{text}'")
    
    # Clean contestant count to not confuse dateparser.
    text_for_date = re.sub(r"(\d+)\s*(contestants|participants|people|peple|entries|to compete|will compete)",
                         " ", text.lower(), flags=re.IGNORECASE)
    
    if DEBUG: print(f"[DEBUG DATE] Cleaned text for search: '{text_for_date}'")

    # Use search_dates to find dates in text.
    search_results = search_dates(text_for_date, settings={'PREFER_DATES_FROM': 'future'})
    
    if DEBUG: print(f"[DEBUG DATE] dateparser.search_dates result: {search_results}")
    
    if search_results:
        # Get the first match
        parsed_date = search_results[0][1] 
        formatted_date = parsed_date.strftime("%Y-%m-%d")
        
        if DEBUG: print(f"[DEBUG DATE] Found date: '{search_results[0][0]}' -> {formatted_date}\n")
        return formatted_date
        
    if DEBUG: print("[DEBUG DATE] Returning None\n")
    return None

# Main Chat Logic

def update_details_and_get_feedback(text, event_details):
    """
    Attempts to fill slots and returns a list of *newly added* confirmations.
    """
    feedback_messages = []
    
    # Check each piece of missing info
    if event_details["event_type"] is None:
        event_type = extract_event_type(text)
        if event_type:
            event_details["event_type"] = event_type
            feedback_messages.append(f"Okay, a **{event_type}** event. Got it.")

    if event_details["contestant_count"] is None:
        count = extract_contestant_count(text)
        if count:
            event_details["contestant_count"] = count
            feedback_messages.append(f"**{count}** contestants. Check.")

    if event_details["scoring"] is None:
        scoring = extract_scoring(text)
        if scoring:
            event_details["scoring"] = scoring
            feedback_messages.append(f"Scoring by **{scoring}**. Noted.")

    if event_details["date"] is None:
        date = extract_date(text)
        if date:
            event_details["date"] = date
            feedback_messages.append(f"Set for **{date}**. Great.")
            
    return feedback_messages

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

def run_chat():
    """Main function to run the console chat."""
    
    event_details = {
        "event_type": None,
        "contestant_count": None,
        "scoring": None,
        "date": None
    }
    
    print("Chat: Hello! I'm here to help you set up your event.")
    print("Chat: You can tell me all the details at once, or I can ask you.")
    
    while True:
        next_question = get_next_question(event_details)
        
        if next_question is None:
            break
            
        if event_details != {k: None for k in event_details}:
             print(f"Chat: {next_question}")

        user_input = input("You: ")
        
        if not user_input:
            continue

        feedback = update_details_and_get_feedback(user_input, event_details)
        
        if feedback:
            for msg in feedback:
                print(f"Chat: {msg.replace('**', '')}")
        elif next_question:
            print("Chat: Sorry, I didn't quite catch that.")

    # --- Verification Step ---
    print("\n--- Event Summary ---")
    print(f"Event Type:        {event_details['event_type']}")
    print(f"Contestant Count:  {event_details['contestant_count']}")
    print(f"Scoring Method:    {event_details['scoring']}")
    print(f"Date:              {event_details['date']}")
    print("----------------------")
    
    while True:
        print("Chat: Does this look correct? (yes / no / edit)")
        confirm = input("You: ").lower().strip()
        
        if confirm == "yes":
            print("Chat: Great! Your event has been registered.")
            break
        elif confirm in ["no", "edit"]:
            print("Chat: Okay, let's start over.")
            run_chat() # Restart
            break
        else:
            print("Chat: Please answer 'yes' or 'no'.")

if __name__ == "__main__":
    run_chat()