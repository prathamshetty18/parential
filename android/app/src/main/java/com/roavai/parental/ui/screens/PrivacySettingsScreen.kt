package com.roavai.parental.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.roavai.parental.ui.theme.RedDanger

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PrivacySettingsScreen() {
    var storeReasoning by remember { mutableStateOf(true) }
    var voiceData by remember { mutableStateOf(true) }
    var cameraExpression by remember { mutableStateOf(false) }
    var aiImprovement by remember { mutableStateOf(false) }

    var showDeleteDialog by remember { mutableStateOf(false) }
    var statusMessage by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Privacy & Data Control", fontWeight = FontWeight.Bold) }) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text("🛡️ Verifiable Consent & Minimisation", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text("No ads. Zero third-party tracking SDKs. Regulated under COPPA, DPDP Act 2023, GDPR.", fontSize = 11.sp, color = Color.Gray)
                }
            }

            // Consent Toggles
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    PrivacyToggleRow(
                        title = "Store Child Stated Reasoning",
                        desc = "Allows parent app to display reasoning behind wrong answers (FR-7)",
                        checked = storeReasoning,
                        onCheckedChange = { storeReasoning = it }
                    )
                    Divider(modifier = Modifier.padding(vertical = 8.dp))
                    PrivacyToggleRow(
                        title = "Voice Audio Processing",
                        desc = "Allow Wini to process voice responses for probe questions",
                        checked = voiceData,
                        onCheckedChange = { voiceData = it }
                    )
                    Divider(modifier = Modifier.padding(vertical = 8.dp))
                    PrivacyToggleRow(
                        title = "Camera & Expression Analysis",
                        desc = "Detect engagement/frustration via camera",
                        checked = cameraExpression,
                        onCheckedChange = { cameraExpression = it }
                    )
                    Divider(modifier = Modifier.padding(vertical = 8.dp))
                    PrivacyToggleRow(
                        title = "AI Model Improvement Opt-In",
                        desc = "Use anonymized data to improve Cloud Tutor models",
                        checked = aiImprovement,
                        onCheckedChange = { aiImprovement = it }
                    )
                }
            }

            // Actions
            Button(
                onClick = {
                    statusMessage = "📥 Export JSON triggered: Downloading child learner history."
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Text("Export Child Data (JSON)", color = MaterialTheme.colorScheme.onSurface)
            }

            Button(
                onClick = { showDeleteDialog = true },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = RedDanger.copy(alpha = 0.15f))
            ) {
                Text("Delete Child Profile & Purge Data", color = RedDanger, fontWeight = FontWeight.Bold)
            }

            statusMessage?.let { msg ->
                Text(msg, fontSize = 12.sp, color = Color.Gray, modifier = Modifier.padding(top = 8.dp))
            }
        }
    }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("FR-9: Confirm Profile Deletion") },
            text = {
                Text("Deleting this profile will immediately unpair Wini and permanently delete all stored reasoning and learner history within 30 days.")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showDeleteDialog = false
                        statusMessage = "✅ FR-9 Confirmed: Child profile deleted. Learner data scheduled for purge within 30 days."
                    }
                ) {
                    Text("Delete Profile", color = RedDanger, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun PrivacyToggleRow(
    title: String,
    desc: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
            Text(desc, fontSize = 10.sp, color = Color.Gray)
        }
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}
