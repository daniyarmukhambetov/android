package com.example.lab4secondtry

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.lab4secondtry.dao.TaskDao
import com.example.lab4secondtry.model.Task

@Database(
    entities = arrayOf(
        Task::class,
    ), version = 1, exportSchema = false
)
abstract class Database : RoomDatabase() {
    abstract fun TaskDao() : TaskDao
}