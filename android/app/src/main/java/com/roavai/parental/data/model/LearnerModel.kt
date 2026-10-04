package com.roavai.parental.data.model

import com.google.gson.annotations.SerializedName

data class LearnerModel(
    @SerializedName("streakDays") val streakDays: Int = 0,
    @SerializedName("selfCorrectionRate") val selfCorrectionRate: Int = 0,
    @SerializedName("topicsCoveredToday") val topicsCoveredToday: List<String> = emptyList(),
    @SerializedName("mastery") val mastery: List<SubjectMastery> = emptyList(),
    @SerializedName("misconceptions") val misconceptions: List<Misconception> = emptyList(),
    @SerializedName("recentSessions") val recentSessions: List<SessionSummary> = emptyList()
)

data class SubjectMastery(
    @SerializedName("subject") val subject: String,
    @SerializedName("score") val score: Int,
    @SerializedName("trend") val trend: String
)

data class Misconception(
    @SerializedName("id") val id: String,
    @SerializedName("subject") val subject: String,
    @SerializedName("concept") val concept: String,
    @SerializedName("date") val date: String,
    @SerializedName("questionAsked") val questionAsked: String,
    @SerializedName("childChoice") val childChoice: String,
    @SerializedName("childStatedReason") val childStatedReason: String,
    @SerializedName("parentTip") val parentTip: String
)

data class SessionSummary(
    @SerializedName("id") val id: String,
    @SerializedName("date") val date: String,
    @SerializedName("duration") val duration: String,
    @SerializedName("subject") val subject: String,
    @SerializedName("triesToCorrectAvg") val triesToCorrectAvg: Double,
    @SerializedName("actionMix") val actionMix: Map<String, String>
)
