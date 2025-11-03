# test_chat.py
# This master script prompts the user to select which test to run.

import os
import sys
import importlib.util
from freezegun import freeze_time

# --- TEST CASES ---
test_prompts = [
    # --- Original 10 ---
    # 1. Standard case
    "I think i want to host a skateboard event next saturday, not snowboard. i dont like snowboard. 12 peple will compete and judges should have final say.",
    # 2. The difficult relative date case
    "I'm running a music festival with 20 contestants on the weekend before christmas. We should use both judges and the audience for scoring.",
    # 3. Date first, different count keyword
    "On Dec 10th, 50 people will join a debate. Only the audience will score.",
    # 4. Different date phrasing, "entries"
    "My snowboard competition is one week into next month. 25 entries. Judges score.",
    # 5. Short, fragmented
    "bmx event. 10 participants. audience and judges. this tuesday.",
    # 6. Messy order and phrasing
    "Judges get final say. 15 peple. Skateboard. The day after tomorrow.",
    # 7. "both" implied, different date
    "I want the audience score and the judges score to count. 30 contestants for debate. tomorrow.",
    # 8. The "noise number" case
    "I need 10 judges for my snowboard event on the 12th of December. 20 contestants will be there. Audience scores.",
    # 9. More complex date
    "film festival, 40 people, judges, January 1st 2026.",
    # 10. A "known fail" to prove the test works (missing info)
    "A film festival with 100 people.",

    # --- New 20 ---
    # 11. Simple & Direct
    "I'm holding a film festival on March 18th. 80 entries. Judges score.",
    # 12. Simple & Direct
    "We need to set up a bmx event for 15 contestants. Audience scores. Next Friday.",
    # 13. Simple & Direct
    "A debate, this Sunday, 40 people. Both will score.",
    # 14. Simple & Direct
    "Music festival, 100 participants, judges and audience, in two weeks.",
    # 15. Simple & Direct
    "Skateboard comp, 22 contestants, audience scoring, August 1st.",
    
    # 16. Complex & Noisy (with negation)
    "Okay, let's do a snowboard competition. Not a bmx one. It'll be on Feb 2nd. 30 people will compete and the judges get the final say.",
    # 17. Complex & Noisy (large numbers)
    "I want to host a music festival with 250 contestants. We need to book it for the first weekend of July. The audience and judges will both have a say.",
    # 18. Complex & Noisy (negation)
    "My film festival is set for the 10th. I expect 60 entries. Just use audience scores, I don't want judges for this one.",
    # 19. Relative Date
    "The debate is in three days. We have 12 participants. I think both scoring methods would be best.",
    # 20. Complex Relative Date
    "Can you set up a skateboard event for 18 contestants? The date is the day before Halloween. Judges will decide the winner.",
    
    # 21. Holiday Date
    "We're running a bmx event. 40 entries. I was thinking it should be on Christmas day, as a special event. Let the audience vote.",
    # 22. Noise Number
    "A film festival for 50 people. Not 100. Let's do it on the 3rd of January. Scoring will be by judges.",
    # 23. Relative Date
    "I have 14 people competing in a debate. We need to schedule it for 2 weeks from tomorrow. The audience and judges should score.",
    # 24. Vague Relative Date
    "Hello, I need a music festival, 75 contestants. Judges have the final say. The date is in 5 weeks.",
    # 25. Date Phrasing
    "A snowboard event, please. 33 people will be there. Let's do it next month, on the 15th. Audience scores.",
    
    # 26. Tricky Edge Case (Noise number vs. scoring)
    "I need 5 judges for 50 contestants at my film festival on January 1st. Audience scores, not judges.",
    # 27. Tricky Edge Case (Multiple contestant numbers)
    "The event is a debate on the 30th. I have 10 people confirmed, but I expect 20. Let's say 20 contestants. Both score.",
    # 28. Tricky Edge Case (Complex relative date)
    "Skateboard event. 16 entries. Audience and judges. Not next Monday, but the Monday after.",
    # 29. Vague Relative Date
    "Music festival. 100 contestants. Audience vote. I need this set up before the end of next month.",
    # 30. Date First (with noise)
    "On the 8th, a bmx comp. 24 contestants. It's not a film festival. Judges and audience score.",
]

