# BÁO CÁO ĐỒ ÁN MÔN HỌC

**Môn học:** Lập trình hướng đối tượng (Object-Oriented Programming - OOP)
**Học kỳ 2 – Năm học 2025–2026**

**Tên đề tài:** Game Cờ Vua Mở Rộng – OnlyChess
**Kho lưu trữ (Repository):** https://github.com/Park-Hip/OnlyChess

**Thành viên thực hiện:**
1. Nguyễn Văn Dũng – MSSV: 25520375
2. Phạm Bách Hiệp – MSSV: 25520538

---

## Lời mở đầu

Đồ án "OnlyChess" được xây dựng với mục tiêu áp dụng kiến thức OOP vào thực tiễn, thông qua việc phát triển một trò chơi chiến thuật theo lượt có cấu trúc linh hoạt. Báo cáo này trình bày ngắn gọn về ý tưởng cốt lõi, các tính năng chính, kiến trúc hệ thống và cách giải quyết những thách thức kỹ thuật trong quá trình phát triển.

---

## Danh mục hình
- Hình 2.1. Giao diện Màn hình chính (Main Menu)
- Hình 2.2. Giao diện lối chơi (Gameplay) và Thanh thông báo
- Hình 2.3. Giao diện Trình đơn Kỹ năng (Ability Menu)
- Hình 2.4. Giao diện Màn hình kết thúc (Game Over)
- Hình 3.1. Sơ đồ Gói (Package Diagram) của toàn bộ hệ thống
- Hình 3.2. Sơ đồ Lớp (Class Diagram) của hệ thống Dung hợp

## Danh mục bảng
- Bảng 2.1. Công thức Dung hợp (Fusion) và mô tả đặc điểm
- Bảng 2.2. Danh sách Kỹ năng (Abilities) và chi phí Điểm hành động (Action Points - AP)
- Bảng 2.3. Danh sách Sự kiện toàn cục (Global Events)
- Bảng 3.1. Sơ đồ tổ chức các Gói (Package) trong mã nguồn
- Bảng 3.2. Các Mẫu thiết kế (Design Pattern) cốt lõi được áp dụng

---

## Chương 1. Giới thiệu đồ án

### 1.1. Thông tin tổng quan
- **Tên ứng dụng:** OnlyChess (Chess Fusion).
- **Thể loại:** Trò chơi chiến thuật theo lượt (Turn-based Strategy Board Game).
- **Ngôn ngữ và Khung làm việc:** Python 3.12 và Pygame 2.6.
- **Chế độ chơi:** Local PvP (hai người thi đấu trên cùng thiết bị).

### 1.2. Đặt vấn đề và Ý tưởng cốt lõi
Cờ vua truyền thống có tính chiến thuật cao nhưng nhịp độ tương đối tĩnh. Để tăng tính biến động chiến thuật, OnlyChess bổ sung ba cơ chế cốt lõi:
1. **Dung hợp (Fusion):** Quân cờ bắt quân đối phương theo công thức nhất định sẽ kết hợp thành một quân lai có sức mạnh mới.
2. **Kỹ năng và Điểm hành động (Action Points – AP):** Tích lũy AP để kích hoạt kỹ năng đặc biệt của từng loại quân.
3. **Sự kiện toàn cục (Global Events):** Các sự kiện ngẫu nhiên định kỳ làm thay đổi trạng thái bàn cờ, buộc người chơi phải liên tục đổi chiến thuật.

### 1.3. Mục tiêu kỹ thuật
Mục tiêu quan trọng nhất là xây dựng hệ thống có thể dễ dàng mở rộng. Hệ thống cần cho phép thêm kỹ năng hoặc sự kiện mới mà không yêu cầu sửa đổi mã nguồn của thành phần cốt lõi. Yếu tố này đóng vai trò quyết định trong việc bảo trì và nâng cấp phần mềm về sau.

---

## Chương 2. Các chức năng chính

### 2.1. Cốt lõi cờ vua (Standard Chess Core)
Hệ thống mô phỏng đầy đủ luật cờ vua tiêu chuẩn. Bàn cờ 8x8 hỗ trợ xác định nước đi hợp lệ cho sáu loại quân. Hệ thống bao gồm đầy đủ cơ chế Nhập thành, Bắt tốt qua đường, Phong cấp và kiểm tra Chiếu bí (Checkmate).

