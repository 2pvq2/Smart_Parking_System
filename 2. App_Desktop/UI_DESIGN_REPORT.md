# THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG - BÁOCÁO ĐỒ ÁN
## Hệ Thống Quản Lý Bãi Đỗ Xe Thông Minh (Smart Parking System)

---

## I. GIỚI THIỆU VỀ THIẾT KẾ GIAO DIỆN

Giao diện người dùng (User Interface - UI) là một thành phần quan trọng trong hệ thống quản lý bãi đỗ xe thông minh, đóng vai trò như cầu nối giữa hệ thống phần cứng IoT và các nhân viên vận hành. Thiết kế giao diện được thực hiện bằng framework PySide6 - một wrapper Python của thư viện Qt, cho phép xây dựng các ứng dụng desktop mạnh mẽ và chuyên nghiệp.

Mục tiêu chính của thiết kế giao diện này là:
- **Tính thân thiện:** Giao diện dễ sử dụng, không cần đào tạo nâng cao
- **Tính hiệu quả:** Các chức năng được sắp xếp hợp lý, giảm thời gian thao tác
- **Tính tin cậy:** Hiển thị thông tin chính xác, cập nhật real-time
- **Tính mở rộng:** Dễ dàng thêm các chức năng mới trong tương lai

---

## II. KIẾN TRÚC GIAO DIỆN TỔNG THỂ

Ứng dụng desktop được thiết kế theo mô hình **Master-Detail** với cấu trúc hai khu vực chính: khu vực điều hướng bên trái (Sidebar) và khu vực nội dung chính (Main Content Area).

### 2.1 Sidebar - Khu vực Điều Hướng

Sidebar được thiết kế ở phía bên trái cửa sổ ứng dụng, chiếm khoảng 200 pixels chiều rộng. Nó sử dụng một gradient màu xanh đậm chuyển từ `#1e3a8a` sang `#0f172a`, tạo ra một hình ảnh chuyên nghiệp và dễ phân biệt với khu vực nội dung. 

Sidebar chứa 6 nút điều hướng chính, mỗi nút đại diện cho một trang chức năng khác nhau:

1. **Dashboard (🏠)** - Trang chủ hiển thị tình trạng tổng quát
2. **Tìm Kiếm (🔍)** - Tra cứu thông tin xe
3. **Vé Tháng (💳)** - Quản lý vé tháng hạn
4. **Lịch Sử (📜)** - Xem lịch sử giao dịch
5. **Thống Kê (📈)** - Báo cáo doanh thu
6. **Cài Đặt (⚙️)** - Cấu hình hệ thống

Ngoài ra, còn có nút **Đăng Xuất (🚪)** ở cuối để người dùng kết thúc phiên làm việc. Các nút được thiết kế với hiệu ứng hover - khi di chuyển chuột vào nút, màu nền sẽ thay đổi nhẹ (fade in với độ trong suốt 10%), và nút hiện tại được active sẽ có một gradient màu xanh sang tím để phân biệt rõ ràng.

### 2.2 Main Content Area - Khu vực Nội Dung

Khu vực nội dung chính chiếm phần còn lại của cửa sổ (khoảng 1080 pixels chiều rộng). Nó sử dụng một `QStackedWidget` - một thành phần Qt cho phép xếp chồng nhiều trang widget và hiển thị chỉ một trang tại một thời điểm. Khi người dùng click vào một nút trong Sidebar, trang tương ứng sẽ được tải lên và hiển thị trong khu vực này.

Cách tiếp cận này có nhiều lợi ích:
- **Hiệu suất:** Các trang được tải trước và lưu trong bộ nhớ, chuyển đổi giữa các trang diễn ra nhanh chóng
- **Mượt mà:** Không cần reload dữ liệu khi quay lại trang cũ
- **Linh hoạt:** Dễ dàng thêm hoặc xóa trang mà không ảnh hưởng đến cấu trúc chính

Kích thước cửa sổ mặc định là 1280×800 pixels, phù hợp với hầu hết các màn hình máy tính để bàn. Tuy nhiên, ứng dụng hỗ trợ thay đổi kích thước động (resizable), và các thành phần UI sẽ tự động điều chỉnh để phù hợp.

