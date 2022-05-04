package com.example.todo.contract
import com.example.todo.view.Task
import retrofit2.Call
import retrofit2.http.*
interface RetrofirServices {
    @GET("todos")
    fun getTODOs(): Call<MutableList<Task>>
}