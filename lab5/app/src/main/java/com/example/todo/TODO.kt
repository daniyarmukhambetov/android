package com.example.todo

data class TODO(
    val userId: Int = 0,
    val title: String = "",
    val completed: Boolean = false,
    val id: Int = 0,
)
