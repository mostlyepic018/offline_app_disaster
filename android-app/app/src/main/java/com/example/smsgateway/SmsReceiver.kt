package com.example.smsgateway

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Telephony
import androidx.work.*

class SmsReceiver: BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (Telephony.Sms.Intents.SMS_RECEIVED_ACTION == intent.action) {
            val msgs = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            for (msg in msgs) {
                val from = msg.originatingAddress ?: ""
                val body = msg.messageBody ?: ""
                enqueueInboundSync(context, from, body)
            }
        }
    }
}

fun enqueueInboundSync(context: Context, from: String, body: String) {
    val data = Data.Builder().putString("from", from).putString("message", body).build()
    val req = OneTimeWorkRequestBuilder<SyncInboundWorker>().setInputData(data).build()
    WorkManager.getInstance(context).enqueue(req)
}
