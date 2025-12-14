"""
Sensor Data Manager - Quản lý dữ liệu từ 10 cảm biến bãi đỗ xe
Nhận data từ ESP32 Node2 và đồng bộ với database
"""

from PySide6.QtCore import QObject, Signal
import time


class SensorDataManager(QObject):
    """Quản lý dữ liệu cảm biến real-time"""
    
    # ⚙️ CẤU HÌNH CÓ THỂ THAY ĐỔI
    MOTOR_SLOTS = 5  # Số slot xe máy
    CAR_SLOTS = 5    # Số slot ô tô
    SENSOR_TIMEOUT = 60  # Timeout 60 giây - nếu không có update sẽ reset sensor data
    
    # Signal thông báo khi có thay đổi số chỗ trống
    slots_changed = Signal(dict)  # {motor_occupied, motor_available, car_occupied, car_available}
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        # Dữ liệu cảm biến real-time
        self.sensor_data = {
            'zone_id': None,
            'status_binary': '0000000000',  # 10 cảm biến (0=trống, 1=có xe)
            'occupied_count': 0,
            'available_count': 10,
            'last_update': None
        }
        
        # Cấu hình (có thể thay đổi)
        self.total_sensor_slots = 10
        self.vehicle_type = "Xe máy"  # Mặc định zone này cho xe máy
        
        # Tracking slots
        self.sensor_slot_states = [False] * 10  # False=trống, True=có xe
        
        # Tracking để chỉ emit signal khi có thay đổi thực sự
        self.last_notified_data = None
        
    def set_vehicle_type(self, vehicle_type):
        """Cấu hình loại xe cho zone cảm biến này"""
        self.vehicle_type = vehicle_type
        print(f"[SENSOR] Zone cảm biến cấu hình cho: {vehicle_type}")
        
    def update_from_node(self, zone_id, status_binary, occupied, available):
        """
        Cập nhật dữ liệu từ Node cảm biến
        
        Args:
            zone_id: ID của zone (1-10)
            status_binary: Chuỗi binary 10 ký tự (VD: "1010001101")
            occupied: Số slot có xe
            available: Số slot trống
        """
        try:
            # Validate data
            if len(status_binary) != self.total_sensor_slots:
                print(f"[SENSOR] ⚠️ Invalid status binary length: {len(status_binary)}")
                return
                
            # Cập nhật dữ liệu
            self.sensor_data['zone_id'] = zone_id
            self.sensor_data['status_binary'] = status_binary
            self.sensor_data['occupied_count'] = occupied
            self.sensor_data['available_count'] = available
            self.sensor_data['last_update'] = time.time()
            
            # Parse binary string thành array
            for i, char in enumerate(status_binary):
                self.sensor_slot_states[i] = (char == '1')
            
            print(f"[SENSOR] 📊 Zone {zone_id}: {status_binary} | "
                  f"Occupied={occupied}, Available={available}")
            
            # Emit signal
            self._notify_changes()
            
        except Exception as e:
            print(f"[SENSOR] ❌ Lỗi update: {e}")
    
    def get_real_available_count(self):
        """
        Lấy số chỗ trống thực tế từ cảm biến
        Ưu tiên dữ liệu cảm biến hơn database
        
        Returns:
            int: Số chỗ trống thực tế
        """
        # Nếu có dữ liệu cảm biến gần đây (trong 30 giây)
        if self.sensor_data['last_update']:
            time_diff = time.time() - self.sensor_data['last_update']
            if time_diff < 30:  # Dữ liệu còn fresh
                return self.sensor_data['available_count']
        
        # Fallback: lấy từ database
        return self._get_db_available_count()
    
    def get_smart_available_count(self, db_motor_count, db_car_count):
        """
        Tính số chỗ trống thông minh cho TỪNG LOẠI XE (xe máy & ô tô)
        
        Data split:
        - Bits 0-4 = 5 xe máy
        - Bits 5-9 = 5 ô tô
        
        Logic:
        - Đếm occupied slots từ cảm biến cho mỗi loại
        - Tính smart available = min(sensor_available, db_available) cho từng loại
        - Tối ưu: không oversell
        
        Args:
            db_motor_count: Số xe máy đang parking trong DB
            db_car_count: Số ô tô đang parking trong DB
            
        Returns:
            dict: {motor_available, car_available}
        """
        result = {'motor_available': 5, 'car_available': 5}
        
        # Nếu có dữ liệu cảm biến fresh
        if self.sensor_data['last_update']:
            time_diff = time.time() - self.sensor_data['last_update']
            if time_diff < 30:
                binary = self.sensor_data['status_binary']
                
                # Đếm occupied slots cho mỗi loại từ binary
                motor_occupied = sum(1 for i in range(self.MOTOR_SLOTS) if binary[i] == '1')
                car_occupied = sum(1 for i in range(self.MOTOR_SLOTS, self.MOTOR_SLOTS + self.CAR_SLOTS) if binary[i] == '1')
                
                # Tính sensor available
                sensor_motor_available = self.MOTOR_SLOTS - motor_occupied
                sensor_car_available = self.CAR_SLOTS - car_occupied
                
                # Tính DB available
                db_motor_available = self.MOTOR_SLOTS - db_motor_count
                db_car_available = self.CAR_SLOTS - db_car_count
                
                # Lấy min (an toàn)
                result['motor_available'] = min(sensor_motor_available, db_motor_available)
                result['car_available'] = min(sensor_car_available, db_car_available)
                
                print(f"[SENSOR-SMART] MOTORCYCLE: Sensor={sensor_motor_available}, "
                      f"DB={db_motor_available}, Result={result['motor_available']}")
                print(f"[SENSOR-SMART] CAR: Sensor={sensor_car_available}, "
                      f"DB={db_car_available}, Result={result['car_available']}")
                
                return result
        
        # Fallback: dùng DB khi không có sensor
        result['motor_available'] = max(0, 5 - db_motor_count)
        result['car_available'] = max(0, 5 - db_car_count)
        print(f"[SENSOR-SMART] Fallback to DB: Motor={result['motor_available']}, Car={result['car_available']}")
        return result
    
    def get_occupied_slots(self):
        """Lấy danh sách các slot đang có xe (theo cảm biến)"""
        return [i for i, occupied in enumerate(self.sensor_slot_states) if occupied]
    
    def get_available_slots(self):
        """Lấy danh sách các slot trống (theo cảm biến)"""
        return [i for i, occupied in enumerate(self.sensor_slot_states) if not occupied]
    
    def is_data_fresh(self, max_age_seconds=30):
        """Kiểm tra dữ liệu cảm biến còn mới không"""
        if not self.sensor_data['last_update']:
            return False
        time_diff = time.time() - self.sensor_data['last_update']
        return time_diff < max_age_seconds
    
    def check_sensor_timeout(self):
        """
        Kiểm tra timeout của cảm biến
        Nếu quá SENSOR_TIMEOUT giây không có update, reset sensor data về mặc định
        Điều này tránh tình trạng UI hiển thị dữ liệu sensor cũ sau khi che cảm biến
        """
        if not self.sensor_data['last_update']:
            return False
            
        time_diff = time.time() - self.sensor_data['last_update']
        
        # Nếu timeout quá lâu, reset sensor data
        if time_diff > self.SENSOR_TIMEOUT:
            print(f"[SENSOR-TIMEOUT] ⚠️ Không có dữ liệu sensor trong {time_diff:.1f}s, reset dữ liệu")
            self._reset_sensor_data()
            return True
            
        return False
    
    def _reset_sensor_data(self):
        """Reset sensor data về trạng thái mặc định (tất cả trống)"""
        self.sensor_data = {
            'zone_id': None,
            'status_binary': '0000000000',  # Reset về tất cả trống
            'occupied_count': 0,
            'available_count': 10,
            'last_update': None
        }
        self.sensor_slot_states = [False] * 10
        print("[SENSOR] 🔄 Đã reset sensor data về trạng thái mặc định")
    
    @property
    def current_binary_status(self):
        """Property để dễ dàng truy cập binary status hiện tại"""
        # Kiểm tra timeout trước khi trả về binary
        self.check_sensor_timeout()
        return self.sensor_data['status_binary']
    
    def get_status_display(self):
        """Lấy chuỗi hiển thị trạng thái"""
        if not self.is_data_fresh():
            return "❌ Không có dữ liệu cảm biến"
        
        binary = self.sensor_data['status_binary']
        display = ""
        for i, char in enumerate(binary):
            if char == '1':
                display += f"[🚗]"
            else:
                display += f"[⬜]"
            if (i + 1) % self.MOTOR_SLOTS == 0:
                display += "\n"
        
        return display
    
    def _get_db_available_count(self):
        """Lấy số chỗ trống từ database (fallback)"""
        try:
            stats = self.db.get_parking_statistics()
            if self.vehicle_type == "Xe máy":
                return stats['motor_available']
            else:
                return stats['car_available']
        except:
            return self.total_sensor_slots
    
    def _notify_changes(self):
        """Thông báo khi có thay đổi"""
        try:
            # Tính toán thống kê
            stats = self.db.get_parking_statistics()
            
            # Lấy số xe đang parking trong DB
            motor_db_parking = stats['motor_total'] - stats['motor_available']
            car_db_parking = stats['car_total'] - stats['car_available']
            
            # Tính số chỗ trống thông minh cho từng loại
            smart_counts = self.get_smart_available_count(motor_db_parking, car_db_parking)
            motor_available = smart_counts['motor_available']
            car_available = smart_counts['car_available']
            motor_occupied = self.MOTOR_SLOTS - motor_available
            car_occupied = self.CAR_SLOTS - car_available
            
            # Tạo data mới
            data = {
                'motor_occupied': motor_occupied,
                'motor_available': motor_available,
                'car_occupied': car_occupied,
                'car_available': car_available
            }
            
            # CHỈ emit signal nếu có THAY ĐỔI thực sự
            if self.last_notified_data != data:
                self.slots_changed.emit(data)
                self.last_notified_data = data
                print(f"[SENSOR-NOTIFY] 📢 Slots changed: Motor {motor_available}/{self.MOTOR_SLOTS}, "
                      f"Car {car_available}/{self.CAR_SLOTS}")
            else:
                # Không log nếu không có thay đổi (giảm spam log)
                pass
            
        except Exception as e:
            print(f"[SENSOR] Lỗi notify: {e}")
    
    def print_debug_info(self):
        """In thông tin debug"""
        print("\n" + "="*60)
        print("SENSOR DATA MANAGER - DEBUG INFO")
        print("="*60)
        print(f"Zone ID: {self.sensor_data['zone_id']}")
        print(f"Vehicle Type: {self.vehicle_type}")
        print(f"Total Slots: {self.total_sensor_slots}")
        print(f"Status Binary: {self.sensor_data['status_binary']}")
        print(f"Occupied: {self.sensor_data['occupied_count']}")
        print(f"Available: {self.sensor_data['available_count']}")
        print(f"Last Update: {self.sensor_data['last_update']}")
        print(f"Data Fresh: {self.is_data_fresh()}")
        print(f"\nSlot States:")
        for i, state in enumerate(self.sensor_slot_states):
            status = "🚗" if state else "⬜"
            print(f"  Slot {i}: {status}")
        print("="*60 + "\n")
