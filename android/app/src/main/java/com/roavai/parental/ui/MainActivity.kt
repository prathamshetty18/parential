package com.roavai.parental.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.roavai.parental.ui.theme.ROAVAIParentalTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private var backgroundTimestamp: Long = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate()
        setContent {
            ROAVAIParentalTheme {
                MainAppNavigation()
            }
        }
    }

    override fun onStop() {
        super.onStop()
        backgroundTimestamp = System.currentTimeMillis()
    }
}
