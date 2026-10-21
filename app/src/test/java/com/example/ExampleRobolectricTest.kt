package com.example

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.example.model.TouchAction
import com.example.model.TouchPacket
import com.example.server.TouchBridgeServer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class ExampleRobolectricTest {

    @Test
    fun readStringFromContext() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val appName = context.getString(R.string.app_name)
        assertEquals("TouchBridge", appName)
    }

    @Test
    fun testServerPacketRouting() {
        val server = TouchBridgeServer.getInstance()
        server.releaseAllTouches()

        // 1. Simulate DOWN on pointer 0
        val pkt1 = TouchPacket(id = 0, action = TouchAction.DOWN, normX = 0.2f, normY = 0.7f)
        server.routePacket(pkt1)
        assertEquals(1, server.activePointers.value.size)
        assertTrue(server.activePointers.value.containsKey(0))

        // 2. Simulate DOWN on pointer 1 (simultaneous multi-touch)
        val pkt2 = TouchPacket(id = 1, action = TouchAction.DOWN, normX = 0.88f, normY = 0.68f)
        server.routePacket(pkt2)
        assertEquals(2, server.activePointers.value.size)

        // 3. Simulate UP on pointer 1
        val pkt3 = TouchPacket(id = 1, action = TouchAction.UP, normX = 0.88f, normY = 0.68f)
        server.routePacket(pkt3)
        assertEquals(1, server.activePointers.value.size)
        assertTrue(server.activePointers.value.containsKey(0))
        assertFalse(server.activePointers.value.containsKey(1))

        // 4. Release all
        server.releaseAllTouches()
        assertEquals(0, server.activePointers.value.size)
    }

    @Test
    fun testJsonPacketParser() {
        val server = TouchBridgeServer.getInstance()
        server.releaseAllTouches()

        val jsonDown = """{"action": "DOWN", "id": 5, "norm_x": 0.5, "norm_y": 0.5, "pressure": 1.0}"""
        server.parseAndRoutePacket(jsonDown)

        assertEquals(1, server.activePointers.value.size)
        val active = server.activePointers.value[5]
        assertEquals(5, active?.id)
        assertEquals(0.5f, active?.x)
        assertEquals(0.5f, active?.y)

        val jsonRelease = """{"action": "RELEASE_ALL"}"""
        server.parseAndRoutePacket(jsonRelease)
        assertEquals(0, server.activePointers.value.size)
    }
}
