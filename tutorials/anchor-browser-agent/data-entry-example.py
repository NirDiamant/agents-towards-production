import os
import requests
import json
from playwright.sync_api import sync_playwright

ANCHOR_API_KEY = os.getenv("ANCHOR_API_KEY")

# Create a session
def create_session(ANCHOR_API_KEY):
    url = "https://api.anchorbrowser.io/v1/sessions"

    payload = {
        "session": {
            "timeout": {                # Reduced timeouts for cost-effective learning
                "max_duration": 4,
                "idle_timeout": 2
            }
        }
    }
    headers = {
        "anchor-api-key": ANCHOR_API_KEY,
        "Content-Type": "application/json"
    }

    # Initialize session
    response = requests.request("POST", url, json=payload, headers=headers)

    # Make sure to keep the cdpUrl for the next step
    session_data = response.json()
    return session_data

def execute_form_submission(connection_string):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connection_string)
        context = browser.contexts[0]
        ai = context.service_workers[0]
        page = context.pages[0]
        # Navigate to resume
        page.goto('https://www.wix.com/demone2/nicol-rider')
        # Execute AI task
        task_payload = {
            "prompt": "Read the resume, understand the details, and complete the form at https://formspree.io/library/donation/charity-donation-form/preview.html as if you were her. Limit the donation to $10.",
            "provider": "openai",
            "model": "gpt-4",
            "highlight_elements": True
        }
        result = ai.evaluate(json.dumps(task_payload))
        print("Task result:", result)
        browser.close()
        return result


if not ANCHOR_API_KEY:
    raise Exception("ANCHOR_API_KEY is not set, please run `export ANCHOR_API_KEY=<your-api-key>` and try again.")

session_data = create_session(ANCHOR_API_KEY)
print(session_data)
connection_string = session_data['data']['cdp_url']
result = execute_form_submission(connection_string)
print(result)