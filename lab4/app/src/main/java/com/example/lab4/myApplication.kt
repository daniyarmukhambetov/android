package com.example.lab4

import Db
import android.app.Application
import android.util.Log
import androidx.room.Room

class Application : Application() {
    private var database : Db ?= null
    override fun onCreate() {
        super.onCreate()
        instance = this
        database = Room.databaseBuilder(this, Db::class.java, "App_Db")
            .fallbackToDestructiveMigration().allowMainThreadQueries().build()
    }
    fun getDb() : Db? {
        return database
    }
    companion object {
        lateinit var instance : Application
    }
}