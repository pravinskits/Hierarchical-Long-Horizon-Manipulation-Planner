package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.TaskResponse
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import com.example.hierarchicalmanipulationapp.data.repository.TaskRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class TaskCreateUiState {
    object Idle : TaskCreateUiState()
    object Loading : TaskCreateUiState()
    data class Success(val task: TaskResponse) : TaskCreateUiState()
    data class Error(val message: String) : TaskCreateUiState()
}

class TaskViewModel(private val repository: TaskRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<TaskCreateUiState>(TaskCreateUiState.Idle)
    val uiState: StateFlow<TaskCreateUiState> = _uiState.asStateFlow()

    fun createTask(goal: String) {
        if (goal.isBlank()) {
            _uiState.value = TaskCreateUiState.Error("Goal cannot be empty")
            return
        }

        _uiState.value = TaskCreateUiState.Loading
        viewModelScope.launch {
            when (val result = repository.createTask(goal)) {
                is Resource.Success -> {
                    _uiState.value = TaskCreateUiState.Success(result.data!!)
                }
                is Resource.Error -> {
                    _uiState.value = TaskCreateUiState.Error(result.message ?: "Failed to create task")
                }
                else -> {}
            }
        }
    }
    
    fun resetState() {
        _uiState.value = TaskCreateUiState.Idle
    }
}
