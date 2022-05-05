package com.example.todo.model

import android.util.Log
import com.example.retrofit.ApiService
import com.example.todo.contract.ContractInterface
import com.example.todo.contract.ContractInterface.Model
import com.example.todo.view.Task
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit


class MainActivityModel: Model {
//    val service = Common()
    var FAKETODOS: MutableList<Task> = mutableListOf(
        Task(1, "delectus aut autem", false, 1),
        Task(2, "quis ut nam facilis et officia qui", false, 1),
        Task(3, "fugiat veniam minus", false, 1),
        Task(4, "et porro tempora", true, 1)
    );
    var todos: MutableList<Task> = mutableListOf();
    override fun getTODOs(): MutableList<Task> {
        val loggingInterceptor = HttpLoggingInterceptor()
        loggingInterceptor.level = HttpLoggingInterceptor.Level.BODY
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl("https://jsonplaceholder.typicode.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .client(okHttpClient)
            .build()

        val apiService = retrofit.create(ApiService::class.java)
        var res: MutableList<Task> = mutableListOf(
            Task(1, "task1", true, 1),
            Task(2, "task2", false, 1),
            Task(3, "task3", false, 1)
        );
        apiService.getTodos().enqueue(object : Callback<MutableList<Task>> {
            override fun onFailure(call: Call<MutableList<Task>>, t: Throwable) {
                t.message?.let { Log.e("Error", it) }
            }

            override fun onResponse(call: Call<MutableList<Task>>, response: Response<MutableList<Task>>) {
                Log.e("Response size: ", response.body()!!.size.toString() + "")
                FAKETODOS = response.body()!!
//                myModel.FAKETODOS = response.body()!!
//                todos.addAll(elements = response.body()!!)
                Log.e("fake",FAKETODOS.toString())
            }
        })
//        apiService.getTodos().
        return FAKETODOS;
    }

    override fun getTODO(id: Int): Task {
        var ret_todo: Task = Task(0, "", false, 0);
        for (todo in this.FAKETODOS) {
            if (todo.id == id) {
                ret_todo = todo
                break
            }
        }
        return ret_todo
    }

    override fun createTODO(todo: Task) {
        this.FAKETODOS.add(todo)
    }

}