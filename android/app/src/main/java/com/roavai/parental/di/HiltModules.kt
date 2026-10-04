package com.roavai.parental.di

import android.content.Context
import androidx.room.Room
import com.roavai.parental.data.local.AppDatabase
import com.roavai.parental.data.local.ChildDao
import com.roavai.parental.data.local.MisconceptionDao
import com.roavai.parental.data.remote.CloudTutorApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "roavai_parental_db"
        ).fallbackToDestructiveMigration().build()
    }

    @Provides
    fun provideChildDao(db: AppDatabase): ChildDao = db.childDao()

    @Provides
    fun provideMisconceptionDao(db: AppDatabase): MisconceptionDao = db.misconceptionDao()
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideCloudTutorApiService(okHttpClient: OkHttpClient): CloudTutorApiService {
        return Retrofit.Builder()
            .baseUrl("http://10.0.2.2:4000/") // Localhost bridge for Android Emulator
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CloudTutorApiService::class.java)
    }
}
