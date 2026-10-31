import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.agent.config.AIAgentConfig
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.ext.agent.structuredOutputWithToolsStrategy
import ai.koog.prompt.dsl.prompt
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import ai.koog.prompt.executor.clients.openai.base.structure.OpenAIStandardJsonSchemaGenerator
import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor
import ai.koog.prompt.structure.StructuredRequest
import ai.koog.prompt.structure.StructuredRequestConfig
import ai.koog.prompt.structure.json.JsonStructure
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ---------------------------------------------------------------------------
// Data class that defines the SHAPE of the response we want from the LLM.
// ---------------------------------------------------------------------------
// Instead of getting free text like "Tokyo is the capital of Japan...",
// the LLM will return a JSON object that Koog deserializes into this class.
// You then access fields directly: analysis.city, analysis.populationMillions, etc.
//
// @Serializable       -- required by Kotlin serialization (handles JSON conversion)
// @SerialName("...")   -- the name sent to the LLM in the schema
// @LLMDescription      -- tells the LLM what each field means (on a class or property)
// @property:LLMDescription -- same, but the "property:" prefix is needed for
//                            data class constructor parameters (a Kotlin quirk)
// ---------------------------------------------------------------------------

@Serializable
@SerialName("CityAnalysis")
@LLMDescription("An analysis of a city covering key facts and livability")
data class CityAnalysis(
    @property:LLMDescription("Name of the city")
    val city: String,

    @property:LLMDescription("Country where the city is located")
    val country: String,

    @property:LLMDescription("Approximate population in millions")
    val populationMillions: Double,

    @property:LLMDescription("The city's primary language")
    val primaryLanguage: String,

    @property:LLMDescription("Three notable landmarks or attractions")
    val landmarks: List<String>,

    @property:LLMDescription("A short summary of the city's character in one or two sentences")
    val summary: String,
)

// ---------------------------------------------------------------------------
// Agent with a structured output strategy
// ---------------------------------------------------------------------------

suspend fun main() {
    val apiKey = System.getenv("OPENAI_API_KEY")
        ?: error("Set the OPENAI_API_KEY environment variable before running this example.")

    val agentConfig = AIAgentConfig(
        prompt = prompt("city-analyst") {
            system("You are a knowledgeable city analyst. When asked about a city, provide accurate structured data.")
        },
        model = OpenAIModels.Chat.GPT5_4,
        // Every node the strategy visits counts as one iteration; the structured output
        // strategy needs 6 even without tool calls, so 5 would be too few.
        maxAgentIterations = 10,
    )

    simpleOpenAIExecutor(apiKey).use { executor ->
        // structuredOutputWithToolsStrategy<CityAnalysis>() is a built-in Koog strategy
        // that lets the agent call tools in a loop and then finish with a structured
        // output of the specified type once the process is complete.
        // Its config says how to request the structure: Native sends a JSON schema generated
        // from CityAnalysis (in the format OpenAI accepts) through the model's structured output API.
        val agent = AIAgent(
            promptExecutor = executor,
            strategy = structuredOutputWithToolsStrategy<CityAnalysis>(
                StructuredRequestConfig(
                    default = StructuredRequest.Native(
                        JsonStructure.create<CityAnalysis>(schemaGenerator = OpenAIStandardJsonSchemaGenerator)
                    )
                )
            ),
            agentConfig = agentConfig,
        )

        // The return type is CityAnalysis -- a real Kotlin object, not a string.
        // No JSON parsing or regex extraction needed in your code.
        val analysis: CityAnalysis = agent.run("Tell me about Tokyo")

        // Access typed fields directly
        println("City: ${analysis.city}")
        println("Country: ${analysis.country}")
        println("Population: ${analysis.populationMillions}M")
        println("Language: ${analysis.primaryLanguage}")
        println("Landmarks: ${analysis.landmarks.joinToString(", ")}")
        println("Summary: ${analysis.summary}")
    }
}
