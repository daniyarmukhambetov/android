package com.example.lab4secondtry

import android.app.Application
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import com.example.lab4secondtry.dao.TaskDao
import com.example.lab4secondtry.model.Task

class MainActivity : AppCompatActivity() {
    lateinit var Applic : MyApplication
    lateinit var db : Database
    lateinit var taskDao : TaskDao
    lateinit var AllTasks : List<Task>
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        Applic = MyApplication().instance()
//        db = Applic.getDatabase()!!
//        taskDao = db.TaskDao()
//        AllTasks = taskDao.get_all_Tasks()
        Log.e("ex", Applic.toString())
    }
}