### 2.2. Cơ chế Dung hợp (Fusion)
Dung hợp kích hoạt tự động khi một quân bắt quân địch và tạo thành cặp hợp lệ. Quân mới sinh ra tồn tại vĩnh viễn và không thể dung hợp lần hai. Bảng 2.1 mô tả các công thức đã cài đặt.

**Bảng 2.1. Công thức Dung hợp (Fusion) và mô tả đặc điểm**

| Quân tấn công | Quân bị bắt | Quân lai (Kết quả) | Mô tả đặc điểm di chuyển |
| :--- | :--- | :--- | :--- |
| Mã (Knight) | Tượng (Bishop) | **Archbishop** | Kết hợp nước đi của Mã và Tượng. |
| Xe (Rook) | Mã (Knight) | **Chancellor** | Kết hợp nước đi của Xe và Mã. |
| Xe (Rook) | Tượng (Bishop) | **Warden** | Đi thẳng không giới hạn, đi chéo tối đa ba ô. |
| Tượng (Bishop) | Xe (Rook) | **Inquisitor** | Đi chéo không giới hạn, đi thẳng tối đa ba ô. |

### 2.3. Hệ thống Kỹ năng và Điểm hành động (AP)
Mỗi bên khởi đầu với 0 AP, tăng một điểm sau mỗi hai lượt (tối đa 5 AP). Việc dùng kỹ năng sẽ tiêu tốn toàn bộ lượt đi. Người chơi nhấp chuột phải vào quân cờ để mở trình đơn Kỹ năng.

**Bảng 2.2. Danh sách Kỹ năng (Abilities) và chi phí AP**

| Quân cờ sở hữu | Tên Kỹ năng | AP | Mô tả tác dụng |
| :--- | :--- | :--- | :--- |
| Mã (Knight) | Swap | 2 | Hoán đổi vị trí với một quân đồng minh. |
| Tượng (Bishop) | Snipe | 3 | Tiêu diệt quân địch trong đường chéo mà không cần di chuyển. |
| Xe (Rook) | Shield | 3 | Cấp trạng thái bảo vệ chặn một lần tiêu diệt cho bản thân và đồng minh liền kề. |
| Tốt (Pawn) | Sprint | 1 | Di chuyển thẳng tối đa ba ô mà không cần là nước đi đầu tiên. |

### 2.4. Hệ thống Sự kiện toàn cục (Global Events)
Hệ thống phát tín hiệu cảnh báo trước một lượt. Sự kiện thực thi mỗi mười hiệp đấu để tạo ra đột biến trên bàn cờ.

**Bảng 2.3. Danh sách Sự kiện toàn cục (Global Events)**

| STT | Tên hiển thị | Tác động |
| :--- | :--- | :--- |
| 1 | Umamusume | Đổi toàn bộ quân (trừ Vua) thành Mã. |
| 2 | Giá Xăng Tăng | Đổi Xe, Chancellor và Warden thành Mã. |
| 3 | Mỹ Đánh Iran | Hủy diệt khu vực 2x2 ngẫu nhiên. Khiên có thể chặn sát thương này. |
| 4 | Tài Xỉu | Ngẫu nhiên loại bỏ một quân của phe Trắng hoặc Đen. |
| 5 | Comeout | Lập tức phong cấp một Tốt ngẫu nhiên thành Hậu. |
| 6 | Việc Nhẹ Volt Cao | Tốt bị choáng, không thể di chuyển trong hai lượt. |
| 7 | Người Chồng Bất Lực | Cả hai Vua không thể di chuyển một lượt. |
| 8 | Khô Gà Trộn Bã Mía | Một đơn vị cơ động ngẫu nhiên bị nhiễm độc, di chuyển tối đa một ô/lượt trong ba lượt. |
| 9 | Lòng Tôi Tan Nát... | Loại bỏ toàn bộ Hậu trên bàn cờ. |
| 10 | Mất Quyền Công Dân | Tiêu diệt một Tốt Đen, đổi quyền điều khiển một Tốt Trắng thành Tốt Đen. |

