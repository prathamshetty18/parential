package com.roavai.parental

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class RoavaiApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}
