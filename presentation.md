---
marp: true
theme: default
class: invert
paginate: true
---

# KỊCH BẢN THUYẾT TRÌNH ĐỒ ÁN MÔN HỌC OOP
**Tên đồ án:** OnlyChess – Cờ Vua Mở Rộng
**Thành viên:** Nguyễn Văn Dũng, Phạm Bách Hiệp

<!-- 
Lời thoại: 
"Xin chào thầy và các bạn. Hôm nay nhóm chúng em xin trình bày về đồ án cuối kỳ môn OOP. Đồ án mang tên 'OnlyChess' – một tựa game Cờ vua mở rộng kết hợp với các cơ chế chiến thuật hiện đại."
-->

---

## 1. Ý tưởng & Đặt vấn đề

- **Vấn đề:** Cờ vua truyền thống có nhịp độ tĩnh.
- **Giải pháp:** Tăng tính "đột biến" có kiểm soát bằng cách kết hợp cơ chế của Boardgame hiện đại.
- **3 Cơ chế cốt lõi:**
  1. Dung hợp quân (Fusion)
  2. Kỹ năng chủ động (Abilities)
  3. Sự kiện toàn cục (Global Events)

<!-- 
Lời thoại:
"Cờ vua rất chặt chẽ nhưng thiếu yếu tố bất ngờ ở những ván đấu dài. Để giải quyết, nhóm đã thêm vào 3 cơ chế: Dung hợp quân, Kỹ năng, và Sự kiện. Việc này ép người chơi không chỉ giải quyết bài toán trên bàn cờ, mà còn phải quản lý tài nguyên và chuẩn bị cho rủi ro."
-->

---

## 2. Tính năng Cốt lõi (Standard Chess Core)

- Bàn cờ 8x8 tiêu chuẩn.
- Di chuyển chuẩn của 6 loại quân cờ.
- **Đầy đủ các luật phức tạp:**
  - Nhập thành (Castling)
  - Bắt tốt qua đường (En Passant)
  - Phong cấp (Promotion)
- **Đánh giá trạng thái:** Chiếu, Chiếu bí, Hòa cờ.

<!-- 
Lời thoại:
"Dù thêm thắt nhiều thứ, OnlyChess vẫn phải là một game Cờ vua. Nhóm đã tự xây dựng lại toàn bộ các luật cờ cơ bản từ đầu, bao gồm cả En Passant hay Castling, đảm bảo Game có thể phân định thắng thua một cách chuẩn xác nhất."
-->

---

## 3. Cơ chế Dung hợp (Fusion)

Bắt quân địch theo công thức sẽ sinh ra quân lai vĩnh viễn:

- Mã ăn Tượng ➡️ **Archbishop** *(Đi như Mã + Tượng)*
- Xe ăn Mã ➡️ **Chancellor** *(Đi như Xe + Mã)*
- Xe ăn Tượng ➡️ **Warden** *(Đi thẳng vô hạn + Chéo 3 ô)*
- Tượng ăn Xe ➡️ **Inquisitor** *(Đi chéo vô hạn + Thẳng 3 ô)*

<!-- 
Lời thoại:
"Điểm nhấn đầu tiên là Dung hợp. Khi một quân ăn quân đối phương khớp công thức, chúng hợp thể thành 1 siêu quân cờ. Cơ chế này ép người chơi phải cân nhắc kỹ: liệu mình ăn quân này thì đối phương có tạo ra một 'quái vật' khó lường hay không."
-->

---

## 4. Kỹ năng & Điểm hành động (AP)

Tích lũy tối đa 5 AP (tăng 1 AP sau mỗi 2 lượt). 

| Quân | Kỹ năng | AP | Tác dụng |
| :--- | :--- | :--- | :--- |
| **Mã** | Swap | 2 | Hoán đổi vị trí với đồng minh |
| **Tượng** | Snipe | 3 | Bắn tỉa quân địch từ xa |
| **Xe** | Shield | 3 | Tạo khiên bảo vệ (chặn 1 đòn tiêu diệt) |
| **Tốt** | Sprint | 1 | Chạy nhanh 3 ô (không bị cản) |

<!-- 
Lời thoại:
"Mỗi loại quân có một Kỹ năng riêng, tiêu tốn Điểm Hành Động (AP). Thay vì di chuyển, Tượng có thể tốn 3 AP để bắn tỉa từ xa. Việc quản lý tài nguyên AP hợp lý đóng vai trò cốt lõi trong việc giành chiến thắng."
-->

---

## 5. Sự kiện Toàn cục (Global Events)

- Xảy ra định kỳ mỗi 10 hiệp đấu.
- Hệ thống phát tín hiệu cảnh báo trước 1 hiệp.
- **Một số sự kiện tiêu biểu:**
  - *Giá Xăng Tăng:* Đổi toàn bộ Xe thành Mã.
  - *Mỹ Đánh Iran:* Mưa thiên thạch phá hủy vùng ngẫu nhiên 2x2.
  - *Việc Nhẹ Volt Cao:* Toàn bộ Tốt bị choáng trong 2 lượt.

