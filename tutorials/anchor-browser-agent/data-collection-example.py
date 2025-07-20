import os
import requests
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

def data_collection_example(connection_string):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connection_string)
        context = browser.contexts[0]
        target_url = "chrome-extension://bppehibnhionalpjigdjdilknbljaeai/background.js"
        ai = next((sw for sw in context.service_workers if sw.url == target_url), None)
        page = context.pages[0]

        page.goto(
            "https://play.grafana.org/a/grafana-k8s-app/navigation/nodes?from=now-1h&to=now&refresh=1m",
            wait_until="domcontentloaded"
        )
        result = ai.evaluate('Collect the node names and their CPU average %, return in JSON array')
        return result

if not ANCHOR_API_KEY:
    raise Exception("ANCHOR_API_KEY is not set, please run `export ANCHOR_API_KEY=<your-api-key>` and try again.")

session_data = create_session(ANCHOR_API_KEY)
print(session_data)
connection_string = session_data['data']['cdp_url']
result = data_collection_example(connection_string)
print(result)



