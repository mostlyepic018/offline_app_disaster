package com.example.smsgateway

import android.app.Application

class SmsgwApp: Application() {
    override fun onCreate() {
        super.onCreate()
        Preferences.init(this)
    }
}
