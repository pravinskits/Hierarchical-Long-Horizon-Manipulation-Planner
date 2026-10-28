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
import com.example.hierarchicalmanipulationapp.ui.components.StatusBadge
import com.example.hierarchicalmanipulationapp.viewmodel.RecoveryUiState
import com.example.hierarchicalmanipulationapp.viewmodel.RecoveryViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecoveryScreen(
    taskId: String,
    viewModel: RecoveryViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(taskId) {
        viewModel.fetchFailuresAndRecoveries(taskId)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Recovery History") },
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
                is RecoveryUiState.Loading -> LoadingState()
                is RecoveryUiState.Error -> ErrorState(state.message)
                is RecoveryUiState.Success -> {
                    if (state.recoveries.isEmpty()) {
                        Text("No recoveries recorded.", modifier = Modifier.padding(16.dp))
                    } else {
                        LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                            items(state.recoveries) { recovery ->
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                                ) {
                                    Column(modifier = Modifier.padding(16.dp)) {
                                        Text("Strategy: ${recovery.strategy}", style = MaterialTheme.typography.titleMedium)
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text("Failure Type: ${recovery.failure_type}")
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween
                                        ) {
                                            Text("Result:")
                                            StatusBadge(status = if (recovery.success) "SUCCESS" else "FAILURE")
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
}
