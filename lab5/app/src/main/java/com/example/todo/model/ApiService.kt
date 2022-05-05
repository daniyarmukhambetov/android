package com.example.retrofit

import com.example.todo.view.Task
import retrofit2.Call
import retrofit2.http.*

interface ApiService {
    @GET("todos/")
    fun getTodos(): Call<MutableList<Task>>

    @GET("todos/{id}/")
    fun getTodoById(@Path("id") todoId: Int): Call<Task>

    @Headers("Cache-Control: max-age=640000", "User-Agent: My-App-Name")
    @GET("todos/")
    fun getTodosByUserId(
        @Query("userId") userId: Int,
        @Query("completed") completed: Boolean
    ): Call<List<Task>>


    @FormUrlEncoded
    @POST("todos/")
    fun addTodo(
        @Field("userId") userId: Int,
        @Field("title") title: String,
        @Field("completed") completed: Boolean
    ): Call<Task>

    @GET
    fun getTodosWithUrl(@Url url: String): Call<List<Task>>
}