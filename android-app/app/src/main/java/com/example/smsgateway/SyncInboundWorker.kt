package com.example.smsgateway

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class SyncInboundWorker(appContext: Context, params: WorkerParameters): CoroutineWorker(appContext, params) {
    private val client = OkHttpClient()

    override suspend fun doWork(): Result {
        val from = inputData.getString("from") ?: return Result.success()
        val message = inputData.getString("message") ?: return Result.success()
        val base = Preferences.baseUrl
        val json = JSONObject(mapOf("from" to from, "message" to message)).toString()
        val req = Request.Builder()
            .url("$base/receive-sms")
            .post(json.toRequestBody("application/json".toMediaType()))
            .build()
        return try {
            client.newCall(req).execute().use { Result.success() }
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
