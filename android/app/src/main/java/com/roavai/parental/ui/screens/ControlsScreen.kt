package com.roavai.parental.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.roavai.parental.data.model.TutoringControls
import com.roavai.parental.ui.theme.GreenSuccess
import com.roavai.parental.ui.theme.IndigoPrimary
import com.roavai.parental.ui.theme.RedDanger
import com.roavai.parental.ui.viewmodel.ControlsUiState
import com.roavai.parental.ui.viewmodel.ControlsViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ControlsScreen(
    viewModel: ControlsViewModel
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Wini Tutoring Controls", fontWeight = FontWeight.Bold) }
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            when (val state = uiState) {
                is ControlsUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is ControlsUiState.Error -> {
                    Text(state.message, modifier = Modifier.align(Alignment.Center), color = RedDanger)
                }
                is ControlsUiState.Success -> {
                    ControlsContent(
                        controls = state.controls,
                        syncLatency = state.syncLatencySeconds,
                        onUpdate = { updated -> viewModel.updateControls(updated) },
                        onPauseToggle = { viewModel.togglePauseWini() }
                    )
                }
            }
        }
    }
}

@Composable
fun ControlsContent(
    controls: TutoringControls,
    syncLatency: Double?,
    onUpdate: (TutoringControls) -> Unit,
    onPauseToggle: () -> Unit
) {
    var timeLimit by remember(controls) { mutableStateOf(controls.dailyTimeLimitMins.toFloat()) }
    var revealTries by remember(controls) { mutableStateOf(controls.answerRevealTries) }
    var frustrationGuard by remember(controls) { mutableStateOf(controls.frustrationGuard) }
    var reasoningVisibility by remember(controls) { mutableStateOf(controls.reasoningVisibility) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Sync Notification (FR-4)
        item {
            Surface(
                color = GreenSuccess.copy(alpha = 0.15f),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("⚡", fontSize = 16.sp)
                    Text(
                        if (syncLatency != null) "Applied on Wini in ${syncLatency}s (<30s rule met)"
                        else "Rule changes sync to Wini within 30 seconds when online.",
                        fontSize = 12.sp,
                        color = GreenSuccess,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }

        // Instant Pause Button
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = RedDanger.copy(alpha = 0.1f)),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .padding(14.dp)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Pause Wini Now", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("Instantly locks Wini screen & pauses session", fontSize = 11.sp, color = Color.Gray)
                    }
                    Button(
                        onClick = onPauseToggle,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (controls.pausedNow) GreenSuccess else RedDanger
                        )
                    ) {
                        Text(if (controls.pausedNow) "Resume" else "Pause Wini")
                    }
                }
            }
        }

        // Daily Time Limit
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Daily Time Limit", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("${timeLimit.toInt()} Mins", fontWeight = FontWeight.Bold, color = IndigoPrimary)
                    }
                    Slider(
                        value = timeLimit,
                        onValueChange = { timeLimit = it },
                        valueRange = 15f..120f,
                        steps = 6,
                        onValueChangeFinished = {
                            onUpdate(controls.copy(dailyTimeLimitMins = timeLimit.toInt()))
                        }
                    )
                }
            }
        }

        // Tutoring Style Header
        item {
            Text("Probe-First Tutoring Controls (P0)", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        }

        // FR-5: Answer reveal tries (1 to 3)
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text("Tries Before Answer Reveal (1 to 3)", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text("Wini always reveals the answer after N wrong tries so the child is never stuck.", fontSize = 11.sp, color = Color.Gray)
                    Spacer(modifier = Modifier.height(10.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf(1, 2, 3).forEach { tries ->
                            FilterChip(
                                selected = (revealTries == tries),
                                onClick = {
                                    revealTries = tries
                                    onUpdate(controls.copy(answerRevealTries = tries))
                                },
                                label = { Text("$tries ${if (tries == 1) "Try" else "Tries"}") },
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
        }

        // FR-8: Frustration Guard Toggle
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Row(
                    modifier = Modifier
                        .padding(14.dp)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Frustration Guard (Default ON)", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("After repeated wrong answers, Wini switches from probing to hints.", fontSize = 11.sp, color = Color.Gray)
                    }
                    Switch(
                        checked = frustrationGuard,
                        onCheckedChange = {
                            frustrationGuard = it
                            onUpdate(controls.copy(frustrationGuard = it))
                        }
                    )
                }
            }
        }

        // Reasoning Visibility Toggle
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Row(
                    modifier = Modifier
                        .padding(14.dp)
                        .fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Child Reasoning Visibility", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("Display stated reasons behind wrong answers on parent dashboard.", fontSize = 11.sp, color = Color.Gray)
                    }
                    Switch(
                        checked = reasoningVisibility,
                        onCheckedChange = {
                            reasoningVisibility = it
                            onUpdate(controls.copy(reasoningVisibility = it))
                        }
                    )
                }
            }
        }
    }
}
