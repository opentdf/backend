/*
 * This file was generated by the Gradle 'init' task.
 *
 * This generated file contains a sample Kotlin library project to get you started.
 */

val keyCloakVersion by extra { "23.0.2" }


plugins {
    // Apply the Kotlin JVM plugin to add support for Kotlin on the JVM.
    id("org.jetbrains.kotlin.jvm").version("1.9.10")

    id ("com.github.johnrengelman.shadow").version("5.2.0")

}

repositories {
    // You can declare any Maven/Ivy/file repository here.
    mavenCentral()
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    kotlinOptions.jvmTarget = "11"
}

tasks.withType<JavaCompile> {
    options.compilerArgs.addAll(listOf("-source", "11", "-target",  "11"))
}

dependencies {
    // Here's where the X509 Certificate Lookup SPI is defined
    compileOnly("org.keycloak:keycloak-services:$keyCloakVersion")

    // And this is needed by all SPIs
    compileOnly("org.keycloak:keycloak-server-spi:$keyCloakVersion")
    compileOnly("org.keycloak:keycloak-server-spi-private:$keyCloakVersion")
    compileOnly("org.keycloak:keycloak-core:$keyCloakVersion")
    compileOnly("org.keycloak:keycloak-model-legacy-services:$keyCloakVersion")
    compileOnly("org.keycloak:keycloak-model-legacy:$keyCloakVersion")
    compileOnly("org.keycloak:keycloak-model-legacy-private:$keyCloakVersion")

    // Use the Kotlin JDK 8 standard library.
    implementation("org.jetbrains.kotlin:kotlin-stdlib")
}
