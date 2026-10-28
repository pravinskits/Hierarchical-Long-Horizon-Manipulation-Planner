package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.FailureEventResponse
import com.example.hierarchicalmanipulationapp.data.model.RecoveryEventResponse
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import com.example.hierarchicalmanipulationapp.data.repository.TaskRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class RecoveryUiState {
    object Loading : RecoveryUiState()
    data class Success(
        val failures: List<FailureEventResponse>,
        val recoveries: List<RecoveryEventResponse>
    ) : RecoveryUiState()
    data class Error(val message: String) : RecoveryUiState()
}

class RecoveryViewModel(private val repository: TaskRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<RecoveryUiState>(RecoveryUiState.Loading)
    val uiState: StateFlow<RecoveryUiState> = _uiState.asStateFlow()

    fun fetchFailuresAndRecoveries(taskId: String) {
        _uiState.value = RecoveryUiState.Loading
        viewModelScope.launch {
            val failureResult = repository.getFailures(taskId)
            val recoveryResult = repository.getRecoveries(taskId)

            if (failureResult is Resource.Success && recoveryResult is Resource.Success) {
                _uiState.value = RecoveryUiState.Success(failureResult.data!!, recoveryResult.data!!)
            } else {
                _uiState.value = RecoveryUiState.Error("Failed to load recovery data")
            }
        }
    }
}
