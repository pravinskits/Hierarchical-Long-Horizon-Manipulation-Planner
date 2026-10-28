package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.PlanResponse
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import com.example.hierarchicalmanipulationapp.data.repository.TaskRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class PlanUiState {
    object Idle : PlanUiState()
    object Loading : PlanUiState()
    data class Success(val plan: PlanResponse) : PlanUiState()
    data class Error(val message: String) : PlanUiState()
}

class PlanViewModel(private val repository: TaskRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<PlanUiState>(PlanUiState.Idle)
    val uiState: StateFlow<PlanUiState> = _uiState.asStateFlow()

    fun generatePlan(taskId: String, planner: String = "deterministic") {
        _uiState.value = PlanUiState.Loading
        viewModelScope.launch {
            when (val result = repository.generatePlan(taskId, planner)) {
                is Resource.Success -> {
                    _uiState.value = PlanUiState.Success(result.data!!)
                }
                is Resource.Error -> {
                    _uiState.value = PlanUiState.Error(result.message ?: "Failed to generate plan")
                }
                else -> {}
            }
        }
    }

    fun resetState() {
        _uiState.value = PlanUiState.Idle
    }
}
