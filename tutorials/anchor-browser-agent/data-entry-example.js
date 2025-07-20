const { chromium } = require('playwright-core');
const axios = require('axios');

const ANCHOR_API_KEY = process.env.ANCHOR_API_KEY;

if (!ANCHOR_API_KEY) {
    console.error("❌ ANCHOR_API_KEY is not set. Run:");
    console.error("export ANCHOR_API_KEY=<your-api-key>");
    process.exit(1);
}

async function createSession(ANCHOR_API_KEY) {
    const url = "https://api.anchorbrowser.io/v1/sessions";
    const payload = {
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
        // Initialize session
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


async function executeFormSubmission(connectionString) {
    const browser = await chromium.connectOverCDP(connectionString);
    const context = browser.contexts()[0];
    const ai = context.serviceWorkers()[0];
    const page = context.pages()[0];
    
    // Navigate to resume
    await page.goto('https://www.wix.com/demone2/nicol-rider');
    
    // Execute AI task
    const taskPayload = {
        "prompt": "Read the resume, understand the details, and complete the form at https://formspree.io/library/donation/charity-donation-form/preview.html as if you were her. Limit the donation to $10.",
        "provider": "openai",
        "model": "gpt-4",
        "highlight_elements": true
    };
    
    const result = await ai.evaluate(JSON.stringify(taskPayload));
    console.log("Task result:", result);
    await browser.close();
    return result;
}

(async () => {
    try {
        const sessionData = await createSession(ANCHOR_API_KEY);
        console.log(sessionData);
        const connectionString = sessionData.data.cdp_url;
        const result = await executeFormSubmission(connectionString);
        console.log(result);
        process.exit(0);
    } catch (error) {
        console.error("Error:", error.message);
        process.exit(1);
    }
})(); 