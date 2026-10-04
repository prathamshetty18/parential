package com.roavai.parental.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.roavai.parental.data.local.UserPreferencesRepository
import com.roavai.parental.data.model.TutoringControls
import com.roavai.parental.data.repository.ControlsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface ControlsUiState {
    object Loading : ControlsUiState
    data class Success(val controls: TutoringControls, val syncLatencySeconds: Double?) : ControlsUiState
    data class Error(val message: String) : ControlsUiState
}

@HiltViewModel
class ControlsViewModel @Inject constructor(
    private val controlsRepository: ControlsRepository,
    private val userPreferencesRepository: UserPreferencesRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<ControlsUiState>(ControlsUiState.Loading)
    val uiState: StateFlow<ControlsUiState> = _uiState.asStateFlow()

    private var currentChildId: String = "child_leo"

    init {
        viewModelScope.launch {
            userPreferencesRepository.activeChildId.collect { childId ->
                currentChildId = childId
                fetchControls(childId)
            }
        }
    }

    fun fetchControls(childId: String = currentChildId) {
        viewModelScope.launch {
            _uiState.value = ControlsUiState.Loading
            val res = controlsRepository.getControls(childId)
            res.onSuccess { controls ->
                _uiState.value = ControlsUiState.Success(controls, null)
            }.onFailure { err ->
                _uiState.value = ControlsUiState.Error(err.message ?: "Error loading controls")
            }
        }
    }

    fun updateControls(newControls: TutoringControls) {
        val startTime = System.currentTimeMillis()
        viewModelScope.launch {
            val res = controlsRepository.updateControls(currentChildId, newControls)
            val elapsedSec = (System.currentTimeMillis() - startTime) / 1000.0
            res.onSuccess {
                // FR-4: Confirmed sync to Wini within 30 seconds
                _uiState.value = ControlsUiState.Success(newControls, elapsedSec)
            }.onFailure { err ->
                _uiState.value = ControlsUiState.Error(err.message ?: "Failed to update rules")
            }
        }
    }

    fun togglePauseWini() {
        val currentState = (_uiState.value as? ControlsUiState.Success)?.controls ?: return
        val updated = currentState.copy(pausedNow = !currentState.pausedNow)
        updateControls(updated)
    }
}
