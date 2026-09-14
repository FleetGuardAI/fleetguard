package com.example.fleetguard_owner

import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.content.pm.PackageManager

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.example.fleetguard_owner/config"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "getGeoapifyKey") {
                try {
                    val appInfo = context.packageManager.getApplicationInfo(context.packageName, PackageManager.GET_META_DATA)
                    val bundle = appInfo.metaData
                    val key = bundle?.getString("GEOAPIFY_API_KEY")
                    result.success(key)
                } catch (e: Exception) {
                    result.error("UNAVAILABLE", "Failed to retrieve key.", null)
                }
            } else {
                result.notImplemented()
            }
        }
    }
}
