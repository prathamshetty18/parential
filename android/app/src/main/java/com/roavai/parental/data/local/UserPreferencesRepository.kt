package com.roavai.parental.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

@Singleton
class UserPreferencesRepository @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private object Keys {
        val PIN_CODE = stringPreferencesKey("pin_code")
        val BIOMETRIC_ENABLED = booleanPreferencesKey("biometric_enabled")
        val LAST_BACKGROUND_TIMESTAMP = longPreferencesKey("last_background_timestamp")
        val ACTIVE_CHILD_ID = stringPreferencesKey("active_child_id")
        val PARENTAL_CONSENT_RECORDED = booleanPreferencesKey("parental_consent_recorded")
    }

    val pinCode: Flow<String?> = context.dataStore.data.map { it[Keys.PIN_CODE] }
    val biometricEnabled: Flow<Boolean> = context.dataStore.data.map { it[Keys.BIOMETRIC_ENABLED] ?: false }
    val activeChildId: Flow<String> = context.dataStore.data.map { it[Keys.ACTIVE_CHILD_ID] ?: "child_leo" }
    val parentalConsentRecorded: Flow<Boolean> = context.dataStore.data.map { it[Keys.PARENTAL_CONSENT_RECORDED] ?: false }

    suspend fun savePinCode(pin: String) {
        context.dataStore.edit { it[Keys.PIN_CODE] = pin }
    }

    suspend fun setActiveChildId(childId: String) {
        context.dataStore.edit { it[Keys.ACTIVE_CHILD_ID] = childId }
    }

    suspend fun setParentalConsent(recorded: Boolean) {
        context.dataStore.edit { it[Keys.PARENTAL_CONSENT_RECORDED] = recorded }
    }

    suspend fun updateLastBackgroundTimestamp(timestamp: Long) {
        context.dataStore.edit { it[Keys.LAST_BACKGROUND_TIMESTAMP] = timestamp }
    }

    suspend fun shouldLockApp(): Boolean {
        var shouldLock = false
        context.dataStore.data.map { prefs ->
            val lastBackground = prefs[Keys.LAST_BACKGROUND_TIMESTAMP] ?: 0L
            val elapsedMs = System.currentTimeMillis() - lastBackground
            // FR-10: Require PIN/Biometrics if backgrounded over 1 minute (60,000 ms)
            shouldLock = elapsedMs > 60_000
        }
        return shouldLock
    }
}