def load_module_from_path(folder_path, version_name):
    """
    Dynamically loads the 'chat_logic.py' module from a given folder.
    """
    file_path = os.path.join(folder_path, "chat_logic.py")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: 'chat_logic.py' not found in folder '{folder_path}'")
        
    # Create a unique module name to avoid import cache conflicts
    module_name = f"chat_logic_{version_name.replace(' ', '_').replace('+', '').lower()}"
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not create import spec for {file_path}")
        
    chat_module = importlib.util.module_from_spec(spec)
    
    spec.loader.exec_module(chat_module)
    
    return chat_module


# Freeze time to match debug output
@freeze_time("2025-10-29")
def run_tests(chat_module, version_name):
    """
    Runs the full test suite using the provided (dynamically loaded) module.
    """
    print(f"\n--- 🧪 Starting Test for: {version_name} ---")
    failures = []
    
    # Turn off debug spam for the test run summary
    if hasattr(chat_module, 'DEBUG'):
        chat_module.DEBUG = False 

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nRunning test case {i}...")
        
        # Reset event details for each test
        event_details = {
            "event_type": None,
            "contestant_count": None,
            "scoring": None,
            "date": None
        }

        # Run the extraction logic from the loaded module
        chat_module.update_details_and_get_feedback(prompt, event_details)
        
        # Check if the bot would ask another question
        next_question = chat_module.get_next_question(event_details)
        
        if next_question is None:
            # All details were filled
            print(f"✅ PASS: All info extracted.")
            print(f"   -> {event_details}")
        else:
            # Bot would have asked a question, meaning info was missed
            print(f"❌ FAIL: Bot would ask a follow-up question.")
            fail_data = {
                "case_index": i,
                "prompt": prompt,
                "first_missing_info": next_question,
                "final_state": event_details.copy()
            }
            failures.append(fail_data)
            print(f"   -> MISSING: {next_question}")

    # --- Summary ---
    print("\n\n--- 📈 Test Summary for: {version_name} ---")
    if not failures:
        print("✅ All test cases passed!")
    else:
        print(f"❌ Failed {len(failures)} out of {len(test_prompts)} cases.")
        print("\n--- Failure Details ---")
        for fail in failures:
            print(f"\nCase {fail['case_index']}: {fail['prompt']}")
            print(f"  -> First question asked: '{fail['first_missing_info']}'")
            print(f"  -> Final State: {fail['final_state']}")
    print("-" * 50)


def main():
    """
    Main menu to prompt the user for which version to test.
    """
    # Define the versions based on folder structure
    versions = {
        "1": ("V1. NLP", "V1. NLP (Simple Regex)"),
        "2": ("V2. NLP + fallback", "V2. NLP + Fallback"),
        "3": ("V3. NLP + spacy", "V3. NLP + spaCy (V13 Hybrid)"),
    }

    while True:
        print("\n--- Chatbot Test Harness ---")
        print("Select the logic version to test:")
        print(" 1. V1. NLP (Simple Regex)")
        print(" 2. V2. NLP + Fallback")
        print(" 3. V3. NLP + spaCy")
        print(" q. Quit")
        
        choice = input("Enter your choice (1, 2, 3, q): ").strip()
        
        if choice in ['q', 'Q']:
            print("Exiting.")
            break
            
        if choice in versions:
            folder_path, version_name = versions[choice]
            try:
                print(f"Loading module from '{folder_path}'...")
                # Dynamically load the chat_logic.py from that folder
                chat_module = load_module_from_path(folder_path, version_name)
                
                # Run the tests
                run_tests(chat_module, version_name)
                
            except Exception as e:
                print(f"\n--- ‼ ERROR ‼ ---")
                print(f"An error occurred while loading or testing {version_name}:")
                print(f"{e}")
                print("Please check the folder path and required dependencies (e.g., 'pip install spacy').")
                print("-" * 50)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()