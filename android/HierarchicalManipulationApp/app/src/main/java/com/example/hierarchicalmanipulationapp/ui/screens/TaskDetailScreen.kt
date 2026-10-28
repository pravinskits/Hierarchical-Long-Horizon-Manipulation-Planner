package com.example.hierarchicalmanipulationapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskDetailScreen(
    taskId: String,
    viewModel: androidx.lifecycle.ViewModel, // Could be ExecutionViewModel for getting status
    onNavigateToFailures: (String) -> Unit,
    onNavigateToRecovery: (String) -> Unit,
    onNavigateBack: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Task Details") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding).padding(16.dp)) {
            Text("Overview", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(16.dp))
            Button(onClick = { onNavigateToFailures(taskId) }, modifier = Modifier.fillMaxWidth()) {
                Text("View Failures")
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(onClick = { onNavigateToRecovery(taskId) }, modifier = Modifier.fillMaxWidth()) {
                Text("View Recovery History")
            }
        }
    }
}
