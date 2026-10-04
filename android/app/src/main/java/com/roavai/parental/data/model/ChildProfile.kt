package com.roavai.parental.data.model

import com.google.gson.annotations.SerializedName

data class ChildProfile(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("age") val age: Int,
    @SerializedName("grade") val grade: String,
    @SerializedName("curriculum") val curriculum: String,
    @SerializedName("language") val language: String = "English",
    @SerializedName("avatar") val avatar: String = "🚀",
    @SerializedName("winiPaired") val winiPaired: Boolean = false,
    @SerializedName("winiDeviceId") val winiDeviceId: String? = null,
    @SerializedName("winiStatus") val winiStatus: String = "offline"
)
