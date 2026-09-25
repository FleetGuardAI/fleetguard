import org.jetbrains.kotlin.gradle.dsl.JvmTarget

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    afterEvaluate {
        project.extensions.findByName("android")?.let { android ->
            try {
                val getNamespace = android.javaClass.getMethod("getNamespace")
                val namespace = getNamespace.invoke(android)
                if (namespace == null) {
                    val setNamespace = android.javaClass.getMethod("setNamespace", String::class.java)
                    setNamespace.invoke(android, project.group.toString())
                }
            } catch (e: Exception) { }

            try {
                val compileOptions = android.javaClass.getMethod("getCompileOptions").invoke(android)
                compileOptions.javaClass.getMethod("setSourceCompatibility", org.gradle.api.JavaVersion::class.java).invoke(compileOptions, org.gradle.api.JavaVersion.VERSION_17)
                compileOptions.javaClass.getMethod("setTargetCompatibility", org.gradle.api.JavaVersion::class.java).invoke(compileOptions, org.gradle.api.JavaVersion.VERSION_17)
            } catch (e: Exception) { }

            try {
                val setCompileSdk = android.javaClass.getMethod("setCompileSdkVersion", Int::class.java)
                setCompileSdk.invoke(android, 36)
            } catch (e: Exception) {
                try {
                    val setCompileSdkStr = android.javaClass.getMethod("setCompileSdkVersion", String::class.java)
                    setCompileSdkStr.invoke(android, "android-36")
                } catch (e2: Exception) {
                    try {
                        val setCompileSdk = android.javaClass.getMethod("setCompileSdk", Int::class.java)
                        setCompileSdk.invoke(android, 36)
                    } catch (e3: Exception) { }
                }
            }
        }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}

allprojects {
    tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_17)
        }
    }
}
