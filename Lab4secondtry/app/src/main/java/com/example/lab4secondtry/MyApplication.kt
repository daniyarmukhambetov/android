package com.example.lab4secondtry

import android.app.Application
import android.util.Log
import androidx.room.Room
import com.example.lab4secondtry.Database

class MyApplication : Application() {
    private var database : Database ?= null
    override fun onCreate() {
        super.onCreate()
        Log.e("MyApplication", "onCreate")
        instance = this
        database = Room.databaseBuilder(this, Database::class.java, "my_db")
            .fallbackToDestructiveMigration()
            .allowMainThreadQueries().build()
    }
    fun getDatabase() : Database? {
        return database
    }
    companion object {
        lateinit var instance : MyApplication
    }
    fun instance() : MyApplication {
        return instance
    }
}