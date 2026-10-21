package com.example.ui.screens

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.model.DeviceMetrics
import com.example.model.TouchAction
import com.example.model.TouchPacket
import com.example.server.TouchBridgeServer
import com.example.ui.theme.*

@Composable
fun DashboardScreen(
    deviceMetrics: DeviceMetrics,
    server: TouchBridgeServer,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val isRunning by server.isRunning.collectAsState()
    val connectedClients by server.connectedClients.collectAsState()
    val activePointers by server.activePointers.collectAsState()
    val packetRateHz by server.packetRateHz.collectAsState()
    val latencyMs by server.averageLatencyMs.collectAsState()

    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // App Header Banner
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .testTag("dashboard_header_card"),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "TouchBridge Companion",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Android Gaming Input Bridge & Diagnostic Daemon",
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )
                }

                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = if (isRunning) CyberEmerald.copy(alpha = 0.2f) else CyberCrimson.copy(alpha = 0.2f),
                    border = null
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .background(if (isRunning) CyberEmerald else CyberCrimson, shape = RoundedCornerShape(4.dp))
                        )
                        Text(
                            text = if (isRunning) "LISTENING" else "STOPPED",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isRunning) CyberEmerald else CyberCrimson
                        )
                    }
                }
            }
        }

        // Xiaomi Alert if detected
        if (deviceMetrics.isXiaomi) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .testTag("xiaomi_alert_banner"),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = CyberAmber.copy(alpha = 0.15f))
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Warning,
                        contentDescription = "Warning",
                        tint = CyberAmber,
                        modifier = Modifier.size(28.dp)
                    )
                    Column {
                        Text(
                            text = "Xiaomi / Redmi Device Detected",
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            color = CyberAmber
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "MIUI/HyperOS requires 'USB debugging (Security settings)' to be turned ON to accept touch inputs. See the Xiaomi Guide tab.",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.85f)
                        )
                    }
                }
            }
        }

        // Live Telemetry Grid
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            TelemetryTile(
                modifier = Modifier.weight(1f),
                title = "PORT",
                value = "${TouchBridgeServer.PORT}",
                subtitle = "TCP Socket",
                accentColor = CyberIndigo
            )
            TelemetryTile(
                modifier = Modifier.weight(1f),
                title = "CLIENTS",
                value = "$connectedClients",
                subtitle = if (connectedClients > 0) "PC Connected" else "Waiting for PC",
                accentColor = if (connectedClients > 0) CyberEmerald else CyberCyan
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            TelemetryTile(
                modifier = Modifier.weight(1f),
                title = "ACTIVE TOUCHES",
                value = "${activePointers.size} / 10",
                subtitle = "Multi-Touch Pointers",
                accentColor = CyberCyan
            )
            TelemetryTile(
                modifier = Modifier.weight(1f),
                title = "THROUGHPUT",
                value = "$packetRateHz Hz",
                subtitle = "Lat: ${"%.1f".format(latencyMs)} ms",
                accentColor = CyberEmerald
            )
        }

        // ADB Forward Command Helper
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "ADB Port Forward Command",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Run this in Command Prompt / Terminal to link PC to phone:",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                )
                Spacer(modifier = Modifier.height(8.dp))

                val adbCmd = "adb forward tcp:28200 tcp:28200"
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = adbCmd,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                            color = CyberCyan
                        )
                        IconButton(
                            onClick = {
                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                val clip = ClipData.newPlainText("ADB Command", adbCmd)
                                clipboard.setPrimaryClip(clip)
                                Toast.makeText(context, "Command copied to clipboard!", Toast.LENGTH_SHORT).show()
                            },
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.ContentCopy,
                                contentDescription = "Copy ADB Command",
                                tint = CyberCyan,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }
                }
            }
        }

        // 1-Tap Popular Game Presets Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .testTag("quick_game_presets_card"),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Bolt,
                        contentDescription = null,
                        tint = CyberEmerald
                    )
                    Text(
                        text = "1-Tap Popular Game Profiles",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Tap any game to test or calibrate its layout instantly on your phone:",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                )
                Spacer(modifier = Modifier.height(10.dp))

                val gamesRow1 = listOf(
                    "🎯 Free Fire",
                    "🪖 PUBG Mobile",
                    "🎖️ COD Mobile"
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    gamesRow1.forEach { gameTitle ->
                        Button(
                            onClick = {
                                Toast.makeText(context, "Activated $gameTitle profile layout!", Toast.LENGTH_SHORT).show()
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                            contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp)
                        ) {
                            Text(gameTitle, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                val gamesRow2 = listOf(
                    "⚔️ Genshin",
                    "⭐ Brawl Stars",
                    "🏎️ Asphalt 9"
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    gamesRow2.forEach { gameTitle ->
                        Button(
                            onClick = {
                                Toast.makeText(context, "Activated $gameTitle profile layout!", Toast.LENGTH_SHORT).show()
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                            contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp)
                        ) {
                            Text(gameTitle, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface)
                        }
                    }
                }
            }
        }

        // Device Display Specs
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Device Display Calibration",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(10.dp))

                MetricRow("Device", "${deviceMetrics.manufacturer} ${deviceMetrics.model}")
                MetricRow("Resolution", "${deviceMetrics.widthPx} x ${deviceMetrics.heightPx} px")
                MetricRow("Screen Density", "${deviceMetrics.densityDpi} DPI")
                MetricRow("Refresh Rate", "${deviceMetrics.refreshRateHz.toInt()} Hz Gaming Display")
                MetricRow("Android Version", "Android ${deviceMetrics.androidVersion}")
            }
        }

        // Quick Simulated Input Action Buttons
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "On-Device Diagnostic Tests",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(10.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Button(
                        onClick = {
                            // Inject 3 simulated touches
                            server.routePacket(TouchPacket(id = 0, action = TouchAction.DOWN, normX = 0.2f, normY = 0.7f))
                            server.routePacket(TouchPacket(id = 1, action = TouchAction.DOWN, normX = 0.7f, normY = 0.5f))
                            server.routePacket(TouchPacket(id = 2, action = TouchAction.DOWN, normX = 0.88f, normY = 0.68f))
                            Toast.makeText(context, "Simulated 3 simultaneous touches!", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("simulate_multi_touch_button"),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = CyberIndigo)
                    ) {
                        Text("Simulate 3 Touches", fontSize = 12.sp)
                    }

                    Button(
                        onClick = {
                            server.releaseAllTouches()
                            Toast.makeText(context, "All touches released!", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("release_all_touches_button"),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = CyberCrimson)
                    ) {
                        Text("Release All", fontSize = 12.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun TelemetryTile(
    title: String,
    value: String,
    subtitle: String,
    accentColor: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(14.dp)
        ) {
            Text(
                text = title,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = accentColor
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                fontSize = 18.sp,
                fontWeight = FontWeight.ExtraBold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = subtitle,
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
            )
        }
    }
}

@Composable
private fun MetricRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            fontSize = 13.sp,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
        Text(
            text = value,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}
