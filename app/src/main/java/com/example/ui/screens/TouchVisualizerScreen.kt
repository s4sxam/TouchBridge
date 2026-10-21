package com.example.ui.screens

import android.view.MotionEvent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInteropFilter
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.model.ActiveTouch
import com.example.model.TouchAction
import com.example.model.TouchPacket
import com.example.server.TouchBridgeServer
import com.example.ui.theme.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private val pointerPalette = listOf(
    CyberIndigo,
    CyberCyan,
    CyberEmerald,
    CyberCrimson,
    CyberAmber,
    Color(0xFFA855F7), // Purple
    Color(0xFFEC4899), // Pink
    Color(0xFF14B8A6), // Teal
    Color(0xFFEAB308), // Yellow
    Color(0xFF3B82F6), // Blue
)

@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun TouchVisualizerScreen(
    server: TouchBridgeServer,
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()
    val serverPointers by server.activePointers.collectAsState()
    val rateHz by server.packetRateHz.collectAsState()
    val latencyMs by server.averageLatencyMs.collectAsState()

    // Local screen touches (to test simultaneous physical + simulated multi-touch)
    val localPointers = remember { mutableStateMapOf<Int, ActiveTouch>() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Top Status Bar
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 14.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "Pointers Active: ${serverPointers.size + localPointers.size}",
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = CyberCyan
                )
                Text(
                    text = "Throughput: $rateHz Hz",
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = CyberEmerald
                )
                Text(
                    text = "Latency: ${"%.1f".format(latencyMs)} ms",
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = CyberIndigoLight
                )
            }
        }

        // Interactive Touch Canvas
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .background(Color(0xFF070B14), shape = RoundedCornerShape(12.dp))
                .pointerInteropFilter { motionEvent ->
                    val action = motionEvent.actionMasked
                    val index = motionEvent.actionIndex
                    val pointerId = motionEvent.getPointerId(index)

                    when (action) {
                        MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> {
                            localPointers[pointerId] = ActiveTouch(
                                id = pointerId,
                                x = motionEvent.getX(index),
                                y = motionEvent.getY(index),
                                pressure = motionEvent.getPressure(index)
                            )
                        }
                        MotionEvent.ACTION_MOVE -> {
                            for (i in 0 until motionEvent.pointerCount) {
                                val pid = motionEvent.getPointerId(i)
                                localPointers[pid] = ActiveTouch(
                                    id = pid,
                                    x = motionEvent.getX(i),
                                    y = motionEvent.getY(i),
                                    pressure = motionEvent.getPressure(i)
                                )
                            }
                        }
                        MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP -> {
                            localPointers.remove(pointerId)
                        }
                        MotionEvent.ACTION_CANCEL -> {
                            localPointers.clear()
                        }
                    }
                    true
                }
                .testTag("touch_visualizer_canvas")
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val w = size.width
                val h = size.height

                // Draw Grid
                val gridStep = 40.dp.toPx()
                var gx = 0f
                while (gx < w) {
                    drawLine(Color(0xFF1E293B), Offset(gx, 0f), Offset(gx, h), strokeWidth = 1f)
                    gx += gridStep
                }
                var gy = 0f
                while (gy < h) {
                    drawLine(Color(0xFF1E293B), Offset(0f, gy), Offset(w, gy), strokeWidth = 1f)
                    gy += gridStep
                }

                // Render Simulated Server Pointers (normalized 0..1 coordinates)
                serverPointers.values.forEach { pt ->
                    val px = pt.x * w
                    val py = pt.y * h
                    val col = pointerPalette[pt.id % pointerPalette.size]

                    // Glowing outer ring
                    drawCircle(
                        color = col.copy(alpha = 0.25f),
                        radius = 48.dp.toPx(),
                        center = Offset(px, py)
                    )
                    drawCircle(
                        color = col,
                        radius = 32.dp.toPx(),
                        center = Offset(px, py),
                        style = Stroke(width = 3.dp.toPx())
                    )
                    // Inner solid knob
                    drawCircle(
                        color = col,
                        radius = 12.dp.toPx(),
                        center = Offset(px, py)
                    )

                    // Crosshairs
                    drawLine(col, Offset(px - 18.dp.toPx(), py), Offset(px + 18.dp.toPx(), py), strokeWidth = 2f)
                    drawLine(col, Offset(px, py - 18.dp.toPx()), Offset(px, py + 18.dp.toPx()), strokeWidth = 2f)
                }

                // Render Physical Finger Touches (absolute pixel coordinates)
                localPointers.values.forEach { pt ->
                    val col = pointerPalette[(pt.id + 5) % pointerPalette.size]
                    drawCircle(
                        color = col.copy(alpha = 0.35f),
                        radius = 40.dp.toPx(),
                        center = Offset(pt.x, pt.y)
                    )
                    drawCircle(
                        color = col,
                        radius = 16.dp.toPx(),
                        center = Offset(pt.x, pt.y)
                    )
                }
            }

            if (serverPointers.isEmpty() && localPointers.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Touch screen or send ADB commands to inspect contacts\n(Supports up to 10 simultaneous touches)",
                        color = Color(0xFF64748B),
                        fontSize = 13.sp,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )
                }
            }
        }

        // Action Toolbar
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = {
                    coroutineScope.launch {
                        // Simulate smooth WASD Joystick circle sweep
                        server.routePacket(TouchPacket(id = 0, action = TouchAction.DOWN, normX = 0.2f, normY = 0.7f))
                        for (deg in 0..360 step 30) {
                            val rad = Math.toRadians(deg.toDouble())
                            val nx = (0.2f + 0.1f * Math.cos(rad)).toFloat()
                            val ny = (0.7f + 0.1f * Math.sin(rad)).toFloat()
                            server.routePacket(TouchPacket(id = 0, action = TouchAction.MOVE, normX = nx, normY = ny))
                            delay(40)
                        }
                        server.routePacket(TouchPacket(id = 0, action = TouchAction.UP, normX = 0.2f, normY = 0.7f))
                    }
                },
                modifier = Modifier
                    .weight(1f)
                    .testTag("test_joystick_sweep_button"),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = CyberIndigo)
            ) {
                Icon(imageVector = Icons.Default.PlayArrow, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Test Joystick", fontSize = 11.sp)
            }

            Button(
                onClick = {
                    coroutineScope.launch {
                        // Simulate Mouse Look swipe across right screen
                        server.routePacket(TouchPacket(id = 1, action = TouchAction.DOWN, normX = 0.6f, normY = 0.5f))
                        for (step in 1..10) {
                            val nx = 0.6f + (step * 0.03f)
                            server.routePacket(TouchPacket(id = 1, action = TouchAction.MOVE, normX = nx, normY = 0.5f))
                            delay(30)
                        }
                        server.routePacket(TouchPacket(id = 1, action = TouchAction.UP, normX = 0.9f, normY = 0.5f))
                    }
                },
                modifier = Modifier
                    .weight(1f)
                    .testTag("test_mouse_swipe_button"),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCyan)
            ) {
                Icon(imageVector = Icons.Default.PlayArrow, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Test Mouse Swipe", fontSize = 11.sp)
            }

            Button(
                onClick = {
                    server.releaseAllTouches()
                    localPointers.clear()
                },
                modifier = Modifier
                    .weight(0.8f)
                    .testTag("clear_touches_button"),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = CyberCrimson)
            ) {
                Icon(imageVector = Icons.Default.Delete, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Clear", fontSize = 11.sp)
            }
        }
    }
}
