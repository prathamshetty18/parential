package com.roavai.parental.data.repository

import com.roavai.parental.data.local.ChildDao
import com.roavai.parental.data.local.ChildEntity
import com.roavai.parental.data.model.ChildProfile
import com.roavai.parental.data.remote.CloudTutorApiService
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChildRepository @Inject constructor(
    private val apiService: CloudTutorApiService,
    private val childDao: ChildDao
) {
    val childrenFlow: Flow<List<ChildEntity>> = childDao.getAllChildren()

    suspend fun refreshChildren(): Result<List<ChildProfile>> {
        return try {
            val response = apiService.getChildren()
            if (response.isSuccessful && response.body() != null) {
                val list = response.body()!!["children"] ?: emptyList()
                childDao.insertChildren(list.map { it.toEntity() })
                Result.success(list)
            } else {
                Result.failure(Exception("Failed to fetch children"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun createChild(name: String, age: Int, grade: String, curriculum: String): Result<ChildProfile> {
        return try {
            val body = mapOf(
                "name" to name,
                "age" to age,
                "grade" to grade,
                "curriculum" to curriculum
            )
            val response = apiService.createChildProfile(body)
            if (response.isSuccessful) {
                refreshChildren()
                Result.success(ChildProfile("child_${System.currentTimeMillis()}", name, age, grade, curriculum))
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to create child"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun deleteChild(childId: String): Result<Boolean> {
        return try {
            val response = apiService.deleteChildProfile(childId)
            if (response.isSuccessful) {
                childDao.deleteChild(childId)
                Result.success(true)
            } else {
                Result.failure(Exception("Failed to delete child"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun ChildProfile.toEntity(): ChildEntity {
        return ChildEntity(
            id = id,
            name = name,
            age = age,
            grade = grade,
            curriculum = curriculum,
            winiPaired = winiPaired,
            winiDeviceId = winiDeviceId,
            winiStatus = winiStatus
        )
    }
}
