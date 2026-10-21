package com.example.server

import android.util.Log
import com.example.model.ActiveTouch
import com.example.model.TouchAction
import com.example.model.TouchPacket
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.ServerSocket
import java.net.Socket

class TouchBridgeServer private constructor() {

    companion object {
        const val PORT = 28200
        private const val TAG = "TouchBridgeServer"

        @Volatile
        private var instance: TouchBridgeServer? = null

        fun getInstance(): TouchBridgeServer {
            return instance ?: synchronized(this) {
                instance ?: TouchBridgeServer().also { instance = it }
            }
        }
    }

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var serverSocket: ServerSocket? = null
    private var serverJob: Job? = null

    private val _isRunning = MutableStateFlow(false)
    val isRunning = _isRunning.asStateFlow()

    private val _connectedClients = MutableStateFlow(0)
    val connectedClients = _connectedClients.asStateFlow()

    private val _recentPackets = MutableStateFlow<List<TouchPacket>>(emptyList())
    val recentPackets = _recentPackets.asStateFlow()

    private val _activePointers = MutableStateFlow<Map<Int, ActiveTouch>>(emptyMap())
    val activePointers = _activePointers.asStateFlow()

    private val _packetRateHz = MutableStateFlow(0)
    val packetRateHz = _packetRateHz.asStateFlow()

    private val _averageLatencyMs = MutableStateFlow(1.5f)
    val averageLatencyMs = _averageLatencyMs.asStateFlow()

    private var packetCountCounter = 0
    private var lastRateCalcTime = System.currentTimeMillis()

    fun start() {
        if (_isRunning.value) return
        serverJob = scope.launch {
            try {
                serverSocket = ServerSocket(PORT)
                _isRunning.value = true
                Log.i(TAG, "TouchBridge TCP Server listening on port $PORT")

                // Start rate calculator ticker
                launch {
                    while (isActive) {
                        delay(1000)
                        val now = System.currentTimeMillis()
                        val dt = (now - lastRateCalcTime).coerceAtLeast(1)
                        val rate = (packetCountCounter * 1000L / dt).toInt()
                        _packetRateHz.value = rate
                        packetCountCounter = 0
                        lastRateCalcTime = now
                    }
                }

                while (isActive) {
                    val clientSocket = serverSocket?.accept() ?: break
                    launch { handleClient(clientSocket) }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Server socket error", e)
            } finally {
                _isRunning.value = false
            }
        }
    }

    private suspend fun handleClient(socket: Socket) = withContext(Dispatchers.IO) {
        _connectedClients.value += 1
        Log.i(TAG, "Client connected: ${socket.inetAddress}")
        try {
            socket.tcpNoDelay = true
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))
            while (isActive && !socket.isClosed) {
                val line = reader.readLine() ?: break
                parseAndRoutePacket(line)
            }
        } catch (e: Exception) {
            Log.d(TAG, "Client disconnected: ${e.message}")
        } finally {
            try { socket.close() } catch (_: Exception) {}
            _connectedClients.value = (_connectedClients.value - 1).coerceAtLeast(0)
            // Safety: client disconnect -> clear touches
            releaseAllTouches()
        }
    }

    fun parseAndRoutePacket(jsonStr: String) {
        try {
            val json = JSONObject(jsonStr)
            val actionStr = json.optString("action", "DOWN")
            val action = when (actionStr.uppercase()) {
                "MOVE" -> TouchAction.MOVE
                "UP" -> TouchAction.UP
                "RELEASE_ALL" -> TouchAction.RELEASE_ALL
                else -> TouchAction.DOWN
            }

            if (action == TouchAction.RELEASE_ALL) {
                releaseAllTouches()
                return
            }

            val id = json.optInt("id", 0)
            val x = json.optInt("x", 0)
            val y = json.optInt("y", 0)
            val normX = json.optDouble("norm_x", 0.5).toFloat()
            val normY = json.optDouble("norm_y", 0.5).toFloat()
            val pressure = json.optDouble("pressure", 1.0).toFloat()
            val timestamp = json.optLong("timestamp", System.currentTimeMillis())

            val packet = TouchPacket(
                id = id,
                action = action,
                x = x,
                y = y,
                normX = normX,
                normY = normY,
                pressure = pressure,
                timestamp = timestamp
            )

            routePacket(packet)
        } catch (e: Exception) {
            Log.w(TAG, "Malformed JSON packet: $jsonStr", e)
        }
    }

    fun routePacket(packet: TouchPacket) {
        packetCountCounter++

        // Latency estimation
        val now = System.currentTimeMillis()
        if (packet.timestamp in 1..now) {
            val lat = (now - packet.timestamp).coerceIn(0, 500)
            _averageLatencyMs.value = (_averageLatencyMs.value * 0.9f + lat * 0.1f)
        }

        // Update active pointer state
        val currentPointers = _activePointers.value.toMutableMap()
        when (packet.action) {
            TouchAction.DOWN, TouchAction.MOVE -> {
                currentPointers[packet.id] = ActiveTouch(
                    id = packet.id,
                    x = packet.normX,
                    y = packet.normY,
                    pressure = packet.pressure
                )
            }
            TouchAction.UP -> {
                currentPointers.remove(packet.id)
            }
            TouchAction.RELEASE_ALL -> {
                currentPointers.clear()
            }
        }
        _activePointers.value = currentPointers

        // Maintain ring buffer of recent packets (max 20)
        val list = _recentPackets.value.toMutableList()
        list.add(0, packet)
        if (list.size > 20) {
            list.removeAt(list.size - 1)
        }
        _recentPackets.value = list
    }

    fun releaseAllTouches() {
        _activePointers.value = emptyMap()
    }

    fun stop() {
        try {
            serverSocket?.close()
        } catch (_: Exception) {}
        serverJob?.cancel()
        _isRunning.value = false
        _connectedClients.value = 0
        releaseAllTouches()
    }
}
