package com.roavai.parental.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.roavai.parental.ui.screens.*
import com.roavai.parental.ui.viewmodel.ControlsViewModel
import com.roavai.parental.ui.viewmodel.DashboardViewModel

sealed class Screen(val route: String, val title: String, val icon: String) {
    object Onboarding : Screen("onboarding", "Consent", "👋")
    object PinLock : Screen("pin_lock", "Lock", "🔒")
    object Home : Screen("home", "Dashboard", "📊")
    object Misconceptions : Screen("misconceptions", "Reasoning", "💡")
    object Controls : Screen("controls", "Controls", "⚙️")
    object Pairing : Screen("pairing", "Pairing", "📲")
    object Privacy : Screen("privacy", "Privacy", "🛡️")
}

@Composable
fun MainAppNavigation() {
    val navController = rememberNavController()
    var isUnlocked by remember { mutableStateOf(false) }
    var consentRecorded by remember { mutableStateOf(true) }

    if (!consentRecorded) {
        OnboardingScreen(onConsentCompleted = { consentRecorded = true })
    } else if (!isUnlocked) {
        PinLockScreen(onUnlocked = { isUnlocked = true })
    } else {
        val bottomNavItems = listOf(
            Screen.Home,
            Screen.Misconceptions,
            Screen.Controls,
            Screen.Pairing,
            Screen.Privacy
        )

        Scaffold(
            bottomBar = {
                NavigationBar {
                    val navBackStackEntry by navController.currentBackStackEntryAsState()
                    val currentRoute = navBackStackEntry?.destination?.route

                    bottomNavItems.forEach { screen ->
                        NavigationBarItem(
                            icon = { Text(screen.icon) },
                            label = { Text(screen.title) },
                            selected = currentRoute == screen.route,
                            onClick = {
                                if (currentRoute != screen.route) {
                                    navController.navigate(screen.route) {
                                        popUpTo(Screen.Home.route)
                                        launchSingleTop = true
                                    }
                                }
                            }
                        )
                    }
                }
            }
        ) { innerPadding ->
            val dashboardViewModel: DashboardViewModel = hiltViewModel()
            val controlsViewModel: ControlsViewModel = hiltViewModel()

            NavHost(
                navController = navController,
                startDestination = Screen.Home.route,
                modifier = Modifier.padding(innerPadding)
            ) {
                composable(Screen.Home.route) {
                    HomeScreen(viewModel = dashboardViewModel)
                }
                composable(Screen.Misconceptions.route) {
                    MisconceptionsScreen(viewModel = dashboardViewModel)
                }
                composable(Screen.Controls.route) {
                    ControlsScreen(viewModel = controlsViewModel)
                }
                composable(Screen.Pairing.route) {
                    PairingScreen()
                }
                composable(Screen.Privacy.route) {
                    PrivacySettingsScreen()
                }
            }
        }
    }
}
