package com.roavai.parental.data.model

import com.google.gson.annotations.SerializedName

data class TutoringControls(
    @SerializedName("dailyTimeLimitMins") val dailyTimeLimitMins: Int = 45,
    @SerializedName("timeSpentTodayMins") val timeSpentTodayMins: Int = 0,
    @SerializedName("pausedNow") val pausedNow: Boolean = false,
    @SerializedName("subjectAllowlist") val subjectAllowlist: List<String> = listOf("Math", "Science"),
    @SerializedName("contentLevel") val contentLevel: String = "Ages 7-9",
    // Probe-First Tutoring Controls (PRD 4.5)
    @SerializedName("answerRevealTries") val answerRevealTries: Int = 2, // 1 to 3
    @SerializedName("probeInputMode") val probeInputMode: String = "both", // voice | tap | both
    @SerializedName("frustrationGuard") val frustrationGuard: Boolean = true,
    @SerializedName("reasoningVisibility") val reasoningVisibility: Boolean = true,
    @SerializedName("lastSyncTimestamp") val lastSyncTimestamp: String? = null
)
