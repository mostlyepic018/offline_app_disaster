package com.example.smsgateway

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val requestPerms = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {}
        val needed = arrayOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.SEND_SMS
        ).filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
        if (needed.isNotEmpty()) requestPerms.launch(needed.toTypedArray())

        setContent {
            MaterialTheme {
                GatewaySettings()
            }
        }
    }
}

@Composable
fun GatewaySettings() {
    var baseUrl by remember { mutableStateOf(Preferences.baseUrl) }
    var status by remember { mutableStateOf("") }

    Column(Modifier.padding(16.dp)) {
        Text(text = "Backend Base URL")
        OutlinedTextField(
            value = baseUrl,
            onValueChange = { baseUrl = it },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(12.dp))
        Button(onClick = {
            Preferences.baseUrl = baseUrl
            status = "Saved: $baseUrl"
        }) { Text("Save") }
        Spacer(Modifier.height(12.dp))
        Text(status)
    }
}
