package com.example.lab4secondtry.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.Duration
import java.util.*

@Entity(tableName = "task_table")
data class Task(
    @PrimaryKey(autoGenerate = true) val TaskId: Int,
    val title: String?,
    val description: String?,
    val status: String?,
    val deadline: String?,
)