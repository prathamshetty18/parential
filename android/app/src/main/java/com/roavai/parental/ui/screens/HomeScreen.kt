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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.roavai.parental.data.model.LearnerModel
import com.roavai.parental.data.model.SubjectMastery
import com.roavai.parental.ui.theme.GreenSuccess
import com.roavai.parental.ui.theme.IndigoPrimary
import com.roavai.parental.ui.viewmodel.DashboardUiState
import com.roavai.parental.ui.viewmodel.DashboardViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: DashboardViewModel
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ROAVAI Cloud Tutor Dashboard", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(MaterialTheme.colorScheme.background)
        ) {
            when (val state = uiState) {
                is DashboardUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is DashboardUiState.Error -> {
                    Text(
                        text = "Error: ${state.message}",
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
                is DashboardUiState.Success -> {
                    DashboardContent(model = state.learnerModel)
                }
            }
        }
    }
}

@Composable
private fun DashboardContent(model: LearnerModel) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Daily Usage Card
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Time Today", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Text("28 / 45 mins", fontWeight = FontWeight.Bold, color = IndigoPrimary, fontSize = 14.sp)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    LinearProgressIndicator(
                        progress = 0.62f,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(8.dp),
                        color = IndigoPrimary,
                        trackColor = MaterialTheme.colorScheme.surface
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("17 mins remaining before daily bedtime limit", fontSize = 12.sp, color = Color.Gray)
                }
            }
        }

        // Streak & Self Correction Rate
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Learning Streak", fontSize = 12.sp, color = Color.Gray)
                        Text("🔥 ${model.streakDays} Days", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    }
                }

                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Self-Correction Rate", fontSize = 12.sp, color = Color.Gray)
                        Text("🎯 ${model.selfCorrectionRate}%", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = GreenSuccess)
                        Text("Fixed after Wini probe", fontSize = 10.sp, color = Color.Gray)
                    }
                }
            }
        }

        // Subject Mastery Title
        item {
            Text("Subject Mastery (Cloud Tutor Model)", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        }

        items(model.mastery) { subject ->
            SubjectMasteryCard(subject)
        }
    }
}

@Composable
fun SubjectMasteryCard(mastery: SubjectMastery) {
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
                Text(mastery.subject, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text("${mastery.score}%", fontWeight = FontWeight.Bold, color = IndigoPrimary)
            }
            Spacer(modifier = Modifier.height(6.dp))
            LinearProgressIndicator(
                progress = mastery.score / 100f,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp),
                color = IndigoPrimary
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text("📈 ${mastery.trend} this week", fontSize = 11.sp, color = Color.Gray)
        }
    }
}
