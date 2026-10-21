package com.example.ui.screens

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.model.VirtualHudElement
import com.example.ui.theme.*

@Composable
fun KeymapOverlayScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    var selectedPreset by remember { mutableStateOf("FPS") }
    var hudOpacity by remember { mutableFloatStateOf(0.85f) }
    var hudScale by remember { mutableFloatStateOf(1.0f) }

    // Editable virtual controls
    val hudElements = remember(selectedPreset) {
        when (selectedPreset) {
            "MOBA" -> mutableStateListOf(
                VirtualHudElement("joy", "JOYSTICK", 0.16f, 0.74f, 0.12f, isJoystick = true),
                VirtualHudElement("atk", "SPACE / ATK", 0.88f, 0.78f, 0.08f),
                VirtualHudElement("q", "Q / S1", 0.78f, 0.82f, 0.06f),
                VirtualHudElement("e", "E / S2", 0.82f, 0.66f, 0.06f),
                VirtualHudElement("r", "R / ULT", 0.88f, 0.54f, 0.06f),
                VirtualHudElement("f", "F / SPELL", 0.72f, 0.72f, 0.05f)
            )
            "RACING" -> mutableStateListOf(
                VirtualHudElement("left", "A (LEFT)", 0.15f, 0.72f, 0.08f),
                VirtualHudElement("right", "D (RIGHT)", 0.28f, 0.72f, 0.08f),
                VirtualHudElement("nitro", "SPACE (NITRO)", 0.88f, 0.65f, 0.09f),
                VirtualHudElement("drift", "SHIFT (DRIFT)", 0.74f, 0.75f, 0.08f)
            )
            else -> mutableStateListOf(
                // Standard FPS / Battle Royale
                VirtualHudElement("wasd", "WASD", 0.18f, 0.72f, 0.12f, isJoystick = true),
                VirtualHudElement("aim_zone", "MOUSE LOOK ZONE", 0.72f, 0.48f, 0.10f, isAimZone = true),
                VirtualHudElement("fire", "L-CLICK (FIRE)", 0.88f, 0.68f, 0.06f),
                VirtualHudElement("ads", "R-CLICK (ADS)", 0.84f, 0.48f, 0.05f),
                VirtualHudElement("jump", "SPACE (JUMP)", 0.92f, 0.78f, 0.05f),
                VirtualHudElement("crouch", "C (CROUCH)", 0.82f, 0.82f, 0.05f),
                VirtualHudElement("reload", "R (RELOAD)", 0.75f, 0.28f, 0.04f),
                VirtualHudElement("sprint", "SHIFT", 0.22f, 0.52f, 0.04f)
            )
        }
    }

    var selectedElementId by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Preset Selector & Sliders Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "HUD Calibration Overlay",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        listOf("FPS", "MOBA", "RACING").forEach { preset ->
                            FilterChip(
                                selected = (selectedPreset == preset),
                                onClick = { selectedPreset = preset },
                                label = { Text(preset, fontSize = 11.sp) }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Opacity: ${(hudOpacity * 100).toInt()}%", fontSize = 11.sp, color = TextSecondary)
                    Slider(
                        value = hudOpacity,
                        onValueChange = { hudOpacity = it },
                        valueRange = 0.2f..1.0f,
                        modifier = Modifier.weight(1f)
                    )

                    Text("Scale: ${(hudScale * 100).toInt()}%", fontSize = 11.sp, color = TextSecondary)
                    Slider(
                        value = hudScale,
                        onValueChange = { hudScale = it },
                        valueRange = 0.5f..1.5f,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // Calibrator Canvas (Touch to Drag Elements)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .background(Color(0xFF070B14), shape = RoundedCornerShape(12.dp))
                .pointerInput(selectedPreset) {
                    detectDragGestures(
                        onDragStart = { offset ->
                            val w = size.width
                            val h = size.height
                            // Find element nearest to drag
                            val clicked = hudElements.findLast { elem ->
                                val cx = elem.normX * w
                                val cy = elem.normY * h
                                val r = elem.radiusNorm * h * hudScale
                                val distSq = (offset.x - cx) * (offset.x - cx) + (offset.y - cy) * (offset.y - cy)
                                distSq <= r * r * 1.5f
                            }
                            selectedElementId = clicked?.id
                            if (clicked != null) {
                                triggerHaptic(context)
                            }
                        },
                        onDrag = { change, dragAmount ->
                            change.consume()
                            val id = selectedElementId ?: return@detectDragGestures
                            val index = hudElements.indexOfFirst { it.id == id }
                            if (index != -1) {
                                val elem = hudElements[index]
                                val newX = (elem.normX + dragAmount.x / size.width).coerceIn(0.02f, 0.98f)
                                val newY = (elem.normY + dragAmount.y / size.height).coerceIn(0.02f, 0.98f)
                                hudElements[index] = elem.copy(normX = newX, normY = newY)
                            }
                        },
                        onDragEnd = {
                            selectedElementId = null
                        }
                    )
                }
                .testTag("keymap_overlay_canvas")
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val w = size.width
                val h = size.height

                // Draw alignment guidelines
                drawLine(Color(0xFF1E293B), Offset(w / 2f, 0f), Offset(w / 2f, h), strokeWidth = 1f)
                drawLine(Color(0xFF1E293B), Offset(0f, h / 2f), Offset(w, h / 2f), strokeWidth = 1f)

                hudElements.forEach { elem ->
                    val cx = elem.normX * w
                    val cy = elem.normY * h
                    val isSel = (elem.id == selectedElementId)

                    if (elem.isJoystick) {
                        val r = elem.radiusNorm * h * hudScale
                        drawCircle(
                            color = CyberIndigo.copy(alpha = hudOpacity * 0.25f),
                            radius = r,
                            center = Offset(cx, cy)
                        )
                        drawCircle(
                            color = CyberIndigo.copy(alpha = hudOpacity),
                            radius = r,
                            center = Offset(cx, cy),
                            style = Stroke(width = if (isSel) 4.dp.toPx() else 2.dp.toPx())
                        )
                        drawCircle(
                            color = CyberIndigo.copy(alpha = hudOpacity),
                            radius = 16.dp.toPx() * hudScale,
                            center = Offset(cx, cy)
                        )
                    } else if (elem.isAimZone) {
                        val zw = elem.zoneWidthNorm * w * hudScale
                        val zh = elem.zoneHeightNorm * h * hudScale
                        drawRect(
                            color = CyberCyan.copy(alpha = hudOpacity * 0.15f),
                            topLeft = Offset(cx - zw / 2f, cy - zh / 2f),
                            size = androidx.compose.ui.geometry.Size(zw, zh)
                        )
                        drawRect(
                            color = CyberCyan.copy(alpha = hudOpacity),
                            topLeft = Offset(cx - zw / 2f, cy - zh / 2f),
                            size = androidx.compose.ui.geometry.Size(zw, zh),
                            style = Stroke(width = 2.dp.toPx())
                        )
                    } else {
                        val r = elem.radiusNorm * h * hudScale
                        val color = if (elem.label.contains("FIRE") || elem.label.contains("ATK")) CyberCrimson else CyberIndigoLight
                        drawCircle(
                            color = color.copy(alpha = hudOpacity * (if (isSel) 0.6f else 0.35f)),
                            radius = r,
                            center = Offset(cx, cy)
                        )
                        drawCircle(
                            color = if (isSel) Color.White else color.copy(alpha = hudOpacity),
                            radius = r,
                            center = Offset(cx, cy),
                            style = Stroke(width = if (isSel) 3.dp.toPx() else 2.dp.toPx())
                        )
                    }
                }
            }

            // Overlay element labels
            hudElements.forEach { elem ->
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(start = (elem.normX * 300).dp, top = (elem.normY * 400).dp)
                ) {
                    // Placement anchor
                }
            }

            Text(
                text = "Drag controls to align with your in-game layout | Coordinates auto-calibrate",
                color = TextSecondary,
                fontSize = 11.sp,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(8.dp)
            )
        }
    }
}

private fun triggerHaptic(context: Context) {
    try {
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator?.vibrate(VibrationEffect.createOneShot(20, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator?.vibrate(20)
        }
    } catch (_: Exception) {}
}
