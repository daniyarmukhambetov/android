package com.example.todo.view

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import androidx.recyclerview.widget.RecyclerView
import com.example.todo.R
import com.example.todo.TODO
import com.example.todo.TasksAdapter
import com.example.todo.contract.ContractInterface
import com.example.todo.presenter.MainActivityPresenter


class MainActivity : AppCompatActivity(), ContractInterface.View {
    private var flowerList: MutableList<Task> = mutableListOf()
    private var presenter: MainActivityPresenter?= null
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        presenter = MainActivityPresenter(this)

//        Log.d("PRESENTER", presenter.toString())
        initView()
    }
    private fun adapterOnClick(task: Task) {
        return
    }

    override fun initView() {
//        updList()
        flowerList = presenter?.getTODOs()!!;
//        presenter?.getTODOs()
        val taskAdapter = TasksAdapter {task -> adapterOnClick(task) }
        val recyclerView: RecyclerView = findViewById(R.id.recycler_view)
        recyclerView.adapter = taskAdapter
        taskAdapter.submitList(this.flowerList)
    }

    override fun updView() {
//        updList()
        flowerList = presenter?.getTODOs()!!;
        val taskAdapter = TasksAdapter {task -> adapterOnClick(task) }
        val recyclerView: RecyclerView = findViewById(R.id.recycler_view)
        recyclerView.adapter = taskAdapter
        taskAdapter.submitList(this.flowerList)
    }

    override fun updList(lst: MutableList<Task>) {
        flowerList = lst;
    }
}