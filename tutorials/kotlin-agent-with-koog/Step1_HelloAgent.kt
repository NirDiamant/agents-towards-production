import ai.koog.agents.core.agent.AIAgent
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor

// "suspend fun main()" is Kotlin's way of writing an async main function.
// If you come from Python, think of it like:  async def main()
// Koog agents run on coroutines, so the entry point must be suspendable.
suspend fun main() {

    // Read the API key from an environment variable.
    // The "?:" operator (called "Elvis") provides a fallback if the value is null.
    // In Python terms:  api_key = os.environ.get("OPENAI_API_KEY") or raise ...
    val apiKey = System.getenv("OPENAI_API_KEY")
        ?: error("Set the OPENAI_API_KEY environment variable before running this example.")

    // Create an executor -- the HTTP client that talks to OpenAI's API.
    // ".use { ... }" automatically closes the connection when the block finishes,
    // similar to Python's "with open(...) as f:" pattern.
    simpleOpenAIExecutor(apiKey).use { executor ->

        // Build the agent. At minimum, it needs:
        //   - an executor (how to reach the LLM)
        //   - a model (which LLM to use)
        //   - a system prompt (the agent's personality / instructions)
        val agent = AIAgent(
            promptExecutor = executor,
            llmModel = OpenAIModels.Chat.GPT5_4Mini,
            systemPrompt = "You are a concise assistant. Answer in one or two sentences.",
        )

        // Send a prompt and get a text response back.
        val response = agent.run("What makes Kotlin a good language for backend development?")
        println("Agent response: $response")
    }
}
