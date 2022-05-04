package com.example.lab4secondtry.Repository

import androidx.annotation.WorkerThread
import com.example.lab4secondtry.dao.TaskDao
import com.example.lab4secondtry.model.Task

class Repo(private val TaskDao : TaskDao) {
    val ALlTasks : List<Task> = TaskDao.get_all_Tasks()
    @Suppress("RedundantSuspendModifier")
    @WorkerThread
    suspend fun insert(task : Task) {
        TaskDao.insert(task)
    }
}