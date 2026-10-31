plugins {
    kotlin("jvm") version "2.3.10"
    kotlin("plugin.serialization") version "2.3.10"
}

repositories {
    mavenCentral()
}

dependencies {
    // Koog AI agent framework by JetBrains
    implementation("ai.koog:koog-agents:0.8.0")

    // Kotlin coroutines (required for suspend-based agent execution)
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.1")

    // Kotlin serialization (required for structured output and tool definitions)
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.10.0")

    // SLF4J no-op logger to suppress logging noise in tutorial output
    implementation("org.slf4j:slf4j-nop:2.0.16")
}

// Allow running each step file individually:
//   ./gradlew step1  ->  runs Step1_HelloAgent.kt
//   ./gradlew step2  ->  runs Step2_AgentWithTools.kt
//   ./gradlew step3  ->  runs Step3_StructuredOutput.kt

tasks.register<JavaExec>("step1") {
    group = "tutorial"
    description = "Run Step 1: Hello Agent"
    mainClass.set("Step1_HelloAgentKt")
    classpath = sourceSets["main"].runtimeClasspath
}

tasks.register<JavaExec>("step2") {
    group = "tutorial"
    description = "Run Step 2: Agent with Tools"
    mainClass.set("Step2_AgentWithToolsKt")
    classpath = sourceSets["main"].runtimeClasspath
}

tasks.register<JavaExec>("step3") {
    group = "tutorial"
    description = "Run Step 3: Structured Output"
    mainClass.set("Step3_StructuredOutputKt")
    classpath = sourceSets["main"].runtimeClasspath
}

// Place Kotlin source files at the tutorial root instead of src/main/kotlin
sourceSets {
    main {
        kotlin {
            setSrcDirs(listOf("."))
        }
    }
}

kotlin {
    jvmToolchain(17)
}
