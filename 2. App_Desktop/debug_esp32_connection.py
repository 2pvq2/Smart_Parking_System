"""
Debug Script - Kiểm tra kết nối ESP32
Chạy script này để debug vấn đề kết nối
"""

import socket
import sys
import time
import threading
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

def check_port_listening():
    """Kiểm tra xem port 8888 có đang listen không"""
    print("\n" + "="*60)
    print("KIỂM TRA PORT 8888")
    print("="*60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Thử bind port - nếu bind thành công, port available
        sock.bind(('0.0.0.0', 8888))
        sock.close()
        print("❌ PORT 8888 KHÔNG CÓ PROCESS LISTENING")
        print("   Hãy chắc chắn ứng dụng Smart Parking đang chạy!")
        return False
    except OSError as e:
        print("✅ PORT 8888 CÓ PROCESS LISTENING")
        print(f"   Lỗi: {e}")
        return True

def simulate_esp32_connection():
    """Mô phỏng kết nối từ ESP32"""
    print("\n" + "="*60)
    print("KIỂM TRA KẾT NỐI ĐẾN SERVER")
    print("="*60)
    
    try:
        # Cố gắng kết nối đến server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        
        print(f"\n🔗 Đang kết nối đến 127.0.0.1:8888...")
        sock.connect(('127.0.0.1', 8888))
        print("✅ KẾT NỐI THÀNH CÔNG!")
        
        # Gửi HELLO message như ESP32 Main
        print("\n📤 Gửi HELLO_FROM_ESP32...")
        sock.send(b"HELLO_FROM_ESP32\n")
        
        # Nhận phản hồi
        response = sock.recv(1024).decode('utf-8', errors='ignore')
        print(f"📥 Nhận phản hồi: {response.strip()}")
        
        time.sleep(1)
        
        # Gửi CARD message
        print("\n📤 Gửi CARD message...")
        sock.send(b"CARD:TEST123456:1\n")
        time.sleep(1)
        
        sock.close()
        print("\n✅ KIỂM TRA HOÀN TẤT")
        return True
        
    except socket.timeout:
        print("❌ TIMEOUT - Server không phản hồi")
        print("   Kiểm tra xem app có đang chạy không")
        return False
    except ConnectionRefusedError:
        print("❌ KẾT NỐI BỊ TỪ CHỐI")
        print("   Server không lắng nghe port 8888")
        print("   Hãy chắc chắn app Smart Parking đang chạy!")
        return False
    except Exception as e:
        print(f"❌ LỖI: {e}")
        return False

def check_network_interfaces():
    """Kiểm tra các network interface"""
    print("\n" + "="*60)
    print("KIỂM TRA NETWORK INTERFACES")
    print("="*60)
    
    import subprocess
    
    try:
        # Windows
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'IPv4' in line or 'Default Gateway' in line:
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"❌ Lỗi kiểm tra network: {e}")

def test_network_server_directly():
    """Test NetworkServer class directly"""
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
        print("\n🔗 Kết nối từ client giả lập...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        
        try:
            client.connect(('127.0.0.1', 8888))
            print("✅ Client kết nối thành công!")
            
            # Gửi HELLO
            client.send(b"HELLO_FROM_ESP32\n")
            time.sleep(1)
            
            print(f"   Connected clients: {server.get_connected_clients()}")
            
            client.close()
        except Exception as e:
            print(f"❌ Client connection failed: {e}")
        
        # Dừng server
        server.stop()
        print("\n✅ Test hoàn tất")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 DEBUG ESP32 CONNECTION")
    print("="*60)
    
    print("\nNhập lựa chọn:")
    print("1. Kiểm tra port 8888")
    print("2. Mô phỏng kết nối ESP32 (yêu cầu app đang chạy)")
    print("3. Kiểm tra network interfaces")
    print("4. Test NetworkServer class trực tiếp")
    print("0. Thoát")
    
    while True:
        choice = input("\nNhập lựa chọn (0-4): ").strip()
        
        if choice == "1":
            check_port_listening()
        elif choice == "2":
            simulate_esp32_connection()
        elif choice == "3":
            check_network_interfaces()
        elif choice == "4":
            test_network_server_directly()
        elif choice == "0":
            break
        else:
            print("Lựa chọn không hợp lệ")
    
    print("\n👋 Tạm biệt!")
