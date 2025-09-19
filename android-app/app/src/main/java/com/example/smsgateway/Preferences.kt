package com.example.smsgateway

import android.content.Context
import androidx.preference.PreferenceManager

object Preferences {
    private const val KEY_BASE_URL = "base_url"
    private lateinit var appContext: Context

    fun init(context: Context) { appContext = context.applicationContext }

    var baseUrl: String
        get() {
            val prefs = PreferenceManager.getDefaultSharedPreferences(appContext)
            return prefs.getString(KEY_BASE_URL, "http://192.168.1.100:8000") ?: "http://192.168.1.100:8000"
        }
        set(value) {
            val prefs = PreferenceManager.getDefaultSharedPreferences(appContext).edit()
            prefs.putString(KEY_BASE_URL, value).apply()
        }
}
