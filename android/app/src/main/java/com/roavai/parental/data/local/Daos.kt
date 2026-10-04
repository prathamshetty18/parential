package com.roavai.parental.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface ChildDao {
    @Query("SELECT * FROM children")
    fun getAllChildren(): Flow<List<ChildEntity>>

    @Query("SELECT * FROM children WHERE id = :childId")
    suspend fun getChildById(childId: String): ChildEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChildren(children: List<ChildEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChild(child: ChildEntity)

    @Query("DELETE FROM children WHERE id = :childId")
    suspend fun deleteChild(childId: String)
}

@Dao
interface MisconceptionDao {
    @Query("SELECT * FROM misconceptions WHERE childId = :childId ORDER BY date DESC")
    fun getMisconceptionsForChild(childId: String): Flow<List<MisconceptionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMisconceptions(misconceptions: List<MisconceptionEntity>)

    @Query("DELETE FROM misconceptions WHERE childId = :childId")
    suspend fun clearChildMisconceptions(childId: String)
}
