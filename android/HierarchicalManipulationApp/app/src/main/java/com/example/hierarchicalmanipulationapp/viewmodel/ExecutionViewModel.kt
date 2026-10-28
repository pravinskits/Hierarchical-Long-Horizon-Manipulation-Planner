package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.TaskStateResponse
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import com.example.hierarchicalmanipulationapp.data.repository.TaskRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class ExecutionUiState {
    object Idle : ExecutionUiState()
    object Loading : ExecutionUiState()
    data class Running(val state: TaskStateResponse) : ExecutionUiState()
    data class Completed(val state: TaskStateResponse) : ExecutionUiState()
    data class Error(val message: String) : ExecutionUiState()
}

class ExecutionViewModel(private val repository: TaskRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<ExecutionUiState>(ExecutionUiState.Idle)
    val uiState: StateFlow<ExecutionUiState> = _uiState.asStateFlow()

    private var pollingJob: Job? = null

    fun startExecution(taskId: String) {
        _uiState.value = ExecutionUiState.Loading
        viewModelScope.launch {
            val result = repository.executeTask(taskId)
            if (result is Resource.Success) {
                startPolling(taskId)
            } else {
                _uiState.value = ExecutionUiState.Error(result.message ?: "Failed to start execution")
            }
        }
    }

    fun startPolling(taskId: String) {
        stopPolling()
        pollingJob = viewModelScope.launch {
            while (true) {
                when (val result = repository.getTaskState(taskId)) {
                    is Resource.Success -> {
                        val state = result.data!!
                        if (state.status == "COMPLETED" || state.status == "FAILED" || state.status == "ABORTED") {
                            _uiState.value = ExecutionUiState.Completed(state)
                            break
                        } else {
                            _uiState.value = ExecutionUiState.Running(state)
                        }
                    }
                    is Resource.Error -> {
                        _uiState.value = ExecutionUiState.Error(result.message ?: "Failed to poll task state")
                        break
                    }
                    else -> {}
                }
                delay(1500) // Poll every 1.5 seconds
            }
        }
    }

    fun abortTask(taskId: String) {
        viewModelScope.launch {
            repository.abortTask(taskId)
            stopPolling()
            fetchFinalState(taskId)
        }
    }

    fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }

    private suspend fun fetchFinalState(taskId: String) {
        when (val result = repository.getTaskState(taskId)) {
            is Resource.Success -> {
                _uiState.value = ExecutionUiState.Completed(result.data!!)
            }
            is Resource.Error -> {
                _uiState.value = ExecutionUiState.Error("Failed to fetch final state")
            }
            else -> {}
        }
    }

    override fun onCleared() {
        super.onCleared()
        stopPolling()
    }
}
