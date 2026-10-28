package com.example.hierarchicalmanipulationapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.hierarchicalmanipulationapp.ui.components.ErrorState
import com.example.hierarchicalmanipulationapp.ui.components.LoadingState
import com.example.hierarchicalmanipulationapp.ui.components.StatusBadge
import com.example.hierarchicalmanipulationapp.viewmodel.ExecutionUiState
import com.example.hierarchicalmanipulationapp.viewmodel.ExecutionViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskExecutionScreen(
    taskId: String,
    viewModel: ExecutionViewModel,
    onNavigateToDetail: (String) -> Unit,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(taskId) {
        if (uiState is ExecutionUiState.Idle) {
            viewModel.startExecution(taskId)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Execution: ${taskId.take(8)}...") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        bottomBar = {
            BottomAppBar {
                if (uiState is ExecutionUiState.Running) {
                    Button(
                        onClick = { viewModel.abortTask(taskId) },
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                    ) {
                        Text("Abort Task")
                    }
                } else if (uiState is ExecutionUiState.Completed) {
                    Button(
                        onClick = { onNavigateToDetail(taskId) },
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp)
                    ) {
                        Text("View Details")
                    }
                }
            }
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize()) {
            when (val state = uiState) {
                is ExecutionUiState.Loading -> LoadingState()
                is ExecutionUiState.Error -> ErrorState(state.message)
                is ExecutionUiState.Running, is ExecutionUiState.Completed -> {
                    val taskState = if (state is ExecutionUiState.Running) state.state else (state as ExecutionUiState.Completed).state
                    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("Status", style = MaterialTheme.typography.titleMedium)
                                    StatusBadge(status = taskState.status)
                                }
                                Spacer(modifier = Modifier.height(16.dp))
                                Text("Progress: ${(taskState.progress_percentage * 100).toInt()}%")
                                LinearProgressIndicator(
                                    progress = taskState.progress_percentage,
                                    modifier = Modifier.fillMaxWidth().height(8.dp)
                                )
                                Spacer(modifier = Modifier.height(16.dp))
                                Text("Current Subgoal", style = MaterialTheme.typography.titleSmall)
                                taskState.current_subgoal?.let { sg ->
                                    Text("${sg.skill_name} (${sg.status})", color = MaterialTheme.colorScheme.primary)
                                } ?: Text("None")
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Subgoal History", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))

                        LazyColumn {
                            items(taskState.completed_subgoals + taskState.failed_subgoals + taskState.pending_subgoals) { sg ->
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                                ) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth().padding(12.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column {
                                            Text(sg.skill_name, style = MaterialTheme.typography.bodyLarge)
                                            sg.error_message?.takeIf { it.isNotBlank() }?.let {
                                                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                                            }
                                        }
                                        StatusBadge(status = sg.status)
                                    }
                                }
                            }
                        }
                    }
                }
                else -> {}
            }
        }
    }
}
