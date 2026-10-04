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
import com.roavai.parental.ui.theme.IndigoPrimary
import com.roavai.parental.ui.theme.RedDanger

@Composable
fun OnboardingScreen(
    onConsentCompleted: () -> Unit
) {
    var consentChecked by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var childName by remember { mutableStateOf("") }
    var childAge by remember { mutableStateOf("8") }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp)
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.Center),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Text("👋 Welcome to ROAVAI", fontWeight = FontWeight.Bold, fontSize = 22.sp)
                Text("Set up your child's profile & pair Wini Cloud Tutor Robot", fontSize = 13.sp, color = Color.Gray)

                OutlinedTextField(
                    value = childName,
                    onValueChange = { childName = it },
                    label = { Text("Child Name / Nickname") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = childAge,
                    onValueChange = { childAge = it },
                    label = { Text("Child Age (e.g. 8)") },
                    modifier = Modifier.fillMaxWidth()
                )

                // FR-1 Mandatory Parental Consent Checkbox
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Checkbox(
                        checked = consentChecked,
                        onCheckedChange = {
                            consentChecked = it
                            errorMessage = null
                        }
                    )
                    Text(
                        "FR-1: I record verifiable parental consent for child data collection under COPPA / DPDP / GDPR.",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }

                errorMessage?.let {
                    Text(it, color = RedDanger, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }

                Button(
                    onClick = {
                        if (!consentChecked) {
                            errorMessage = "FR-1 Error: Parental consent must be recorded before profile creation."
                        } else if (childName.isBlank()) {
                            errorMessage = "Please enter a valid child name."
                        } else {
                            onConsentCompleted()
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = IndigoPrimary)
                ) {
                    Text("Record Consent & Create Profile")
                }
            }
        }
    }
}
