package com.example

import android.os.Build
import android.os.Bundle
import android.util.DisplayMetrics
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.model.DeviceMetrics
import com.example.server.TouchBridgeServer
import com.example.ui.screens.*
import com.example.ui.theme.*

class MainActivity : ComponentActivity() {

    private val server = TouchBridgeServer.getInstance()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Start Companion TCP Server on port 28200
        server.start()

        val metrics = extractDeviceMetrics()

        setContent {
            TouchBridgeTheme {
                MainScreen(
                    deviceMetrics = metrics,
                    server = server,
                    onEmergencyRelease = {
                        server.releaseAllTouches()
                        Toast.makeText(this, "Emergency Release: All touches cleared!", Toast.LENGTH_SHORT).show()
                    }
                )
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        server.stop()
    }

    private fun extractDeviceMetrics(): DeviceMetrics {
        val dm = resources.displayMetrics
        val mfg = Build.MANUFACTURER.orEmpty()
        val isXiaomi = mfg.contains("xiaomi", ignoreCase = true) ||
                mfg.contains("redmi", ignoreCase = true) ||
                mfg.contains("poco", ignoreCase = true)

        @Suppress("DEPRECATION")
        val refreshRate = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            display?.refreshRate ?: 60f
        } else {
            windowManager.defaultDisplay.refreshRate
        }

        val orient = if (resources.configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE) {
            "Landscape"
        } else {
            "Portrait"
        }

        return DeviceMetrics(
            widthPx = dm.widthPixels,
            heightPx = dm.heightPixels,
            densityDpi = dm.densityDpi,
            refreshRateHz = refreshRate,
            orientation = orient,
            manufacturer = mfg.replaceFirstChar { it.uppercase() },
            model = Build.MODEL.orEmpty(),
            androidVersion = Build.VERSION.RELEASE.orEmpty(),
            isXiaomi = isXiaomi
        )
    }
}

enum class NavigationTab(val title: String) {
    DASHBOARD("Dashboard"),
    VISUALIZER("Multi-Touch"),
    XIAOMI_GUIDE("Xiaomi Guide"),
    HUD_CALIBRATOR("HUD Calibrate"),
    EVENT_LOG("Event Stream")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    deviceMetrics: DeviceMetrics,
    server: TouchBridgeServer,
    onEmergencyRelease: () -> Unit
) {
    var selectedTab by remember { mutableStateOf(NavigationTab.DASHBOARD) }
    val isRunning by server.isRunning.collectAsState()

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "TouchBridge Universal",
                            fontWeight = FontWeight.Bold,
                            fontSize = 17.sp,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Surface(
                            shape = MaterialTheme.shapes.small,
                            color = if (isRunning) CyberEmerald.copy(alpha = 0.2f) else CyberCrimson.copy(alpha = 0.2f)
                        ) {
                            Text(
                                text = "TCP:28200",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (isRunning) CyberEmerald else CyberCrimson,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }
                },
                actions = {
                    IconButton(
                        onClick = onEmergencyRelease,
                        modifier = Modifier.testTag("emergency_release_appbar_button")
                    ) {
                        Icon(
                            imageVector = Icons.Default.Shield,
                            contentDescription = "Emergency Touch Release",
                            tint = CyberCrimson
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface,
                modifier = Modifier.testTag("main_navigation_bar")
            ) {
                NavigationBarItem(
                    selected = (selectedTab == NavigationTab.DASHBOARD),
                    onClick = { selectedTab = NavigationTab.DASHBOARD },
                    icon = { Icon(Icons.Default.Dashboard, contentDescription = "Dashboard") },
                    label = { Text("Dashboard", fontSize = 10.sp) },
                    modifier = Modifier.testTag("nav_tab_dashboard")
                )
                NavigationBarItem(
                    selected = (selectedTab == NavigationTab.VISUALIZER),
                    onClick = { selectedTab = NavigationTab.VISUALIZER },
                    icon = { Icon(Icons.Default.TouchApp, contentDescription = "Multi-Touch") },
                    label = { Text("Touches", fontSize = 10.sp) },
                    modifier = Modifier.testTag("nav_tab_visualizer")
                )
                NavigationBarItem(
                    selected = (selectedTab == NavigationTab.XIAOMI_GUIDE),
                    onClick = { selectedTab = NavigationTab.XIAOMI_GUIDE },
                    icon = { Icon(Icons.Default.Security, contentDescription = "Xiaomi Guide") },
                    label = { Text("Xiaomi", fontSize = 10.sp) },
                    modifier = Modifier.testTag("nav_tab_xiaomi")
                )
                NavigationBarItem(
                    selected = (selectedTab == NavigationTab.HUD_CALIBRATOR),
                    onClick = { selectedTab = NavigationTab.HUD_CALIBRATOR },
                    icon = { Icon(Icons.Default.SportsEsports, contentDescription = "HUD Calibrate") },
                    label = { Text("HUD", fontSize = 10.sp) },
                    modifier = Modifier.testTag("nav_tab_hud")
                )
                NavigationBarItem(
                    selected = (selectedTab == NavigationTab.EVENT_LOG),
                    onClick = { selectedTab = NavigationTab.EVENT_LOG },
                    icon = { Icon(Icons.Default.Terminal, contentDescription = "Event Stream") },
                    label = { Text("Log", fontSize = 10.sp) },
                    modifier = Modifier.testTag("nav_tab_log")
                )
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (selectedTab) {
                NavigationTab.DASHBOARD -> DashboardScreen(deviceMetrics, server)
                NavigationTab.VISUALIZER -> TouchVisualizerScreen(server)
                NavigationTab.XIAOMI_GUIDE -> XiaomiGuideScreen()
                NavigationTab.HUD_CALIBRATOR -> KeymapOverlayScreen()
                NavigationTab.EVENT_LOG -> ProtocolLogScreen(server)
            }
        }
    }
}
