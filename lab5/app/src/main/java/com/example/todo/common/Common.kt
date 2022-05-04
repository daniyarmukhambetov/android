package com.example.todo.common
import com.example.todo.contract.RetrofirServices
import com.example.todo.Retrofit.RetrofitClient

object Common {
    private val BASE_URL = "https://jsonplaceholder.typicode.com/users/1/"
    val retrofitService: RetrofirServices
        get() = RetrofitClient.getClient(BASE_URL).create(RetrofirServices::class.java)
}