---

## III. Mописание CÁC TRANG CHỨC NĂNG

### 3.1 Trang Dashboard - Trung Tâm Điều Hành

Trang Dashboard là trang chủ của hệ thống, được hiển thị mặc định khi ứng dụng khởi động. Đây là nơi mà nhân viên vận hành có thể nhanh chóng nắm bắt tình trạng toàn bộ bãi đỗ xe.

Trang này được chia thành ba khu vực chính:

**Khu vực 1: Thống Kê Nhanh (Statistics Cards)**

Ở phía trên cùng, có bốn thẻ thông tin được sắp xếp theo hàng ngang. Mỗi thẻ hiển thị một chỉ số quan trọng:
- Số lượng xe vào trong ngày hôm nay (hình biểu tượng xe 🚗 màu xanh)
- Số lượng xe ra trong ngày hôm nay (hình biểu tượng xe 🚗)
- Số chỗ trống cho xe máy (tỷ lệ kiểu "3/5 chỗ")
- Số chỗ trống cho ô tô (tỷ lệ kiểu "2/5 chỗ")

Các thẻ này được cập nhật real-time, tức là dữ liệu sẽ thay đổi ngay khi có xe vào/ra. Thiết kế các thẻ sử dụng nền màu nhạt (#f9fafb), viền mỏng màu xám (#e5e7eb), và các góc bo tròn (border-radius: 8px) để tạo ra sự mềm mại, hiện đại.

**Khu vực 2: Streams Camera**

Bên dưới thống kê, có hai khung hình camera được hiển thị song song:
- **Camera Cổng Vào (Lane 1):** Hiển thị hình ảnh từ camera ở lối vào bãi
- **Camera Cổng Ra (Lane 2):** Hiển thị hình ảnh từ camera ở lối ra bãi

Mỗi khung hình có kích thước 640×360 pixels, đủ lớn để nhân viên có thể nhìn rõ biển số xe. Các stream này được cập nhật liên tục thông qua một thread riêng (CameraThread), để đảm bảo UI thread không bị block. Nếu camera không khả dụng, các khung sẽ hiển thị hình ảnh placeholder màu xám.

**Khu vực 3: Sơ Đồ Bãi Đỗ (Parking Map)**

Phía dưới cùng là sơ đồ bãi đỗ xe được vẽ động dưới dạng lưới 2 hàng 5 cột (tổng cộng 10 slot). Mỗi slot được biểu diễn bằng một nút button với kích thước 140×100 pixels. Tùy vào trạng thái, các nút sẽ có màu khác nhau:

- **Xanh lá (#22c55e):** Slot trống, sẵn sàng đón xe
- **Đỏ (#ef4444):** Slot đã có xe đỗ
- **Vàng (#eab308):** Slot dành riêng cho khách vé tháng, đã có xe đỗ

Mỗi nút hiển thị tên slot (ví dụ "M1", "A1") và kí hiệu "(GUEST)" hoặc "(MONTHLY)". Sơ đồ này được cập nhật liên tục từ dữ liệu cảm biến của ESP32 Node2, cho phép nhân viên theo dõi tình trạng từng slot cụ thể.

**Khu vực 4: Điều Khiển**

Ở cuối cùng, có hai nút lớn để mở barie của hai làn:
- **[Mở Cổng 1]** - Gửi lệnh OPEN_1 để mở barie làn vào
- **[Mở Cổng 2]** - Gửi lệnh OPEN_2 để mở barie làn ra

Những nút này chỉ được sử dụng trong trường hợp khẩn cấp hoặc khi hệ thống tự động không hoạt động bình thường.

### 3.2 Trang Tìm Kiếm - Tra Cứu Thông Tin Xe

Trang này cho phép nhân viên nhanh chóng tra cứu thông tin về một chiếc xe cụ thể dựa vào biển số. Giao diện rất đơn giản: một ô nhập liệu (QLineEdit) ở phía trên cho phép nhân viên gõ vào biển số xe, và một bảng kết quả ở phía dưới.

Bảng kết quả hiển thị các thông tin chi tiết như:
- Biển số xe
- Loại xe (Xe máy hay Ô tô)
- Thời gian vào bãi
- Thời gian ra bãi (nếu đã ra)
- Phí dự tính (tính toán dựa trên thời gian lưu trú)

Khi nhân viên gõ vào ô tìm kiếm, bảng sẽ cập nhật ngay lập tức thông qua kế nối signal-slot của Qt. Nếu không tìm thấy, bảng sẽ hiển thị trống.

### 3.3 Trang Vé Tháng - Quản Lý Khách Hàng Thường Xuyên

Trang này là một phần quan trọng của hệ thống, phục vụ quản lý khách hàng có vé tháng hạn. Trang được chia thành hai phần chính:

**Phần 1: Form Đăng Ký Vé Tháng Mới**

Một form với các trường nhập liệu:
- **Biển số xe:** Ô nhập văn bản
- **Tên chủ xe:** Ô nhập văn bản
- **Mã thẻ RFID:** Ô chỉ đọc + nút "Quét thẻ"
  
  Đây là một cải tiến quan trọng - thay vì nhân viên phải gõ tay mã thẻ (dễ sai), họ chỉ cần click nút "Quét thẻ" và quét thẻ RFID vào đầu đọc ở làn vào. Một dialog sẽ xuất hiện chờ quét, và khi quét xong, mã sẽ tự động điền vào ô. Nếu không quét được trong 30 giây hoặc nhân viên click "Hủy", form sẽ quay trở lại trạng thái bình thường.

- **Loại xe:** Dropdown menu (Xe máy / Ô tô)
- **Ô đỗ riêng:** Radio button (Riêng / Vãng lai)
- **Ảnh đại diện:** Nút "Tải ảnh" để chọn ảnh từ máy tính
- **Thời gian hiệu lực:** Date picker để chọn ngày đăng ký và ngày hết hạn

Khi nhân viên click "Đồng ý", một dialog thanh toán sẽ xuất hiện cho phép chọn phương thức thanh toán (tiền mặt / chuyển khoản / QR code). Sau khi xác nhận thanh toán, vé tháng sẽ được lưu vào database và danh sách sẽ tự động cập nhật.

**Phần 2: Danh Sách Vé Tháng Đang Hoạt Động**

Một bảng hiển thị tất cả vé tháng hiện tại với 8 cột:
1. Biển số
2. Tên chủ xe
3. Mã thẻ RFID
4. Loại xe
5. Ngày đăng ký
6. Ngày hết hạn
7. Ô đỗ riêng được gán
8. Ảnh đại diện (với nút "Xem ảnh")

Ở phía trên bảng, có một ô tìm kiếm để nhân viên có thể lọc danh sách theo biển số, tên hoặc mã thẻ. Bảng hỗ trợ phân trang (pagination), mỗi trang hiển thị khoảng 10-15 hàng, với các nút "Trước" và "Sau" để chuyển trang.

Mỗi hàng trong bảng có các nút hành động:
- **[Xem ảnh]** - Hiển thị ảnh đại diện của khách (trong popup)
- **[Gia hạn]** - Mở dialog để chọn thời hạn gia hạn (1/3/6/12 tháng)
- **[Xóa]** - Xóa vé tháng khỏi hệ thống (soft delete - chỉ đánh dấu là inactive, không xóa vật lý khỏi DB)

### 3.4 Trang Lịch Sử - Ghi Nhận Giao Dịch

Trang Lịch Sử (Entry/Exit History) cung cấp một bản ghi chi tiết về tất cả các giao dịch trong hệ thống - mỗi khi một chiếc xe vào hoặc ra bãi, một bản ghi sẽ được tạo.

**Khu vực Bộ Lọc:**

Ở phía trên bảng, có các công cụ lọc:
- **Ngày từ / đến:** Hai date picker để chọn khoảng thời gian cần xem
- **Loại xe:** Dropdown (Tất cả / Xe máy / Ô tô)
- **Loại vé:** Dropdown (Tất cả / Vé ngắn hạn / Vé tháng)
- **Nút [Áp dụng]:** Click để load lại dữ liệu theo các bộ lọc đã chọn

**Bảng Dữ Liệu:**

Bảng chính hiển thị các cột:
1. Biển số xe
2. Loại xe
3. Thời gian vào
4. Thời gian ra
5. Thời gian lưu trú (tính tự động)
6. Phí thanh toán (tính theo giá cước)
7. Phương thức thanh toán (Tiền mặt / Chuyển khoản / Vé tháng)

Bảng cũng hỗ trợ phân trang, mỗi trang hiển thị 20 bản ghi, với các nút điều hướng ở cuối.

### 3.5 Trang Thống Kê - Báo Cáo Doanh Thu

Trang Thống Kê (Statistics) là một công cụ mạnh mẽ cho các nhà quản lý, cho phép họ phân tích doanh thu, xu hướng, và hiệu suất của bãi đỗ.

**Khu vực Bộ Lọc Thời Gian:**

Ở phía trên cùng, có các nút nhanh:
- **[Hôm nay]** - Hiển thị dữ liệu của ngày hôm nay
- **[Tháng này]** - Hiển thị 30 ngày gần nhất
- **[Năm nay]** - Hiển thị 365 ngày gần nhất
- **[Tùy chỉnh]** - Cho phép chọn khoảng thời gian bất kỳ

**Khu vực Tóm Tắt Doanh Thu (Summary Cards):**

Bốn thẻ hiển thị các con số chủ yếu:
- Tổng doanh thu (trong khoảng thời gian đã chọn)
- Doanh thu trung bình mỗi ngày
- Tổng số lượt xe (vào + ra)
- Tỷ lệ chiếm dụng bãi (%)

**Các Biểu Đồ:**

Trang này bao gồm ba loại biểu đồ khác nhau:

1. **Biểu đồ Cột (Bar Chart):** Hiển thị doanh thu theo từng ngày trong khoảng thời gian đã chọn. Trục X là các ngày, trục Y là doanh thu (tính bằng VND). Nhân viên có thể nhìn ngay thấy những ngày "kinh doanh tốt" và những ngày "yên tĩnh".

2. **Biểu đồ Tròn (Pie Chart):** Hiển thị tỷ lệ xe máy so với ô tô trong tổng số lượt xe. Ví dụ, nếu trong tháng có 60% xe máy và 40% ô tô, biểu đồ sẽ hiển thị bằng hai phần cung tròn với các màu khác nhau.

3. **Biểu đồ Đường (Line Chart):** Hiển thị xu hướng doanh thu theo thời gian - nó giúp phát hiện các mô hình (pattern) như "doanh thu luôn cao vào ngày thứ năm" hoặc "doanh thu giảm vào mùa hè".

Tất cả các biểu đồ được vẽ động sử dụng thư viện PyQtGraph, cung cấp hiệu suất cao và có thể vẽ số lượng điểm dữ liệu lớn mà không bị lag.

### 3.6 Trang Cài Đặt - Cấu Hình Hệ Thống

Trang Cài Đặt (Settings) cho phép các nhà quản lý cấu hình các thông số của hệ thống.

**Phần 1: Thông Tin Bãi Đỗ**

Các ô nhập liệu cho:
- Tên bãi đỗ (ví dụ "Bãi đỗ xe Trung Tâm Hà Nội")
- Địa chỉ đầy đủ
- Số điện thoại liên hệ

Những thông tin này sẽ được hiển thị trên các biên lai và báo cáo.

**Phần 2: Giá Vé**

Bãi đỗ xe sử dụng hệ thống giá khối (tiered pricing). Nhà quản lý có thể cấu hình:
- Giá xe máy khối 1: Giá cho 2 giờ đầu (ví dụ 25.000 VND)
- Giá xe máy khối 2: Giá theo giờ cho các giờ tiếp theo (ví dụ 10.000 VND/giờ)
- Giá ô tô khối 1: Giá cho 2 giờ đầu (ví dụ 35.000 VND)
- Giá ô tô khối 2: Giá theo giờ cho các giờ tiếp theo (ví dụ 15.000 VND/giờ)
- Giá vé tháng xe máy (ví dụ 500.000 VND/tháng)
- Giá vé tháng ô tô (ví dụ 1.000.000 VND/tháng)

Các giá này được lưu trữ trong database dưới dạng cài đặt (settings table), cho phép thay đổi linh hoạt mà không cần chỉnh sửa mã nguồn.

**Phần 3: Cấu Hình Phần Cứng**

Các ô nhập liệu cho:
- Địa chỉ IP của ESP32 Main (để kết nối TCP)
- Địa chỉ IP của ESP32 Node2 Sensor
- Port TCP (mặc định 8888)
- Số lượng slot xe máy (mặc định 5)
- Số lượng slot ô tô (mặc định 5)

**Phần 4: Quản Lý Người Dùng**

Một bảng hiển thị danh sách nhân viên với các cột:
- ID
- Tên đăng nhập
- Họ tên
- Chức vụ (ADMIN / STAFF)
- Trạng thái (Hoạt động / Vô hiệu)
- Điện thoại

Có các nút:
- **[➕ Thêm]** - Mở form để thêm người dùng mới
- **[✏️ Sửa]** - Chỉnh sửa thông tin người dùng đã chọn
- **[🗑️ Xóa]** - Xóa người dùng
- **[🔑 Đặt lại mật khẩu]** - Reset mật khẩu về mặc định

Chỉ ADMIN mới có quyền truy cập trang này. Nếu một STAFF cố gắng vào, hệ thống sẽ hiển thị thông báo "Từ chối truy cập".

---

## IV. DIALOG VÀ CÁC CỬA SỔ PHỤ

### 4.1 Dialog Đăng Nhập

Khi ứng dụng khởi động, trước tiên sẽ hiển thị một dialog đăng nhập. Dialog này yêu cầu nhân viên nhập:
- **Tên đăng nhập (Username):** Ô QLineEdit bình thường
- **Mật khẩu (Password):** Ô QLineEdit với mode EchoMode.Password (ẩn ký tự)

Nút **[Đăng nhập]** sẽ gửi thông tin đến database để xác thực. Nếu sai, sẽ hiển thị thông báo lỗi. Nếu đúng, dialog sẽ đóng và MainWindow sẽ hiển thị. Dữ liệu đăng nhập được lưu để kiểm tra quyền truy cập (ADMIN hay STAFF).

### 4.2 Dialog Thanh Toán

Khi một xe ra bãi hoặc khi đăng ký vé tháng, một dialog thanh toán sẽ xuất hiện để nhân viên chọn phương thức.

Dialog có ba tab (page) được quản lý bằng QStackedWidget:

**Tab 1 - Tiền Mặt (Cash):**
```
Hiển thị: "✅ Nhân viên xác nhận đã nhận tiền mặt"
```
Nhân viên sẽ xác nhận là họ đã nhận tiền từ khách, sau đó click "Xác nhận thanh toán".

**Tab 2 - Chuyển Khoản (Bank Transfer):**
```
Hiển thị thông tin tài khoản ngân hàng:
- Ngân hàng: VCB (Vietcombank)
- Số tài khoản: 1234567890
- Chủ tài khoản: CÔNG TY BÃI ĐỖ XE
```
Khách sẽ chuyển tiền đến tài khoản này, nhân viên xác nhận sau khi kiểm tra.

**Tab 3 - QR Code:**
```
Hiển thị mã QR để khách quét bằng smartphone
Có thể là mã chuyển khoản VietQR hoặc link thanh toán online
```

Ở cuối dialog, hai nút:
- **[❌ Hủy]** - Hủy giao dịch
- **[✅ Xác nhận thanh toán]** - Xác nhận đã thanh toán và đóng dialog

### 4.3 Dialog Quét Thẻ RFID

Khi nhân viên click nút "Quét thẻ" trong form đăng ký vé tháng, dialog này sẽ xuất hiện:

```
┌─────────────────────────────────┐
│ Quét thẻ RFID                   │
├─────────────────────────────────┤
│                                 │
│ Vui lòng đưa thẻ RFID vào       │
│ đầu đọc...                      │
│                                 │
│ Đang chờ...                     │
│ (hoặc ✅ Đã quét: A1B2C3D4)     │
│                                 │
│              [Hủy]              │
│                                 │
└─────────────────────────────────┘
```

Dialog này sẽ chờ lắng nghe tín hiệu `card_scanned` từ NetworkServer. Khi ESP32 gửi tin nhắn "CARD:UID:LANE", tín hiệu sẽ được phát ra, callback sẽ được gọi, và mã thẻ sẽ được điền vào ô trong form. Dialog sẽ tự động đóng sau 1.5 giây.

Việc kết nối tín hiệu sử dụng `Qt.DirectConnection` để đảm bảo signal được xử lý ngay lập tức, không bị queue lại.

---

## V. CÔNG NGHỆ VÀ FRAMEWORK SỬ DỤNG

### 5.1 PySide6 - Qt for Python

PySide6 là một framework để xây dựng giao diện người dùng đa nền tảng bằng Python. Nó là wrapper (bộ bao) của thư viện C++ Qt, cung cấp:
- **Widget:** Các thành phần UI cơ bản (Button, Label, LineEdit, etc.)
- **Layout:** Các bộ sắp xếp (VBox, HBox, Grid) để tổ chức widget
- **Signal-Slot:** Cơ chế kết nối sự kiện - nếu user click nút, signal được phát ra, slot tương ứng sẽ được gọi
- **QUiLoader:** Tải các file .ui (XML) được tạo bởi Qt Designer

### 5.2 Qt Designer - Thiết Kế Visual

Các file .ui được tạo bằng một công cụ đồ họa tên là Qt Designer. Đây là công cụ WYSIWYG (What You See Is What You Get) - nhà phát triển có thể kéo thả các widget lên canvas, đặt lên layout, và công cụ sẽ sinh ra code XML tương ứng.

Các file .ui được lưu dưới dạng XML:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
   <!-- các widget con được định nghĩa ở đây -->
   <widget class="QPushButton" name="btnDashboard">
     <property name="text"><string>Dashboard</string></property>
     ...
   </widget>
 </widget>
</ui>
```

Trong main.py, các file .ui được tải động bằng QUiLoader:
```python
loader = QUiLoader()
file = QFile("ui/app_mainwindow.ui")
widget = loader.load(file)
```

Cách tiếp cận này có lợi ích:
- **Tách biệt:** Logic code và giao diện được tách riêng
- **Dễ bảo trì:** Có thể chỉnh giao diện mà không cần chạy code
- **Tái sử dụng:** Cùng một file .ui có thể được tải nhiều lần

### 5.3 Stylesheet (QSS)

QSS (Qt Style Sheets) là một công cụ để styling UI, tương tự CSS trong web. Nó được lưu trong file `styles.qss`:

```css
/* Global Styles */
QWidget {
  background: #ffffff;
  color: #0f172a;
  font-family: "Segoe UI", Roboto;
}

/* Sidebar */
QWidget#sidebar {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
              stop:0 #1e3a8a, stop:1 #0f172a);
}

/* Button */
QPushButton {
  background-color: #2563eb;
  color: white;
  border-radius: 4px;
  padding: 8px 16px;
}

QPushButton:hover {
  background-color: #1d4ed8;
}
```

File QSS được tải ở đầu ứng dụng:
```python
with open("ui/styles.qss") as f:
    app.setStyleSheet(f.read())
```

Tất cả các widget sẽ tự động áp dụng các style này.

### 5.4 Threading - Xử Lý Đa Luồng

UI của Qt là single-threaded - nếu bạn thực hiện một tác vụ nặng (như đọc từ camera) trong main thread, giao diện sẽ bị đông cứng.

Để giải quyết, ứng dụng sử dụng hai thread phụ:

**CameraThread - Xử lý Camera:**
```python
class CameraThread(QThread):
    frame_ready = Signal(np.ndarray)  # Signal phát ra khi có frame mới
    
    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret:
                self.frame_ready.emit(frame)
```

Thread này chạy một vòng lặp vô hạn, đọc frame từ camera liên tục, và phát signal mỗi khi có frame mới. Main thread sẽ lắng nghe signal này và cập nhật QLabel.

**NetworkServer - Nhận Dữ Liệu ESP32:**
```python
class NetworkServer(QObject):
    card_scanned = Signal(str, int)  # Signal khi quét thẻ
    
    def _run_server(self):
        while self.running:
            client, addr = self.server_socket.accept()
            # Thread mới để xử lý client này
            threading.Thread(target=self._handle_client, 
                           args=(client,)).start()
```

Network server chạy trong một thread riêng, lắng nghe các kết nối TCP từ ESP32. Khi có tin nhắn "CARD:...", server sẽ parse và phát signal `card_scanned`, mà main thread sẽ lắng nghe.

---

## VI. CƠ CHẾ SIGNAL-SLOT

Signal-Slot là cơ chế chính để giao tiếp giữa các thành phần trong Qt. Một signal là một tin hiệu được phát ra khi một sự kiện xảy ra, và một slot là một hàm sẽ được gọi khi tín hiệu được phát ra.

### 6.1 Ví Dụ: Click Button

```python
# 1. Định nghĩa signal
class NetworkServer(QObject):
    card_scanned = Signal(str, int)  # (card_uid, lane_number)

# 2. Phát signal
def _process_message(self, message):
    if message.startswith("CARD:"):
        uid, lane = parse_card(message)
        self.card_scanned.emit(uid, lane)  # ← Phát signal tại đây

# 3. Kết nối signal với slot
server = NetworkServer()
server.card_scanned.connect(self.handle_card_scan)

# 4. Định nghĩa slot
@Slot(str, int)
def handle_card_scan(self, uid, lane):
    # Hàm này sẽ được gọi khi card_scanned signal được phát
    print(f"Quét thẻ: {uid} tại làn {lane}")
```

Ưu điểm:
- **Loose coupling:** Các thành phần không cần biết nhau tồn tại
- **Asynchronous:** Signal có thể được phát từ thread khác
- **Flexible:** Một signal có thể kết nối với nhiều slot

---

## VII. TỪ ĐIỀU HƯỚNG (Navigation)

Khi user click một nút trong Sidebar, cách nó hoạt động như sau:

```python
# 1. Setup (trong __init__)
btn_dashboard = sidebar.findChild(QPushButton, "btnDashboard")
btn_dashboard.clicked.connect(lambda: self.switch_page("dashboard"))

# 2. Hàm switch_page
def switch_page(self, page_name):
    if page_name in self.loaded_pages:
        widget = self.loaded_pages[page_name]
        self.stacked_widget.setCurrentWidget(widget)
        # Cập nhật CSS để highlight nút đang active
        self.update_active_button(page_name)
```

QStackedWidget là một widget chứa nhiều widget con, nhưng chỉ hiển thị một lần. Khi gọi `setCurrentWidget()`, widget đó sẽ được hiển thị, các widget khác sẽ bị ẩn.

---

## VIII. CẬP NHẬT DỮ LIỆU REAL-TIME

Dữ liệu trong ứng dụng được cập nhật real-time thông qua các cơ chế:

### 8.1 Timer-Based Updates (Cập nhật dựa trên Timer)

```python
# Trong __init__ của MainWindow
self.update_timer = QTimer()
self.update_timer.timeout.connect(self.update_dashboard_stats)
self.update_timer.start(3000)  # Cập nhật mỗi 3 giây

# Hàm cập nhật
def update_dashboard_stats(self):
    # Lấy dữ liệu từ DB
    total_in = self.db.count_entries_today()
    total_out = self.db.count_exits_today()
    
    # Cập nhật UI
    self.lbl_total_in.setText(str(total_in))
    self.lbl_total_out.setText(str(total_out))
```

Mỗi 3 giây, dữ liệu sẽ được refresh từ database. Tần suất này được chọn để cân bằng giữa độ chính xác (cập nhật nhanh) và hiệu suất (không quá thường xuyên).

### 8.2 Signal-Based Updates (Cập nhật dựa trên Signal)

Khi có sự kiện quan trọng (ví dụ quét thẻ), signal được phát ngay lập tức:

```python
# NetworkServer phát signal
self.card_scanned.emit(uid, lane)

# MainWindow lắng nghe
self.network_server.card_scanned.connect(self.handle_card_scan)

# Slot được gọi ngay
@Slot(str, int)
def handle_card_scan(self, uid, lane):
    # Xử lý và cập nhật UI ngay lập tức
    self.update_dashboard_stats()
```

---

## IX. PHỐI MÀU VÀ THIẾT KẾ (Color Scheme & Design)

### 9.1 Phối Màu Chính

Ứng dụng sử dụng một phối màu chuyên nghiệp với tập trung vào xanh và xám:

| Yếu tố | Màu | Mã Hex | Mục đích |
|--------|-----|--------|---------|
| Sidebar | Xanh đậm gradient | #1e3a8a → #0f172a | Menu chính |
| Button active | Xanh lam gradient | #2563eb → #7c3aed | Highlight |
| Slot trống | Xanh lá | #22c55e | Dễ nhìn, tích cực |
| Slot có xe | Đỏ | #ef4444 | Cảnh báo, chú ý |
| Slot vé tháng | Vàng | #eab308 | Phân biệt |
| Nền chính | Trắng | #ffffff | Sạch sẽ |
| Nền phụ | Xám nhạt | #f9fafb | Khác biệt |
| Border | Xám | #e5e7eb | Ngăn cách |
| Text chính | Xám đậm | #0f172a | Dễ đọc |
| Text phụ | Xám | #64748b | Phân cấp |

### 9.2 Hiệu Ứng & Animation

- **Hover Effect:** Khi di chuột vào button, background thay đổi nhẹ (fade in)
- **Active State:** Button hiện tại được highlight với gradient rõ ràng
- **Border Radius:** Tất cả button và card có các góc bo tròn (4-8px)
- **Padding & Spacing:** Có khoảng cách lành mạnh giữa các thành phần

### 9.3 Typography (Kiểu Chữ)

- **Font mặc định:** Segoe UI, Roboto, Helvetica (sans-serif)
- **Size chính:** 10pt
- **Size tiêu đề:** 12-14pt, bold
- **Line height:** 1.5 để dễ đọc

---

## X. CÁCH MỞ RỘNG VÀ BẢO TRÌ

### 10.1 Thêm Trang Mới

Để thêm một trang mới (ví dụ trang "Báo cáo"):

**Bước 1:** Tạo file .ui
- Mở Qt Designer
- File → New → Widget
- Thiết kế giao diện
- Save as: `ui/pages/report.ui`

**Bước 2:** Cập nhật main.py
```python
self.pages = {
    # ...
    "report": "report.ui",  # ← Thêm dòng này
}
```

**Bước 3:** Thêm nút sidebar
```python
btn_report = sidebar.findChild(QPushButton, "btnReport")
if btn_report:
    btn_report.clicked.connect(lambda: self.switch_page("report"))
```

**Bước 4:** Implement logic
```python
def setup_report_page(self, widget):
    """Setup logic cho trang Report"""
    btn_export = widget.findChild(QPushButton, "btnExport")
    if btn_export:
        btn_export.clicked.connect(self.export_report)
```

### 10.2 Thay Đổi Phối Màu

Chỉnh sửa file `ui/styles.qss`:
```css
QWidget#sidebar {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 #YOUR_COLOR1, stop:1 #YOUR_COLOR2);
}
```

Reload ứng dụng, phối màu sẽ được áp dụng ngay.

### 10.3 Tối Ưu Hiệu Suất

- **Pagination:** Bảng lớn nên được chia trang (20-50 hàng/trang)
- **Lazy Loading:** Chỉ tải dữ liệu khi user vào trang
- **Caching:** Lưu kết quả query để tái sử dụng
- **Async:** Sử dụng thread cho tác vụ nặng

---

## XI. KẾT LUẬN

Giao diện người dùng của hệ thống quản lý bãi đỗ xe thông minh được thiết kế với sự chú trọng đến tính thân thiện, hiệu quả, và chuyên nghiệp. Sử dụng framework PySide6, ứng dụng cung cấp một giao diện đa nền tảng (Windows, macOS, Linux) với cách tương tác trực quan.

Kiến trúc modular cho phép dễ dàng mở rộng với các tính năng mới, trong khi cơ chế signal-slot đảm bảo các thành phần giao tiếp một cách linh hoạt và hiệu quả. Việc tách biệt logic và UI bằng file .ui cũng giúp dự án dễ bảo trì và phát triển trong tương lai.

---

**Tài liệu này có thể được sử dụng trong báo cáo đồ án hoặc luận văn để mô tả chi tiết về thiết kế giao diện người dùng của hệ thống.**

