package com.example.hierarchicalmanipulationapp.viewmodel

import androidx.lifecycle.ViewModel
import com.example.hierarchicalmanipulationapp.data.api.ApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class SettingsViewModel : ViewModel() {
    private val _baseUrl = MutableStateFlow(ApiClient.getBaseUrl())
    val baseUrl: StateFlow<String> = _baseUrl.asStateFlow()

    fun updateBaseUrl(newUrl: String) {
        ApiClient.setBaseUrl(newUrl)
        _baseUrl.value = ApiClient.getBaseUrl()
    }
}
