"""
Test NetworkServer class directly without user input
"""

import socket
import sys
import time
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

print("\n" + "="*60)
print("TEST NETWORK SERVER CLASS")
print("="*60)

try:
    from core.network_server import NetworkServer
    
    print("✅ Import NetworkServer thành công")
    
    # Tạo server instance
    server = NetworkServer(host='0.0.0.0', port=8888)
    print(f"✅ NetworkServer instance tạo được")
    print(f"   Host: {server.host}, Port: {server.port}")
    print(f"   Running: {server.running}")
    
    # Start server
    print("\n🚀 Khởi động server...")
    server.start()
    time.sleep(2)
    
    print(f"   Running: {server.running}")
    print(f"   Connected clients: {server.get_connected_clients()}")
    
    # Thử kết nối từ client
    print("\n🔗 Kết nối từ client giả lập (127.0.0.1:8888)...")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(3)
    
    try:
        client.connect(('127.0.0.1', 8888))
        print("✅ Client kết nối thành công!")
        
        # Gửi HELLO
        print("\n📤 Gửi HELLO_FROM_ESP32...")
        client.send(b"HELLO_FROM_ESP32\n")
        time.sleep(1)
        
        print(f"📊 Connected clients: {server.get_connected_clients()}")
        
        # Test CARD message
        print("\n📤 Gửi CARD message (giả lập RFID scan)...")
        client.send(b"CARD:TEST123456:1\n")
        time.sleep(1)
        
        print(f"📊 Connected clients (after CARD): {server.get_connected_clients()}")
        
        client.close()
        print("\n✅ Client disconnected")
        
    except socket.timeout:
        print("❌ TIMEOUT - Server không phản hồi")
    except ConnectionRefusedError as e:
        print(f"❌ KẾT NỐI BỊ TỪ CHỐI: {e}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    # Dừng server
    print("\n⏹️ Dừng server...")
    server.stop()
    time.sleep(1)
    print("✅ Server stopped")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ TEST HOÀN TẤT")
print("="*60)
