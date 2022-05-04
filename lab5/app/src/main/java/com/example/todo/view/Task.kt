package com.example.todo.view

data class Task(
    val id: Int,
    val title: String,
    val completed: Boolean,
    val userId: Int
)
