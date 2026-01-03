# 📋 Giao Diện Login - Smart Parking System

## 📝 Giới Thiệu

Hệ thống đã được cập nhật với giao diện login an toàn, hỗ trợ hai loại tài khoản:
- **👤 Admin** - Quản trị viên hệ thống (toàn quyền)
- **👥 Staff** - Nhân viên quản lý (quyền hạn giới hạn)

## 🔐 Tài Khoản Mặc Định

### Admin
```
Tên đăng nhập: admin
Mật khẩu: admin123
```

### Nhân Viên (Staff)
```
Tên đăng nhập: staff1
Mật khẩu: staff123

Tên đăng nhập: staff2
Mật khẩu: staff123
```

## 🚀 Cách Chạy Ứng Dụng

### 1. Chạy từ Main
```bash
python main.py
```

Khi chạy, bạn sẽ thấy:
1. **Dialog Login** hiển thị
2. Nhập tên đăng nhập và mật khẩu
3. Nhấn **"Đăng Nhập"** hoặc Enter
4. Nếu thành công, ứng dụng chính sẽ mở

### 2. Chạy Login riêng (Test)
```bash
python login_dialog.py
```

### 3. Quản lý người dùng (Chỉ cho Admin)
```bash
python user_management.py
```

## 📌 Các Tính Năng

### ✅ Login Dialog
- ✓ Nhập tên đăng nhập và mật khẩu
- ✓ "Ghi nhớ tên đăng nhập" cho lần đăng nhập tiếp theo
- ✓ Xác thực MD5 mật khẩu
- ✓ Kiểm tra tài khoản có hoạt động không
- ✓ Thông báo lỗi rõ ràng

### 👨‍💼 User Management (Admin Only)
- ✓ Xem danh sách tất cả người dùng
- ✓ Thêm người dùng mới
- ✓ Chỉnh sửa thông tin (họ tên, chức vụ, số điện thoại)
- ✓ Kích hoạt/Vô hiệu hóa tài khoản
- ✓ Xóa người dùng
- ✓ Đặt lại mật khẩu

## 🔑 Mã Hóa Mật Khẩu

- Mật khẩu được mã hóa bằng **MD5** trước khi lưu vào database
- Khi đăng nhập, mật khẩu nhập vào sẽ được mã hóa rồi so sánh

## 📊 Cấu Trúc Database

### Bảng `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'STAFF',  -- 'ADMIN' hoặc 'STAFF'
    phone TEXT,
    is_active INTEGER DEFAULT 1,  -- 1: Hoạt động, 0: Vô hiệu
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🎨 Giao Diện

### Login Dialog
```
┌─────────────────────────────────────┐
│  🅿️ SMART PARKING SYSTEM             │
│  Hệ thống quản lý đỗ xe thông minh  │
├─────────────────────────────────────┤
│                                     │
│ Tên đăng nhập:                      │
│ [________________________]          │
│                                     │
│ Mật khẩu:                           │
│ [________________________]          │
│                                     │
│ ☐ Ghi nhớ tên đăng nhập             │
│                                     │
│ [✓ Đăng Nhập]  [Thoát]             │
│                                     │
└─────────────────────────────────────┘
```

## 🛡️ Bảo Mật

- ✓ Mật khẩu được mã hóa MD5
- ✓ Kiểm tra tài khoản hoạt động
- ✓ Ghi nhớ username (không ghi nhớ mật khẩu)
- ✓ Có thể vô hiệu hóa tài khoản mà không xóa

## 📝 Thay Đổi Mật Khẩu

Để đổi mật khẩu:

### Dành cho Admin:
1. Mở **User Management** (python user_management.py)
2. Chọn tài khoản cần đổi mật khẩu
3. Nhấn **"🔑 Đặt lại mật khẩu"**
4. Nhập mật khẩu mới

### Dành cho User:
Hiện tại chưa có tính năng tự đổi mật khẩu. Liên hệ Admin để được hỗ trợ.

## 🔗 File Liên Quan

- `login_dialog.py` - Dialog đăng nhập
- `user_management.py` - Quản lý người dùng (Admin)
- `main.py` - Ứng dụng chính (đã tích hợp login)
- `database.py` - Khởi tạo database và bảng users
- `core/db_manager.py` - Quản lý database

## 🐛 Ghi Chú

- Nếu chưa có tài khoản admin, hệ thống sẽ tạo mặc định (admin/admin123)
- Tài khoản demo staff1 và staff2 cũng được tạo tự động
- Username được ghi nhớ trong file `.login_config` (không bảo mật, chỉ thuận tiện)
- Để xóa ghi nhớ, xóa file `.login_config` hoặc bỏ check "Ghi nhớ tên đăng nhập"
