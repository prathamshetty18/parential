package com.roavai.parental.ui.theme

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

val IndigoPrimary = Color(0xFF6366F1)
val IndigoDark = Color(0xFF4F46E5)
val PurpleAccent = Color(0xFFA855F7)
val GreenSuccess = Color(0xFF10B981)
val AmberWarning = Color(0xFFF59E0B)
val RedDanger = Color(0xFFEF4444)

val DarkBg = Color(0xFF0B0F19)
val DarkSurface = Color(0xFF131B2E)
val DarkCard = Color(0xFF1C2640)

val LightBg = Color(0xFFF8FAFC)
val LightSurface = Color(0xFFFFFFFF)
val LightCard = Color(0xFFF1F5F9)

val DarkColorScheme = darkColorScheme(
    primary = IndigoPrimary,
    secondary = PurpleAccent,
    background = DarkBg,
    surface = DarkSurface,
    surfaceVariant = DarkCard,
    error = RedDanger
)

val LightColorScheme = lightColorScheme(
    primary = IndigoDark,
    secondary = PurpleAccent,
    background = LightBg,
    surface = LightSurface,
    surfaceVariant = LightCard,
    error = RedDanger
)
