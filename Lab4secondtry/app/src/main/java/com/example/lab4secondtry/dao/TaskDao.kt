package com.example.lab4secondtry.dao

import com.example.lab4secondtry.Database
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.example.lab4secondtry.model.Task

@Dao
interface TaskDao {
    @Insert
    fun insert(task: Task)
    @Query("select * from task_table")
    fun get_all_Tasks(): List<Task>
}