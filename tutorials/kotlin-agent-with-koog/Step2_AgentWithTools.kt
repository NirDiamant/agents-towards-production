import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.reflect.ToolSet
import ai.koog.agents.core.tools.reflect.asTools
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------
// A ToolSet is a class whose methods can be called by the LLM.
// Think of it like defining "functions" that an AI assistant can use.
//
// @Tool           -- marks a function as callable by the agent
// @LLMDescription -- tells the LLM what the function (or parameter) does,
//                    so it knows WHEN and HOW to call it
// ---------------------------------------------------------------------------

@LLMDescription("Tools for looking up weather, performing calculations, and retrieving facts")
class AssistantTools : ToolSet {

    @Tool
    @LLMDescription("Get the current weather for a given city. Returns temperature and conditions.")
    fun getWeather(@LLMDescription("City name, e.g. 'Tokyo'") city: String): String {
        // In a real app, this would call a weather API.
        // We use hardcoded data so the tutorial works without extra API keys.
        val data = mapOf(
            "tokyo" to "22C, partly cloudy",
            "london" to "14C, rainy",
            "new york" to "28C, sunny",
            "sydney" to "18C, clear skies",
        )
        return data[city.lowercase()] ?: "25C, clear (default forecast)"
    }

    @Tool
    @LLMDescription("Evaluate a basic arithmetic expression and return the numeric result.")
    fun calculate(@LLMDescription("Arithmetic expression, e.g. '144 / 12'") expression: String): String {
        val result = evaluateExpression(expression)
        return "$expression = $result"
    }

    @Tool
    @LLMDescription("Look up a factual piece of information about a topic.")
    fun lookupFact(@LLMDescription("Topic to look up, e.g. 'Kotlin'") topic: String): String {
        val facts = mapOf(
            "kotlin" to "Kotlin was created by JetBrains and first released in 2011. It became an official Android language in 2017.",
            "koog" to "Koog is an open-source AI agent framework by JetBrains for building LLM-powered agents in Kotlin.",
            "react pattern" to "ReAct (Reason + Act) is an agent pattern where the LLM reasons about a task, takes an action, observes the result, and repeats.",
        )
        return facts[topic.lowercase()] ?: "No specific fact found for '$topic'."
    }

    // Simple recursive expression evaluator for +, -, *, /
    private fun evaluateExpression(expr: String): Double {
        val sanitized = expr.replace(" ", "")
        return when {
            "+" in sanitized.drop(1) -> {
                val i = sanitized.indexOfLast { it == '+' }
                evaluateExpression(sanitized.substring(0, i)) + evaluateExpression(sanitized.substring(i + 1))
            }
            "-" in sanitized.drop(1) -> {
                val i = sanitized.indexOfLast { it == '-' }
                evaluateExpression(sanitized.substring(0, i)) - evaluateExpression(sanitized.substring(i + 1))
            }
            "*" in sanitized -> {
                val i = sanitized.indexOfFirst { it == '*' }
                evaluateExpression(sanitized.substring(0, i)) * evaluateExpression(sanitized.substring(i + 1))
            }
            "/" in sanitized -> {
                val i = sanitized.indexOfFirst { it == '/' }
                evaluateExpression(sanitized.substring(0, i)) / evaluateExpression(sanitized.substring(i + 1))
            }
            else -> sanitized.toDouble()
        }
    }
}

// ---------------------------------------------------------------------------
// Agent configuration and execution
// ---------------------------------------------------------------------------

suspend fun main() {
    val apiKey = System.getenv("OPENAI_API_KEY")
        ?: error("Set the OPENAI_API_KEY environment variable before running this example.")

    // Register the tools so the agent can discover and call them.
    // .asTools() converts the annotated ToolSet class into Koog's internal format.
    val toolRegistry = ToolRegistry {
        tools(AssistantTools().asTools())
    }

    simpleOpenAIExecutor(apiKey).use { executor ->
        val agent = AIAgent(
            promptExecutor = executor,
            llmModel = OpenAIModels.Chat.GPT5_4Mini,
            systemPrompt = """
                You are a helpful assistant with access to tools for weather, calculations, and fact lookup.
                When asked a question, use the appropriate tools to find the answer.
                Always use tools when they are relevant rather than guessing.
            """.trimIndent(),
            // Pass the tool registry -- without this, the agent has no tools.
            toolRegistry = toolRegistry,
        )

        // Ask a multi-part question that forces the agent to use all three tools.
        val question = "What is the weather in Tokyo, and what is 144 divided by 12? " +
            "Also, tell me an interesting fact about Kotlin."
        println("Question: $question\n")

        // The agent will automatically:
        //   1. Read the question
        //   2. Decide which tools to call (getWeather, calculate, lookupFact)
        //   3. Call each tool and read the results
        //   4. Compose a final answer from the tool outputs
        val response = agent.run(question)
        println("Agent response: $response")
    }
}
