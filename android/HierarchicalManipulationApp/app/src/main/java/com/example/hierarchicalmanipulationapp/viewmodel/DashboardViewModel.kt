package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.HealthResponse
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import com.example.hierarchicalmanipulationapp.data.repository.SystemRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class DashboardUiState {
    object Loading : DashboardUiState()
    data class Success(val health: HealthResponse) : DashboardUiState()
    data class Error(val message: String) : DashboardUiState()
}

class DashboardViewModel(private val repository: SystemRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<DashboardUiState>(DashboardUiState.Loading)
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        checkHealth()
    }

    fun checkHealth() {
        _uiState.value = DashboardUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getSystemHealth()) {
                is Resource.Success -> {
                    _uiState.value = DashboardUiState.Success(result.data!!)
                }
                is Resource.Error -> {
                    _uiState.value = DashboardUiState.Error(result.message ?: "Unknown error")
                }
                else -> {}
            }
        }
    }
}
