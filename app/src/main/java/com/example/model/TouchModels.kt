package com.example.model

enum class TouchAction {
    DOWN, MOVE, UP, RELEASE_ALL
}

data class TouchPacket(
    val id: Int = 0,
    val action: TouchAction = TouchAction.DOWN,
    val x: Int = 0,
    val y: Int = 0,
    val normX: Float = 0.5f,
    val normY: Float = 0.5f,
    val pressure: Float = 1.0f,
    val timestamp: Long = System.currentTimeMillis()
)

data class ActiveTouch(
    val id: Int,
    val x: Float,
    val y: Float,
    val pressure: Float = 1.0f,
    val colorIndex: Int = id % 10
)

data class DeviceMetrics(
    val widthPx: Int,
    val heightPx: Int,
    val densityDpi: Int,
    val refreshRateHz: Float,
    val orientation: String,
    val manufacturer: String,
    val model: String,
    val androidVersion: String,
    val isXiaomi: Boolean
)

data class XiaomiDiagnosticStep(
    val id: String,
    val title: String,
    val description: String,
    val isCritical: Boolean,
    val isCompleted: Boolean = false
)

data class VirtualHudElement(
    val id: String,
    val label: String,
    val normX: Float,
    val normY: Float,
    val radiusNorm: Float = 0.06f,
    val isJoystick: Boolean = false,
    val isAimZone: Boolean = false,
    val zoneWidthNorm: Float = 0.4f,
    val zoneHeightNorm: Float = 0.6f
)
