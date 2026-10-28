package com.example.hierarchicalmanipulationapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.hierarchicalmanipulationapp.ui.components.ErrorState
import com.example.hierarchicalmanipulationapp.ui.components.LoadingState
import com.example.hierarchicalmanipulationapp.viewmodel.ExperimentUiState
import com.example.hierarchicalmanipulationapp.viewmodel.ExperimentViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExperimentsScreen(
    viewModel: ExperimentViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Experiments Benchmark") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize()) {
            when (val state = uiState) {
                is ExperimentUiState.Loading -> LoadingState()
                is ExperimentUiState.Error -> ErrorState(state.message)
                is ExperimentUiState.Success -> {
                    if (state.experiments.isEmpty()) {
                        Text("No benchmark results available yet.", modifier = Modifier.padding(16.dp))
                    } else {
                        LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                            items(state.experiments) { exp ->
                                Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                    Column(modifier = Modifier.padding(16.dp)) {
                                        Text("System: ${exp.system}", style = MaterialTheme.typography.titleMedium)
                                        Text("Scenario: ${exp.scenario}")
                                        Text("Horizon: ${exp.horizon}")
                                        Text("Failure Rate: ${exp.failure_rate}")
                                        Text("Task Success: ${exp.task_success}")
                                        Text("Execution Time: ${exp.execution_time}s")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
