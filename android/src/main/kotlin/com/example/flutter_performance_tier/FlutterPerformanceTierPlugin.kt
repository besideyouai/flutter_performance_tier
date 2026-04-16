package com.example.flutter_performance_tier

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

class FlutterPerformanceTierPlugin : FlutterPlugin, MethodChannel.MethodCallHandler {
    companion object {
        const val channelName: String = "performance_tier/device_signals"
        private const val collectDeviceSignalsMethod: String = "collectDeviceSignals"
    }

    private lateinit var channel: MethodChannel
    private lateinit var applicationContext: Context

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        applicationContext = binding.applicationContext
        channel = MethodChannel(binding.binaryMessenger, channelName)
        channel.setMethodCallHandler(this)
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            collectDeviceSignalsMethod -> result.success(collectDeviceSignals())
            else -> result.notImplemented()
        }
    }

    private fun collectDeviceSignals(): Map<String, Any?> {
        val activityManager =
            applicationContext.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager?.getMemoryInfo(memoryInfo)
        val memoryPressureLevel = resolveMemoryPressureLevel(memoryInfo)

        return mapOf(
            "platform" to "android",
            "deviceModel" to Build.MODEL.takeIf { it.isNotBlank() },
            "totalRamBytes" to memoryInfo.totalMem.takeIf { it > 0L },
            "isLowRamDevice" to activityManager?.isLowRamDevice,
            "mediaPerformanceClass" to mediaPerformanceClassOrNull(),
            "sdkInt" to Build.VERSION.SDK_INT,
            "memoryPressureState" to memoryPressureState(memoryPressureLevel),
            "memoryPressureLevel" to memoryPressureLevel
        )
    }

    private fun mediaPerformanceClassOrNull(): Int? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            return null
        }

        val mediaPerformanceClass = Build.VERSION.MEDIA_PERFORMANCE_CLASS
        return mediaPerformanceClass.takeIf { it > 0 }
    }

    private fun resolveMemoryPressureLevel(memoryInfo: ActivityManager.MemoryInfo): Int {
        if (memoryInfo.lowMemory) {
            return 2
        }
        if (memoryInfo.threshold > 0L && memoryInfo.availMem <= memoryInfo.threshold * 2L) {
            return 1
        }
        return 0
    }

    private fun memoryPressureState(level: Int): String {
        return when {
            level >= 2 -> "critical"
            level >= 1 -> "moderate"
            else -> "normal"
        }
    }
}