<!-- 
Lời thoại:
"Cứ 10 hiệp đấu, 1 thiên tai hoặc sự kiện ngẫu nhiên sẽ giáng xuống bàn cờ. Chẳng hạn như 'Giá Xăng Tăng' biến toàn bộ quân Xe thành Mã. Hệ thống này buộc người chơi phải liên tục đổi chiến thuật để sinh tồn."
-->

---

## 6. Sơ đồ tổ chức mã nguồn (Packages)

Mã nguồn được phân tách theo **Nguyên lý Đơn trách nhiệm (SRP)**:

- `game`: Vòng lặp trò chơi, trạng thái.
- `pieces`: Logic di chuyển của các quân.
- `fusion`: Đối chiếu và thực thi Dung hợp.
- `abilities`: Xử lý Kỹ năng.
- `events`: Kích hoạt Sự kiện.
- `ui`: Giao diện (View) & Tương tác.

<!-- 
Lời thoại:
"Về mặt kỹ thuật, dự án có 65 file mã nguồn. Nhóm không nhét mọi thứ vào 1 file, mà áp dụng kiến trúc Module. Nhờ chia thành 6 gói độc lập, 2 thành viên có thể code song song mà không sợ bị xung đột tính năng."
-->

---

## 7. Kiến trúc phần mềm (SOLID)

**Nguyên lý Đóng/Mở (OCP) với Registry Pattern:**
- Để thêm tính năng (Kỹ năng, Sự kiện), chỉ cần tạo File mới và gắn nhãn (Decorator).
- *Lợi ích:* Hệ thống cốt lõi không bị sửa đổi, an toàn tuyệt đối.

**Nguyên lý Đơn trách nhiệm (SRP) với Pipeline Pattern:**
- Xử lý các tác vụ phức tạp (kiểm tra dung hợp, trừ AP, đếm sự kiện) theo dây chuyền (Pipeline).
- *Lợi ích:* Tránh tạo ra lớp xử lý quá cồng kềnh (God Object).

<!-- 
Lời thoại:
"Điển hình cho OCP là Registry Pattern. Bọn em tạo Decorator để đăng ký Sự kiện mới mà không cần chạm vào lõi Game. Còn với SRP, bọn em dùng mô hình Pipeline: nước đi xong sẽ đi qua từng màng lọc tự động, giúp code dễ bảo trì vô cùng."
-->

---

## 8. Khó khăn & Giải pháp kỹ thuật

1. **Lớp xử lý quá lớn (God Object):** 
   👉 *Giải quyết:* Cải tiến bằng kiến trúc Module và Pipeline.
2. **Xung đột trạng thái (Logic Race):** Kỹ năng & Sự kiện "giẫm chân" lên nhau. 
   👉 *Giải quyết:* Tách bạch vòng đời, quản lý ở các luồng xử lý riêng biệt.
3. **Lỗi dữ liệu khi kiểm tra chiếu bí (Rollback):** Mô phỏng nước đi gây sai lệch số lượng khiên. 
   👉 *Giải quyết:* Thiết kế hệ thống **Snapshot** để sao lưu chính xác từng thuộc tính nhỏ nhất trước khi chạy thử.

<!-- 
Lời thoại:
"Một trong những lỗi kinh khủng nhất nhóm gặp phải là khi mô phỏng nước đi để kiểm tra Chiếu Bí, nó làm hỏng số khiên hoặc hiệu ứng độc của các quân cờ khác. Nhóm đã giải quyết triệt để bằng hệ thống Snapshot, sao lưu và khôi phục (Rollback) dữ liệu an toàn tuyệt đối."
-->

---

## 9. Tổng kết & Tương lai

- **Thành quả:** Trò chơi vận hành ổn định, được bảo vệ bởi **182 Unit Tests**. 
- **Hướng phát triển tương lai:**
  - Tích hợp Trí tuệ nhân tạo (AI - Minimax).
  - Đánh qua mạng nội bộ (Online Multiplayer bằng Socket).
  - Nâng cấp Đồ họa / Hiệu ứng động (Animations).

<!-- 
Lời thoại:
"Dự án đã giúp bọn em hiểu sâu về sức mạnh của OOP và Design Pattern. Mọi thứ hiện đang được bảo vệ bởi hơn 180 Unit Test nên cực kỳ khó lỗi. Nếu có thêm thời gian, nhóm sẽ tích hợp AI Minimax để chơi đơn và tính năng Đánh qua mạng."
-->

---

# Cảm ơn Thầy và các bạn đã lắng nghe!

*Q & A - Chuyển sang phần Demo*

<!-- 
Lời thoại:
"Và sau đây, nhóm xin phép được chạy trực tiếp Demo sản phẩm để thầy và các bạn cùng trải nghiệm thử một vài tính năng. Xin cảm ơn!"
-->
