const { chromium } = require('playwright-core');
const axios = require('axios');

const ANCHOR_API_KEY = process.env.ANCHOR_API_KEY;

if (!ANCHOR_API_KEY) {
    console.error("❌ ANCHOR_API_KEY is not set. Run:");
    console.error("export ANCHOR_API_KEY=<your-api-key>");
    process.exit(1);
}

async function dataCollectionExample(connectionString = `wss://connect.anchorbrowser.io?apiKey=${ANCHOR_API_KEY}`) {
    const browser = await chromium.connectOverCDP(connectionString);
    const context = browser.contexts()[0];
    const ai = context.serviceWorkers()[0];
    const page = context.pages()[0];

    await page.goto(
        "https://play.grafana.org/a/grafana-k8s-app/navigation/nodes?from=now-1h&to=now&refresh=1m",
        { waitUntil: 'domcontentloaded' }
    );
    return await ai.evaluate('Collect the node names and their CPU average %, return in JSON array');
}

async function createSessionWithProfile(profileName = "my-profile") {
    const url = "https://api.anchorbrowser.io/v1/sessions";
    const payload = {
        browser: {
            profile: {
                name: profileName,
                persist: true
            }
        },
        session: {
            timeout: {
                max_duration: 4,
                idle_timeout: 2
            }
        }
    };
    const headers = {
        "anchor-api-key": ANCHOR_API_KEY,
        "Content-Type": "application/json"
    };

    try {
        const response = await axios.post(url, payload, { headers });
        return response.data;
    } catch (error) {
        if (error.response) {
            const { status, statusText, data } = error.response;
            if (status === 401) {
                console.error("❌ Authentication failed: Invalid or missing API key");
            } else {
                console.error(`❌ HTTP Error ${status}: ${statusText}`);
                console.error("Response data:", data);
            }
        } else if (error.request) {
            console.error("❌ Network error: No response from server");
        } else {
            console.error("❌ Error:", error.message);
        }
        process.exit(1);
    }
}

async function dataCollectionExampleWithProfile(profileName = "my-profile") {
    const sessionData = await createSessionWithProfile(profileName);
    const connectionString = sessionData.data.cdp_url;
    return await dataCollectionExample(connectionString);
}

(async () => {
    try {
        console.log("data_collection_example:");
        const result1 = await dataCollectionExample();
        console.log(result1);
        console.log("-".repeat(100));
        console.log("data_collection_example_with_profile:");
        const result2 = await dataCollectionExampleWithProfile("my-profile");
        console.log(result2);
    } catch (error) {
        console.error("❌ Runtime error:", error.message);
        console.log("Please check the data-collection guide for more troubleshooting.");
        process.exit(1);
    }
})();