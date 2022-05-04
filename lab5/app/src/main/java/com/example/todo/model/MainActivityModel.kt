package com.example.todo.model

import com.example.todo.TODO
import com.example.todo.common.Common
import com.example.todo.contract.ContractInterface.Model
import com.example.todo.contract.RetrofirServices
import com.example.todo.view.Task
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response


class MainActivityModel: Model {
    lateinit var service: RetrofirServices;

    var FAKETODOS: MutableList<Task> = mutableListOf(
        Task(1, "task1", true, 1),
        Task(2, "task2", false, 1),
        Task(3, "task3", false, 1)
    );
    init {
        service = Common.retrofitService
        service.getTODOs().enqueue(object : Callback<MutableList<Task>> {
            override fun onFailure(call: Call<MutableList<Task>>, t: Throwable) {
            }

            override fun onResponse(
                call: Call<MutableList<Task>>,
                response: Response<MutableList<Task>>
            ) {
                FAKETODOS = response.body() as MutableList<Task>
            }
        }
        )
    }
    override fun getTODOs(): MutableList<Task> {
        return FAKETODOS
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