### 2.5. Giao diện người dùng (UI)
Giao diện Pygame gồm màn hình chính, màn hình kết thúc, thanh thông báo lịch sử theo chuẩn FAN (Fusion Algebraic Notation) và bảng hướng dẫn. Giao diện thiết kế tối giản nhằm giúp người chơi tập trung vào bàn cờ.

---

## Chương 3. Thiết kế kiến trúc phần mềm

Chương này tập trung phân tích kiến trúc phần mềm và cách hệ thống áp dụng các nguyên lý thiết kế nhằm đáp ứng yêu cầu mở rộng lâu dài.

### 3.1. Sơ đồ tổ chức mã nguồn
Mã nguồn (65 tệp tin Python) được chia thành các Gói (Package) độc lập. Mỗi gói giải quyết một bài toán duy nhất. 

**Bảng 3.1. Sơ đồ tổ chức các Gói (Package) trong mã nguồn**

| Gói (Package) | Trách nhiệm chính |
| :--- | :--- |
| `game` | Quản lý vòng lặp trò chơi, trạng thái và chuỗi xử lý sau nước đi. |
| `pieces` | Cung cấp logic di chuyển cho các quân cờ tiêu chuẩn và quân lai. |
| `fusion` | Xử lý việc đối chiếu công thức và thay thế quân khi Dung hợp. |
| `abilities` | Chứa danh bạ và logic độc lập cho từng Kỹ năng. |
| `events` | Quản lý bộ đếm lượt và logic thực thi Sự kiện. |
| `ui` | Xử lý đồ họa, tiếp nhận sự kiện nhấp chuột và âm thanh. |

### 3.2. Mô hình kiến trúc MVC
Dự án sử dụng Model-View-Controller để tách logic trò chơi khỏi giao diện hiển thị. Tầng Model quản lý trạng thái, vòng lặp và tự động đếm lượt sự kiện. Tầng View/Controller chịu trách nhiệm hiển thị và chuyển thao tác người dùng thành các lệnh gọi Kỹ năng tương ứng gửi xuống Model. Việc chia tách này giúp kiểm thử dễ dàng hơn.

### 3.3. Các Mẫu thiết kế (Design Pattern) và SOLID
Dự án áp dụng một số nguyên lý SOLID, tiêu biểu là SRP và OCP để đảm bảo mã nguồn linh hoạt.

**Bảng 3.2. Mẫu thiết kế cốt lõi được áp dụng**

| Mẫu thiết kế | Giải quyết vấn đề gì? | Lợi ích |
| :--- | :--- | :--- |
| **Lớp trừu tượng (Base Class)** | Hệ thống cần gọi cùng một hành động cho nhiều loại Kỹ năng/Sự kiện khác nhau. | Gọi phương thức thống nhất mà không phụ thuộc vào loại đối tượng cụ thể. |
| **Registry Pattern** | Làm sao thêm chức năng mới mà không phải vào lõi sửa code liên tục? | Thêm tính năng dễ dàng qua Decorator. Tránh sửa đổi hệ thống lõi. |
| **Pipeline Pattern** | Cần kiểm tra nhiều quy tắc tuần tự sau khi di chuyển một quân cờ. | Dễ dàng chèn hoặc bỏ các bước xử lý độc lập khỏi vòng lặp. |

#### Nguyên lý Đóng/Mở (OCP) với Registry Pattern
OCP yêu cầu thành phần phần mềm cần "mở cho việc mở rộng, nhưng đóng đối với việc sửa đổi". Bằng cách dùng Registry Pattern, trung tâm xử lý chỉ lấy danh sách các lớp đã được đăng ký. Để thêm sự kiện, lập trình viên chỉ cần tạo lớp mới và gắn nhãn (Decorator). Mã nguồn hiện tại không bị tác động, giảm nguy cơ phát sinh lỗi liên đới.

#### Nguyên lý Đơn trách nhiệm (SRP) với Pipeline
SRP yêu cầu mỗi lớp chỉ có một lý do duy nhất để thay đổi. Vòng lặp trò chơi không tự quản lý việc tăng AP hay Dung hợp. Thay vào đó, hệ thống gọi chuỗi xử lý sau nước đi. Các lớp nhỏ độc lập trong chuỗi này lần lượt thực thi nhiệm vụ riêng biệt. Cơ chế này loại bỏ các lớp xử lý quá cồng kềnh.

