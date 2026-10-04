package com.roavai.parental.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "children")
data class ChildEntity(
    @PrimaryKey val id: String,
    val name: String,
    val age: Int,
    val grade: String,
    val curriculum: String,
    val winiPaired: Boolean,
    val winiDeviceId: String?,
    val winiStatus: String
)

@Entity(tableName = "misconceptions")
data class MisconceptionEntity(
    @PrimaryKey val id: String,
    val childId: String,
    val subject: String,
    val concept: String,
    val date: String,
    val questionAsked: String,
    val childChoice: String,
    val childStatedReason: String,
    val parentTip: String
)
