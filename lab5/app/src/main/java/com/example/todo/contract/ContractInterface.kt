package com.example.todo.contract

import com.example.todo.TODO
import com.example.todo.view.Task

interface ContractInterface {
    interface View {
        fun initView()
        fun updView()
        fun updList(lst: MutableList<Task>)
    }
    interface Presenter {
        fun getTODOs(): MutableList<Task>
        fun createTODO(todo: Task)
        fun getTODO(id: Int): Task
    }
    interface Model {
        fun getTODOs(): MutableList<Task>
        fun createTODO(todo: Task)
        fun getTODO(id: Int): Task
    }
}