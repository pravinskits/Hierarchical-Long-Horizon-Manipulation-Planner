package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hierarchicalmanipulationapp.data.model.ExperimentItem
import com.example.hierarchicalmanipulationapp.data.repository.ExperimentRepository
import com.example.hierarchicalmanipulationapp.data.repository.Resource
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class ExperimentUiState {
    object Loading : ExperimentUiState()
    data class Success(val experiments: List<ExperimentItem>) : ExperimentUiState()
    data class Error(val message: String) : ExperimentUiState()
}

class ExperimentViewModel(private val repository: ExperimentRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<ExperimentUiState>(ExperimentUiState.Loading)
    val uiState: StateFlow<ExperimentUiState> = _uiState.asStateFlow()

    init {
        fetchExperiments()
    }

    fun fetchExperiments() {
        _uiState.value = ExperimentUiState.Loading
        viewModelScope.launch {
            when (val result = repository.getExperiments()) {
                is Resource.Success -> {
                    _uiState.value = ExperimentUiState.Success(result.data!!.experiments)
                }
                is Resource.Error -> {
                    _uiState.value = ExperimentUiState.Error(result.message ?: "Failed to load experiments")
                }
                else -> {}
            }
        }
    }
}
