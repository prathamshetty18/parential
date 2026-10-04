package com.roavai.parental.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.roavai.parental.data.local.UserPreferencesRepository
import com.roavai.parental.data.model.LearnerModel
import com.roavai.parental.data.repository.LearnerModelRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface DashboardUiState {
    object Loading : DashboardUiState
    data class Success(val learnerModel: LearnerModel) : DashboardUiState
    data class Error(val message: String) : DashboardUiState
}

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val learnerModelRepository: LearnerModelRepository,
    private val userPreferencesRepository: UserPreferencesRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<DashboardUiState>(DashboardUiState.Loading)
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            userPreferencesRepository.activeChildId.collect { childId ->
                loadLearnerModel(childId)
            }
        }
    }

    fun loadLearnerModel(childId: String) {
        viewModelScope.launch {
            _uiState.value = DashboardUiState.Loading
            val result = learnerModelRepository.fetchLearnerModel(childId)
            result.onSuccess { model ->
                _uiState.value = DashboardUiState.Success(model)
            }.onFailure { err ->
                // FR-3: Instant cached fallback loading under 1s
                _uiState.value = DashboardUiState.Error(err.message ?: "Failed to fetch learner model")
            }
        }
    }
}
