"""
TCP Server để nhận dữ liệu từ ESP32 qua WiFi
Giao thức: ESP32 gửi các lệnh dạng text qua TCP socket

Format message từ ESP:
- CARD:<UID>:<LANE>  (VD: CARD:A1B2C3D4:1)
- CLOSED:<LANE>       (VD: CLOSED:1)
- HELLO_FROM_ESP32    (Tin chào ban đầu - ESP32 Main)
- HELLO:ZONE_1:SLOTS_10 (Tin chào từ ESP32 Node2 sensor)
- PARKING_DATA:zone_id:status_binary:occupied:available

Format lệnh gửi xuống ESP:
- OPEN_1  (Mở barie làn 1)
- OPEN_2  (Mở barie làn 2)
- MSG:<Line1>|<Line2>  (Hiển thị message trên LCD)
"""

import socket
import threading
from PySide6.QtCore import QObject, Signal
import time


class NetworkServer(QObject):
    """TCP Server hỗ trợ nhiều ESP32 kết nối đồng thời"""
    
    # Signals để gửi dữ liệu về main thread
    card_scanned = Signal(str, int)  # (card_uid, lane_number)
    barrier_closed = Signal(int)     # (lane_number) - khi barie đóng
    esp_connected = Signal(str)      # (client_ip)
    esp_disconnected = Signal()
    sensor_data_received = Signal(int, str, int, int)  # (zone_id, status_binary, occupied, available)
    
    def __init__(self, host='0.0.0.0', port=8888):
        super().__init__()
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {socket: {'address': addr, 'type': 'main'/'sensor', 'zone_id': 1}}
        self.clients_lock = threading.Lock()
        self.running = False
        self.server_thread = None
        
    def start(self):
        """Khởi động TCP server"""
        if self.running:
            print("[NET] Server đã chạy rồi!")
            return
            
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"[NET] TCP Server đang lắng nghe tại {self.host}:{self.port}")
    
    def stop(self):
        """Dừng server"""
        self.running = False
        
        # Đóng tất cả client connections
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("[NET] Server đã dừng")
    
    def _run_server(self):
        """Thread chính của server - Accept multiple connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind explicitly to IPv4 localhost and external
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Cho phép tối đa 5 connections
            self.server_socket.settimeout(0.5)  # Timeout ngắn hơn để check running flag
            
            print(f"[NET] ✅ Server sẵn sàng nhận kết nối từ ESP32")
            print(f"[NET] 📍 Binding: {self.host}:{self.port}")
            
            while self.running:
                try:
                    # Chấp nhận kết nối từ ESP32
                    client, address = self.server_socket.accept()
                    print(f"[NET] 🔗 ESP32 đã kết nối từ {address}")
                    
                    # Lưu client vào dictionary
                    with self.clients_lock:
                        self.clients[client] = {
                            'address': address,
                            'type': 'unknown',  # Sẽ được set sau khi nhận HELLO
                            'zone_id': None
                        }
                    
                    self.esp_connected.emit(str(address[0]))
                    
                    # Tạo thread riêng cho mỗi client
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[NET] Lỗi accept: {e}")
                    time.sleep(1)
            
        except Exception as e:
            print(f"[NET] ❌ Lỗi server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def _handle_client(self, client_socket, address):
        """Xử lý messages từ một ESP32 client (chạy trong thread riêng)"""
        buffer = ""
        
        try:
            client_socket.settimeout(60.0)  # Timeout 60s cho recv
            
            while self.running:
                try:
                    # Nhận dữ liệu
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Decode và thêm vào buffer
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Xử lý từng dòng (message kết thúc bằng \n)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        message = line.strip()
                        
                        if message:
                            print(f"[NET] 📩 Nhận từ {address[0]}: {message}")
                            self._process_message(message, client_socket)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[NET] Lỗi nhận dữ liệu từ {address}: {e}")
                    break
        
        finally:
            # Xóa client khỏi dictionary
            with self.clients_lock:
                if client_socket in self.clients:
                    client_info = self.clients.pop(client_socket)
                    print(f"[NET] ❌ ESP32 ngắt kết nối: {address} (Type: {client_info['type']})")
            
            # Đóng socket
            try:
                client_socket.close()
            except:
                pass
            
            self.esp_disconnected.emit()
    
    def _process_message(self, message, client_socket):
        """Xử lý message từ ESP32"""
        parts = message.split(':')
        
        if len(parts) == 0:
            return
        
        command = parts[0]
        
        # CARD:<UID>:<LANE>
        if command == "CARD" and len(parts) >= 3:
            try:
                card_uid = parts[1]
                lane = int(parts[2])
                print(f"[NET] 🎫 Quét thẻ: {card_uid} tại làn {lane}")
                self.card_scanned.emit(card_uid, lane)
                
                # Đánh dấu client này là ESP32 Main
                with self.clients_lock:
                    if client_socket in self.clients:
                        self.clients[client_socket]['type'] = 'main'
                        
            except ValueError:
                print(f"[NET] ⚠️ Lỗi format CARD: {message}")
        
        # CHECKOUT:<LANE>
        elif command == "CHECKOUT" and len(parts) >= 2:
            try:
                lane = int(parts[1])
                print(f"[NET] 🚗 Checkout không thẻ tại làn {lane}")
                self.card_scanned.emit("", lane)
            except ValueError:
                print(f"[NET] ⚠️ Lane number không hợp lệ: {parts[1]}")
        
        # CLOSED:<LANE>
        elif command == "CLOSED" and len(parts) >= 2:
            try:
                lane = int(parts[1])
                print(f"[NET] 🚧 Barie làn {lane} đã đóng")
                # Emit signal
                self.barrier_closed.emit(lane)
            except ValueError:
                pass
        
        elif message == "HELLO_FROM_ESP32":
            print(f"[NET] 👋 ESP32 Main chào hỏi - Kết nối thành công!")
            
            # Đánh dấu client này là ESP32 Main
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]['type'] = 'main'
            
            # Gửi lại tin xác nhận
            self._send_to_client(client_socket, "ACK")
        
        elif parts[0] == "HELLO" and len(parts) >= 3:
            # Format: HELLO:ZONE_1:SLOTS_10
            # Handshake từ Node cảm biến
            zone_info = parts[1]  # ZONE_1
            slots_info = parts[2]  # SLOTS_10
            
            # Parse zone_id
            try:
                zone_id = int(zone_info.split('_')[1])
            except:
                zone_id = 1
            
            print(f"[NET] 🤝 ESP32 Node2 (Sensor) kết nối: {zone_info}, {slots_info}")
            
            # Đánh dấu client này là sensor node
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients[client_socket]['type'] = 'sensor'
                    self.clients[client_socket]['zone_id'] = zone_id
            
            self._send_to_client(client_socket, "OK")
        
        elif parts[0] == "PARKING_DATA" and len(parts) >= 5:
            # Format: PARKING_DATA:1:1010001101:5:5
            # zone_id, status_binary, occupied, available
            try:
                zone_id = int(parts[1])
                status_binary = parts[2]
                occupied = int(parts[3])
                available = int(parts[4])
                
                print(f"[NET] 📊 Sensor Data: Zone={zone_id}, "
                      f"Binary={status_binary}, Occ={occupied}, Avail={available}")
                
                # Emit signal để xử lý
                self.sensor_data_received.emit(zone_id, status_binary, occupied, available)
                
            except (ValueError, IndexError) as e:
                print(f"[NET] ⚠️ Invalid PARKING_DATA format: {message}")
        
        elif parts[0] == "HEARTBEAT":
            # Format: HEARTBEAT:ZONE_1:192.168.1.3:RSSI_-42
            # print(f"[NET] 💓 Heartbeat từ {parts[2]}, RSSI: {parts[3]}")
            pass  # Không log heartbeat nữa để giảm spam
        
        else:
            print(f"[NET] ⚠️ Lệnh không xác định: {message}")
    
    def _send_to_client(self, client_socket, command):
        """Gửi lệnh đến một client cụ thể"""
        try:
            message = command + '\n'
            client_socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[NET] ❌ Lỗi gửi đến client: {e}")
            return False
    
    def send_command(self, command, target='main'):
        """
        Gửi lệnh xuống ESP32
        
        Args:
            command: Lệnh cần gửi
            target: 'main' (ESP32 chính), 'sensor' (Node cảm biến), 'all' (tất cả)
        """
        sent_count = 0
        
        with self.clients_lock:
            for client_socket, info in self.clients.items():
                if target == 'all' or info['type'] == target:
                    if self._send_to_client(client_socket, command):
                        sent_count += 1
                        print(f"[NET] 📤 Đã gửi: {command} → {info['type']} ({info['address'][0]})")
        
        if sent_count == 0:
            print(f"[NET] ⚠️ Không có client {target} để gửi")
            return False
        
        return True
    
    def open_barrier(self, lane_number):
        """Mở barie (lane: 1 hoặc 2) - chỉ gửi đến ESP32 Main"""
        return self.send_command(f"OPEN_{lane_number}", target='main')
    
    def send_lcd_message(self, line1, line2):
        """Gửi message hiển thị lên LCD ESP32 - chỉ gửi đến ESP32 Main"""
        return self.send_command(f"MSG:{line1}|{line2}", target='main')
    
    def is_connected(self, client_type='main'):
        """Kiểm tra ESP có kết nối không"""
        with self.clients_lock:
            for info in self.clients.values():
                if info['type'] == client_type:
                    return True
        return False
    
    def get_connected_clients(self):
        """Lấy danh sách các client đang kết nối"""
        with self.clients_lock:
            return [(info['address'][0], info['type'], info.get('zone_id')) 
                    for info in self.clients.values()]