---

## Chương 4. Khó khăn và giải pháp kỹ thuật

### 4.1. Lớp xử lý quá lớn (God Object)
**Khó khăn:** Ban đầu, toàn bộ quy trình kiểm tra di chuyển, giao diện và sự kiện nằm chung trong một lớp duy nhất. Sự phụ thuộc chéo khiến hệ thống khó bảo trì.
**Giải pháp:** Chia dự án thành kiến trúc dựa trên Mô-đun. Logic trò chơi được tách riêng vào sáu gói độc lập.
**Kết quả:** Cải thiện đáng kể khả năng bảo trì. Việc bổ sung tính năng không làm ảnh hưởng đến cấu trúc tổng thể.

### 4.2. Xung đột trạng thái giữa Kỹ năng và Sự kiện
**Khó khăn:** Kỹ năng và Sự kiện thường cùng tác động lên một quân cờ (phá hủy hoặc đổi loại quân), dễ gây ra xung đột trạng thái (logic race).
**Giải pháp:** Tách rõ vòng đời của hai hệ thống. Sự kiện tự động chạy ở tầng Model, còn Kỹ năng chỉ chạy thông qua lệnh yêu cầu từ Controller.
**Kết quả:** Hai hệ thống không bao giờ tương tác chéo, giảm thiểu rủi ro xung đột dữ liệu.

### 4.3. Lỗi dữ liệu khi kiểm tra chiếu bí (Rollback)
**Khó khăn:** Việc mô phỏng thử nước đi để kiểm tra "chiếu" dễ gây sai lệch các thuộc tính phức tạp như số điểm khiên hay trạng thái nhiễm độc.
**Giải pháp:** Lưu sao lưu tạm thời (snapshot) toàn bộ thuộc tính của quân cờ trước khi mô phỏng. Khi nước đi không an toàn, hàm khôi phục (rollback) sẽ ghi đè lại dữ liệu.
**Kết quả:** Đảm bảo tính nhất quán của trạng thái bàn cờ sau mỗi lần kiểm tra.

---

## Chương 5. Kết luận

### 5.1. Kết quả đạt được
Đồ án đã xây dựng thành công bộ quy tắc mở rộng và hệ thống quân lai như đề xuất. Kiến trúc linh hoạt giúp dự án có khả năng duy trì lâu dài. Hệ thống bao gồm 182 Kiểm thử đơn vị (Unit Test) đã vượt qua toàn bộ khâu kiểm thử, đảm bảo sự ổn định và giảm nguy cơ lỗi.

### 5.2. Kiến thức tích lũy
Quá trình thực hiện đã củng cố vai trò của các nguyên lý thiết kế SRP và OCP trong thực tiễn. Việc chia cấu trúc rõ ràng ngay từ đầu giúp tối ưu hóa hiệu suất làm việc nhóm. Đồng thời, việc ứng dụng Unit Test và Git là yếu tố quan trọng giúp nhóm quản lý tốt rủi ro.

### 5.3. Hạn chế và Hướng phát triển
Trò chơi hiện mới hỗ trợ thi đấu nội bộ hai người, chưa tích hợp Trí tuệ nhân tạo (AI) và thiếu các hiệu ứng hình ảnh (Animation) sinh động. 

Trong tương lai, nhóm dự định tích hợp mô-đun AI sử dụng thuật toán Minimax (kết hợp Alpha-Beta Pruning) cho chế độ chơi đơn (PvE). Hơn nữa, việc bổ sung giao thức mạng Socket sẽ giúp hỗ trợ tính năng thi đấu trực tuyến. Kết cấu linh hoạt hiện tại tạo tiền đề cho việc mở rộng nhanh chóng thư viện Kỹ năng và Sự kiện.

---

## Tài liệu tham khảo

1. *Python 3.12 Documentation*. Truy cập từ: https://docs.python.org/3/
2. *Pygame Documentation*. Truy cập từ: https://www.pygame.org/docs/
3. Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
4. Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.
5. Shvets, A. (2021). *Dive Into Design Patterns*. Refactoring Guru.
6. *PEP 8 – Style Guide for Python Code*. Truy cập từ: https://peps.python.org/pep-0008/
7. *Chess Programming Wiki*. Truy cập từ: https://www.chessprogramming.org/
