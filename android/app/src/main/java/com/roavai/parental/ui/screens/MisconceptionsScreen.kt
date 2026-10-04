package com.roavai.parental.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.roavai.parental.data.model.Misconception
import com.roavai.parental.ui.theme.AmberWarning
import com.roavai.parental.ui.theme.GreenSuccess
import com.roavai.parental.ui.theme.IndigoPrimary
import com.roavai.parental.ui.viewmodel.DashboardUiState
import com.roavai.parental.ui.viewmodel.DashboardViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MisconceptionsScreen(
    viewModel: DashboardViewModel
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Child Reasoning & Misconceptions", fontWeight = FontWeight.Bold) }
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
                is DashboardUiState.Success -> {
                    val list = state.learnerModel.misconceptions
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        item {
                            Card(
                                colors = CardDefaults.cardColors(containerColor = IndigoPrimary.copy(alpha = 0.1f))
                            ) {
                                Row(
                                    modifier = Modifier.padding(12.dp),
                                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                                ) {
                                    Text("🧠", fontSize = 20.sp)
                                    Text(
                                        "Cloud Tutor probe questions find the child's underlying misconception when wrong options are picked.",
                                        fontSize = 12.sp
                                    )
                                }
                            }
                        }

                        items(list) { misconception ->
                            MisconceptionCardItem(misconception)
                        }
                    }
                }
                else -> {
                    CircularProgressIndicator(modifier = Modifier.padding(32.dp))
                }
            }
        }
    }
}

@Composable
fun MisconceptionCardItem(m: Misconception) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Surface(
                    color = AmberWarning.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(
                        m.subject,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = AmberWarning
                    )
                }
                Text(m.date, fontSize = 10.sp, color = Color.Gray)
            }

            Spacer(modifier = Modifier.height(8.dp))
            Text(m.concept, fontWeight = FontWeight.Bold, fontSize = 15.sp)
            Spacer(modifier = Modifier.height(4.dp))
            Text("Question: ${m.questionAsked}", fontSize = 12.sp, color = Color.Gray)
            Text("Child Picked: ${m.childChoice}", fontSize = 12.sp, color = Color.Gray)

            Spacer(modifier = Modifier.height(10.dp))
            // FR-6: Child Stated Reason
            Surface(
                color = MaterialTheme.colorScheme.surface,
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(10.dp)) {
                    Text("🗣️ Child Stated Reason (from Wini Probe):", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = IndigoPrimary)
                    Spacer(modifier = Modifier.height(2.dp))
                    Text("\"${m.childStatedReason}\"", fontSize = 12.sp, fontStyle = FontStyle.Italic)
                }
            }

            Spacer(modifier = Modifier.height(10.dp))
            // Parent Tip Box
            Surface(
                color = GreenSuccess.copy(alpha = 0.1f),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(10.dp)) {
                    Text("💡 Parent Tip: ", fontWeight = FontWeight.Bold, fontSize = 11.sp, color = GreenSuccess)
                    Text(m.parentTip, fontSize = 11.sp, color = GreenSuccess)
                }
            }
        }
    }
}
