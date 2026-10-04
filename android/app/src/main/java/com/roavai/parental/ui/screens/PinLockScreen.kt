package com.roavai.parental.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.roavai.parental.ui.theme.IndigoPrimary

@Composable
fun PinLockScreen(
    onUnlocked: () -> Unit
) {
    var enteredPin by remember { mutableStateOf("") }
    var errorText by remember { mutableStateOf<String?>(null) }

    fun addDigit(digit: String) {
        if (enteredPin.length < 4) {
            enteredPin += digit
            errorText = null
        }
        if (enteredPin.length == 4) {
            if (enteredPin == "1234") {
                onUnlocked()
            } else {
                errorText = "Incorrect PIN code. Try 1234."
                enteredPin = ""
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            Text("🔒", fontSize = 48.sp)
            Text("FR-10 App Security Lock", fontWeight = FontWeight.Bold, fontSize = 20.sp)
            Text("App requires PIN after 1 min in background", fontSize = 12.sp, color = Color.Gray)

            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                repeat(4) { idx ->
                    Surface(
                        modifier = Modifier.size(16.dp),
                        shape = CircleShape,
                        color = if (idx < enteredPin.length) IndigoPrimary else Color.Gray.copy(alpha = 0.3f)
                    ) {}
                }
            }

            errorText?.let {
                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }

            // Keypad
            val buttons = listOf(
                listOf("1", "2", "3"),
                listOf("4", "5", "6"),
                listOf("7", "8", "9"),
                listOf("☝️", "0", "⌫")
            )

            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                buttons.forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        row.forEach { btnText ->
                            OutlinedButton(
                                onClick = {
                                    when (btnText) {
                                        "⌫" -> if (enteredPin.isNotEmpty()) enteredPin = enteredPin.dropLast(1)
                                        "☝️" -> onUnlocked() // Biometrics bypass
                                        else -> addDigit(btnText)
                                    }
                                },
                                modifier = Modifier.size(64.dp),
                                shape = CircleShape
                            ) {
                                Text(btnText, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            TextButton(onClick = { onUnlocked() }) {
                Text("Demo Auto-Unlock (1234)", color = IndigoPrimary)
            }
        }
    }
}
