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
import com.example.hierarchicalmanipulationapp.viewmodel.RecoveryUiState
import com.example.hierarchicalmanipulationapp.viewmodel.RecoveryViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FailureScreen(
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
                title = { Text("Failures") },
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
                    if (state.failures.isEmpty()) {
                        Text("No failures recorded.", modifier = Modifier.padding(16.dp))
                    } else {
                        LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                            items(state.failures) { failure ->
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                                ) {
                                    Column(modifier = Modifier.padding(16.dp)) {
                                        Text(failure.failure_type, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onErrorContainer)
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text("Skill: ${failure.skill_name}")
                                        Text("Message: ${failure.message}")
                                        
                                        // Demonstrate distinction between controlled vs natural
                                        val isControlled = failure.message.contains("inject", ignoreCase = true)
                                        Text("Source: ${if (isControlled) "CONTROLLED INJECTION" else "NATURAL FAILURE"}",
                                            color = if (isControlled) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                                        )
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
