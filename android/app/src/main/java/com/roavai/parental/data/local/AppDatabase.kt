package com.roavai.parental.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [ChildEntity::class, MisconceptionEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun childDao(): ChildDao
    abstract fun misconceptionDao(): MisconceptionDao
}
