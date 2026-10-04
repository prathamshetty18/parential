package com.roavai.parental.data.remote

import com.roavai.parental.data.model.ChildProfile
import com.roavai.parental.data.model.LearnerModel
import com.roavai.parental.data.model.TutoringControls
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface CloudTutorApiService {

    @POST("api/consent")
    suspend fun recordConsent(
        @Body body: Map<String, String>
    ): Response<Map<String, Any>>

    @GET("api/children")
    suspend fun getChildren(): Response<Map<String, List<ChildProfile>>>

    @POST("api/children")
    suspend fun createChildProfile(
        @Body body: Map<String, Any>
    ): Response<Map<String, Any>>

    @POST("api/pairing/qr")
    suspend fun pairWiniRobot(
        @Body body: Map<String, String>
    ): Response<Map<String, Any>>

    @GET("api/learner-model/{childId}")
    suspend fun getLearnerModel(
        @Path("childId") childId: String
    ): Response<LearnerModel>

    @GET("api/controls/{childId}")
    suspend fun getControls(
        @Path("childId") childId: String
    ): Response<TutoringControls>

    @POST("api/controls/{childId}")
    suspend fun updateControls(
        @Path("childId") childId: String,
        @Body controls: TutoringControls
    ): Response<Map<String, Any>>

    @DELETE("api/privacy/delete/{childId}")
    suspend fun deleteChildProfile(
        @Path("childId") childId: String
    ): Response<Map<String, Any>>
}
