package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.CreationExtras
import com.example.hierarchicalmanipulationapp.data.api.ApiClient
import com.example.hierarchicalmanipulationapp.data.repository.ExperimentRepository
import com.example.hierarchicalmanipulationapp.data.repository.SystemRepository
import com.example.hierarchicalmanipulationapp.data.repository.TaskRepository

object AppViewModelProvider {
    private val apiService by lazy { ApiClient.getApiService() }
    val systemRepository by lazy { SystemRepository(apiService) }
    val taskRepository by lazy { TaskRepository(apiService) }
    val experimentRepository by lazy { ExperimentRepository(apiService) }

    val Factory = object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>, extras: CreationExtras): T {
            return when {
                modelClass.isAssignableFrom(DashboardViewModel::class.java) -> {
                    DashboardViewModel(systemRepository) as T
                }
                modelClass.isAssignableFrom(TaskViewModel::class.java) -> {
                    TaskViewModel(taskRepository) as T
                }
                modelClass.isAssignableFrom(PlanViewModel::class.java) -> {
                    PlanViewModel(taskRepository) as T
                }
                modelClass.isAssignableFrom(ExecutionViewModel::class.java) -> {
                    ExecutionViewModel(taskRepository) as T
                }
                modelClass.isAssignableFrom(RecoveryViewModel::class.java) -> {
                    RecoveryViewModel(taskRepository) as T
                }
                modelClass.isAssignableFrom(ExperimentViewModel::class.java) -> {
                    ExperimentViewModel(experimentRepository) as T
                }
                modelClass.isAssignableFrom(SettingsViewModel::class.java) -> {
                    SettingsViewModel() as T
                }
                else -> throw IllegalArgumentException("Unknown ViewModel class")
            }
        }
    }
}
