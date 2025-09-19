package com.example.smsgateway

import android.content.Context
import android.telephony.SmsManager
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import okhttp3.OkHttpClient
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray

class SyncOutboundWorker(appContext: Context, params: WorkerParameters): CoroutineWorker(appContext, params) {
    private val client = OkHttpClient()

    override suspend fun doWork(): Result {
        val base = Preferences.baseUrl
        val fetch = Request.Builder().url("$base/gateway/outbound?limit=20").get().build()
        return try {
            client.newCall(fetch).execute().use { resp ->
                val body = resp.body?.string() ?: return Result.success()
                val arr = JSONArray(body)
                if (arr.length() == 0) return Result.success()

                val ids = mutableListOf<Int>()
                for (i in 0 until arr.length()) {
                    val m = arr.getJSONObject(i)
                    val phone = m.getString("phone")
                    val text = m.getString("body")
                    SmsManager.getDefault().sendTextMessage(phone, null, text, null, null)
                    ids.add(m.getInt("id"))
                }
                val mark = Request.Builder().url("$base/gateway/mark-sent")
                    .post(JSONArray(ids).toString().toRequestBody("application/json".toMediaType()))
                    .build()
                client.newCall(mark).execute().use { }
            }
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
