package com.example.hierarchicalmanipulationapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.hierarchicalmanipulationapp.ui.components.ErrorState
import com.example.hierarchicalmanipulationapp.ui.components.LoadingState
import com.example.hierarchicalmanipulationapp.ui.components.StatusBadge
import com.example.hierarchicalmanipulationapp.viewmodel.DashboardUiState
import com.example.hierarchicalmanipulationapp.viewmodel.DashboardViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel,
    onNavigateToCreateTask: () -> Unit,
    onNavigateToExperiments: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ManipulaPlan Dashboard") }
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onNavigateToCreateTask,
                text = { Text("New Task") },
                icon = { }
            )
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize()) {
            when (val state = uiState) {
                is DashboardUiState.Loading -> LoadingState()
                is DashboardUiState.Error -> ErrorState(state.message)
                is DashboardUiState.Success -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp)
                    ) {
                        Card(
                            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("System Status", style = MaterialTheme.typography.titleMedium)
                                Spacer(modifier = Modifier.height(8.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("API Service:")
                                    StatusBadge(status = state.health.status)
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("Simulation:")
                                    StatusBadge(status = if (state.health.simulation_available) "AVAILABLE" else "UNAVAILABLE")
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("LLM Planner:")
                                    StatusBadge(status = if (state.health.llm_enabled) "AVAILABLE" else "UNAVAILABLE")
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                Text("Version: ${state.health.version}", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                        
                        // Placeholder for Tasks / Metrics / Navigation
                        Button(onClick = { viewModel.checkHealth() }, modifier = Modifier.fillMaxWidth()) {
                            Text("Refresh Status")
                        }
                    }
                }
            }
        }
    }
}
