package com.example.smsgateway

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class BootReceiver: BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (Intent.ACTION_BOOT_COMPLETED == intent.action) {
            scheduleOutbound(context)
        }
    }
}

fun scheduleOutbound(context: Context) {
    val req = PeriodicWorkRequestBuilder<SyncOutboundWorker>(15, TimeUnit.MINUTES).build()
    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        "outbound-poller",
        ExistingPeriodicWorkPolicy.UPDATE,
        req
    )
}
