package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.Terminal
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.model.TouchAction
import com.example.model.TouchPacket
import com.example.server.TouchBridgeServer
import com.example.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun ProtocolLogScreen(
    server: TouchBridgeServer,
    modifier: Modifier = Modifier
) {
    val packets by server.recentPackets.collectAsState()
    val timeFormat = remember { SimpleDateFormat("HH:mm:ss.SSS", Locale.getDefault()) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Log Header Bar
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Terminal,
                        contentDescription = "Console",
                        tint = CyberCyan,
                        modifier = Modifier.size(22.dp)
                    )
                    Text(
                        text = "Protocol Event Stream",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }

                Text(
                    text = "${packets.size} Events Buffered",
                    fontSize = 12.sp,
                    color = TextSecondary
                )
            }
        }

        // Event List
        if (packets.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .background(Color(0xFF070B14), shape = RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Awaiting touch packets over ADB port 28200...\nConnect TouchBridge Desktop to see live events",
                    color = TextSecondary,
                    fontSize = 13.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .testTag("protocol_log_list"),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(packets) { pkt ->
                    PacketRow(pkt, timeFormat)
                }
            }
        }
    }
}

@Composable
private fun PacketRow(pkt: TouchPacket, timeFormat: SimpleDateFormat) {
    val actionColor = when (pkt.action) {
        TouchAction.DOWN -> CyberEmerald
        TouchAction.MOVE -> CyberCyan
        TouchAction.UP -> CyberAmber
        TouchAction.RELEASE_ALL -> CyberCrimson
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = actionColor.copy(alpha = 0.2f)
                ) {
                    Text(
                        text = pkt.action.name,
                        color = actionColor,
                        fontWeight = FontWeight.Bold,
                        fontSize = 10.sp,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }

                Text(
                    text = "ID: ${pkt.id}",
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            Text(
                text = "X: ${"%.3f".format(pkt.normX)}  Y: ${"%.3f".format(pkt.normY)}",
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                color = TextSecondary
            )

            Text(
                text = timeFormat.format(Date(pkt.timestamp)),
                fontFamily = FontFamily.Monospace,
                fontSize = 10.sp,
                color = TextSecondary.copy(alpha = 0.8f)
            )
        }
    }
}
