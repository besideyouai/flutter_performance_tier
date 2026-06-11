package com.example.flutter_performance_tier

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.io.File

class FlutterPerformanceTierPlugin : FlutterPlugin, MethodChannel.MethodCallHandler {
    companion object {
        const val channelName: String = "performance_tier/device_signals"
        private const val collectDeviceSignalsMethod: String = "collectDeviceSignals"
        private const val writePerformanceReportMethod: String = "writePerformanceReport"
        private const val listPerformanceReportsMethod: String = "listPerformanceReports"
        private const val reportsDirectoryName: String = "performance_tier_reports"
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
            writePerformanceReportMethod -> writePerformanceReport(call, result)
            listPerformanceReportsMethod -> result.success(listPerformanceReports())
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

    private fun writePerformanceReport(call: MethodCall, result: MethodChannel.Result) {
        val content = call.argument<String>("content")
        val fileName = call.argument<String>("fileName")
        val reportId = call.argument<String>("reportId")
        if (content.isNullOrBlank()) {
            result.error(
                "invalid_report_content",
                "Performance report content must be a non-empty JSON string.",
                null
            )
            return
        }
        if (!isSafeReportFileName(fileName)) {
            result.error(
                "invalid_report_file_name",
                "Performance report fileName must be a safe .json file name.",
                null
            )
            return
        }

        try {
            val reportsDir = reportsDirectory()
            if (!reportsDir.exists() && !reportsDir.mkdirs()) {
                result.error(
                    "report_directory_unavailable",
                    "Could not create performance report directory.",
                    reportsDir.absolutePath
                )
                return
            }
            val reportFile = nextAvailableReportFile(reportsDir, fileName!!)
            reportFile.writeText(content, Charsets.UTF_8)
            result.success(reportFileMap(reportFile) + mapOf("reportId" to reportId))
        } catch (error: Exception) {
            result.error(
                "write_performance_report_failed",
                error.message,
                null
            )
        }
    }

    private fun listPerformanceReports(): List<Map<String, Any?>> {
        val reportsDir = reportsDirectory()
        val reportFiles = reportsDir.listFiles { file ->
            file.isFile && file.name.endsWith(".json")
        } ?: return emptyList()
        return reportFiles
            .sortedByDescending { file -> file.lastModified() }
            .map(::reportFileMap)
    }

    private fun reportsDirectory(): File {
        return File(applicationContext.filesDir, reportsDirectoryName)
    }

    private fun nextAvailableReportFile(directory: File, requestedFileName: String): File {
        val firstCandidate = File(directory, requestedFileName)
        if (!firstCandidate.exists()) {
            return firstCandidate
        }

        val baseName = requestedFileName.removeSuffix(".json")
        for (sequence in 1..999) {
            val candidate = File(directory, "$baseName-$sequence.json")
            if (!candidate.exists()) {
                return candidate
            }
        }

        throw IllegalStateException(
            "Could not choose a unique performance report file name."
        )
    }

    private fun reportFileMap(file: File): Map<String, Any?> {
        return mapOf(
            "fileName" to file.name,
            "relativePath" to "files/$reportsDirectoryName/${file.name}",
            "absolutePath" to file.absolutePath,
            "bytes" to file.length(),
            "modifiedAtEpochMs" to file.lastModified(),
            "writtenAtEpochMs" to file.lastModified()
        )
    }

    private fun isSafeReportFileName(fileName: String?): Boolean {
        if (fileName.isNullOrBlank()) {
            return false
        }
        if (!fileName.endsWith(".json")) {
            return false
        }
        return fileName.all { char ->
            char.isLetterOrDigit() || char == '-' || char == '_' || char == '.'
        }
    }
}
