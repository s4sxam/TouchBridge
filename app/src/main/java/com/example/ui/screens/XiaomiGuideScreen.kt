package com.example.ui.screens

import android.content.Intent
import android.provider.Settings
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material.icons.filled.Security
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
import com.example.model.XiaomiDiagnosticStep
import com.example.ui.theme.*

@Composable
fun XiaomiGuideScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val scrollState = rememberScrollState()

    val initialSteps = remember {
        listOf(
            XiaomiDiagnosticStep(
                id = "dev_options",
                title = "1. Enable Developer Options",
                description = "Go to Settings > About Phone > Tap 'OS version' or 'MIUI version' 7 times until you see 'You are now a developer!'",
                isCritical = true
            ),
            XiaomiDiagnosticStep(
                id = "usb_debugging",
                title = "2. Enable USB Debugging",
                description = "Go to Settings > Additional Settings > Developer Options > Toggle 'USB Debugging' ON.",
                isCritical = true
            ),
            XiaomiDiagnosticStep(
                id = "sim_card",
                title = "3. Active SIM Card & Mi Account",
                description = "Xiaomi requires an active SIM card and signed-in Mi Account to enable touch injection permissions. This is only needed once.",
                isCritical = true
            ),
            XiaomiDiagnosticStep(
                id = "security_settings",
                title = "4. Enable 'USB debugging (Security settings)' [CRITICAL]",
                description = "In Developer Options, scroll down to 'USB debugging (Security settings)'. Toggle it ON and accept the 3 confirmation countdowns. WITHOUT THIS, TOUCH INJECTION IS SILENTLY BLOCKED!",
                isCritical = true
            ),
            XiaomiDiagnosticStep(
                id = "stay_awake",
                title = "5. Enable 'Stay Awake'",
                description = "Keep phone display awake while charging/USB connected so your game stream does not sleep.",
                isCritical = false
            ),
            XiaomiDiagnosticStep(
                id = "pointer_location",
                title = "6. Optional: Enable 'Pointer Location'",
                description = "In Developer Options, turn ON 'Pointer location' to see real-time hardware touch coordinates overlaid at the top of the screen.",
                isCritical = false
            )
        )
    }

    val steps = remember { mutableStateListOf(*initialSteps.toTypedArray()) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(DarkBackground)
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Header Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier.padding(18.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Security,
                    contentDescription = "Security",
                    tint = CyberAmber,
                    modifier = Modifier.size(36.dp)
                )
                Column {
                    Text(
                        text = "Xiaomi & Redmi Setup Guide",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = "Fixing 'Touch Not Responding' on MIUI & HyperOS",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )
                }
            }
        }

        // Quick Setting Shortcut Button
        Button(
            onClick = {
                try {
                    context.startActivity(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))
                } catch (e: Exception) {
                    try {
                        context.startActivity(Intent(Settings.ACTION_SETTINGS))
                    } catch (_: Exception) {
                        Toast.makeText(context, "Could not open settings", Toast.LENGTH_SHORT).show()
                    }
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .testTag("open_developer_options_button"),
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(containerColor = CyberIndigo)
        ) {
            Icon(imageVector = Icons.Default.OpenInNew, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Open Phone Developer Options", fontWeight = FontWeight.Bold)
        }

        // Checklist of Steps
        steps.forEachIndexed { index, step ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        steps[index] = step.copy(isCompleted = !step.isCompleted)
                    }
                    .testTag("step_card_${step.id}"),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = if (step.isCompleted) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface
                )
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Icon(
                        imageVector = if (step.isCompleted) Icons.Default.CheckCircle else Icons.Default.RadioButtonUnchecked,
                        contentDescription = "Check",
                        tint = if (step.isCompleted) CyberEmerald else if (step.isCritical) CyberAmber else Color(0xFF64748B),
                        modifier = Modifier.size(24.dp)
                    )
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = step.title,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (step.isCompleted) CyberEmerald else MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = step.description,
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }
    }
}
