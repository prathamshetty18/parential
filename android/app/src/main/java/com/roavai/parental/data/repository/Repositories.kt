package com.roavai.parental.data.repository

import com.roavai.parental.data.local.MisconceptionDao
import com.roavai.parental.data.local.MisconceptionEntity
import com.roavai.parental.data.model.LearnerModel
import com.roavai.parental.data.model.Misconception
import com.roavai.parental.data.model.TutoringControls
import com.roavai.parental.data.remote.CloudTutorApiService
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LearnerModelRepository @Inject constructor(
    private val apiService: CloudTutorApiService,
    private val misconceptionDao: MisconceptionDao
) {
    fun getMisconceptionsFlow(childId: String): Flow<List<MisconceptionEntity>> {
        return misconceptionDao.getMisconceptionsForChild(childId)
    }

    suspend fun fetchLearnerModel(childId: String): Result<LearnerModel> {
        return try {
            val response = apiService.getLearnerModel(childId)
            if (response.isSuccessful && response.body() != null) {
                val model = response.body()!!
                misconceptionDao.insertMisconceptions(model.misconceptions.map { it.toEntity(childId) })
                Result.success(model)
            } else {
                Result.failure(Exception("Failed to load learner model"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun Misconception.toEntity(childId: String): MisconceptionEntity {
        return MisconceptionEntity(
            id = id,
            childId = childId,
            subject = subject,
            concept = concept,
            date = date,
            questionAsked = questionAsked,
            childChoice = childChoice,
            childStatedReason = childStatedReason,
            parentTip = parentTip
        )
    }
}

@Singleton
class ControlsRepository @Inject constructor(
    private val apiService: CloudTutorApiService
) {
    suspend fun getControls(childId: String): Result<TutoringControls> {
        return try {
            val res = apiService.getControls(childId)
            if (res.isSuccessful && res.body() != null) {
                Result.success(res.body()!!)
            } else {
                Result.failure(Exception("Failed to get controls"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun updateControls(childId: String, controls: TutoringControls): Result<Boolean> {
        return try {
            val res = apiService.updateControls(childId, controls)
            if (res.isSuccessful) {
                Result.success(true)
            } else {
                Result.failure(Exception("Failed to update controls"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
