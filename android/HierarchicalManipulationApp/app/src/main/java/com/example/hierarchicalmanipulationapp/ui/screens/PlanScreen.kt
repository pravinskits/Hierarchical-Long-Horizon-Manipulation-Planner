package com.example.hierarchicalmanipulationapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.hierarchicalmanipulationapp.ui.components.ErrorState
import com.example.hierarchicalmanipulationapp.ui.components.LoadingState
import com.example.hierarchicalmanipulationapp.ui.components.StatusBadge
import com.example.hierarchicalmanipulationapp.viewmodel.PlanUiState
import com.example.hierarchicalmanipulationapp.viewmodel.PlanViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlanScreen(
    taskId: String,
    viewModel: PlanViewModel,
    onNavigateToExecution: (String) -> Unit,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(taskId) {
        if (uiState is PlanUiState.Idle) {
            viewModel.generatePlan(taskId)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Task Plan") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        bottomBar = {
            if (uiState is PlanUiState.Success) {
                BottomAppBar {
                    Button(
                        onClick = { onNavigateToExecution(taskId) },
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp)
                    ) {
                        Text("Execute Plan")
                    }
                }
            }
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize()) {
            when (val state = uiState) {
                is PlanUiState.Loading -> LoadingState()
                is PlanUiState.Error -> {
                    Column {
                        ErrorState(state.message, modifier = Modifier.weight(1f))
                        Button(onClick = { viewModel.generatePlan(taskId) }, modifier = Modifier.padding(16.dp).fillMaxWidth()) {
                            Text("Retry")
                        }
                    }
                }
                is PlanUiState.Success -> {
                    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                        Card(modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Task ID: ${state.plan.task_id}", style = MaterialTheme.typography.bodySmall)
                                Text("Planner: ${state.plan.planner.uppercase()}", fontWeight = FontWeight.Bold)
                            }
                        }

                        Text("Subgoals Timeline", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(bottom = 8.dp))
                        
                        LazyColumn(modifier = Modifier.fillMaxSize()) {
                            itemsIndexed(state.plan.subgoals) { index, subgoal ->
                                Card(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                                ) {
                                    Column(modifier = Modifier.padding(12.dp)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                text = "${index + 1}. ${subgoal.skill_name}",
                                                style = MaterialTheme.typography.titleMedium,
                                                fontWeight = FontWeight.Bold
                                            )
                                            StatusBadge(status = subgoal.status)
                                        }
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text("ID: ${subgoal.id}", style = MaterialTheme.typography.bodySmall)
                                        subgoal.parameters?.let { params ->
                                            Text("Params: $params", style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                }
                                if (index < state.plan.subgoals.size - 1) {
                                    Icon(
                                        Icons.Filled.ArrowDownward,
                                        contentDescription = "Next",
                                        modifier = Modifier.padding(vertical = 4.dp).align(Alignment.CenterHorizontally)
                                    )
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
