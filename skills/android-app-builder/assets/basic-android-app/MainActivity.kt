package com.example.basicapp

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import com.example.basicapp.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize view binding
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Set toolbar/action bar
        setSupportActionBar(binding.toolbar)

        // Example: Load data in background
        lifecycleScope.launch {
            // TODO: Load initial data, call APIs, etc.
        }
    }

    override fun onStart() {
        super.onStart()
        // Register listeners, start location updates, etc.
    }

    override fun onStop() {
        super.onStop()
        // Unregister listeners, stop updates, etc.
    }

    override fun onDestroy() {
        super.onDestroy()
        // Clean up resources
    }
}
