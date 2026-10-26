# BÁO CÁO KIỂM TOÁN AN NINH API (SECURITY AUDIT REPORT)
**Dự án**: Social Network Service API  
**Môn học**: Kiến trúc Hướng Dịch vụ (INT3505E) - Buổi 06: Authentication & Authorization  
**Mục tiêu rà soát**: `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`  
**Tiêu chuẩn đối chiếu**: OWASP API Security Top 10 (2023), RFC 6749 (OAuth 2.0), RFC 7519 (JWT), NIST SP 800-63B.

---

## 1. TỔNG QUAN RỦI RO & BỀ MẶT TẤN CÔNG (EXECUTIVE SUMMARY)

Trong các hệ thống phân tán và ứng dụng mạng xã hội có lưu lượng cao (High-throughput Social Network Systems), xác thực (Authentication - AuthN) và phân quyền (Authorization - AuthZ) đóng vai trò phòng tuyến đầu tiên. Sự nhầm lẫn giữa định danh (Bạn là ai?) và quyền hạn (Bạn được làm gì?) hoặc thiết kế API thiếu chặt chẽ sẽ mở ra những bề mặt tấn công nghiêm trọng, dẫn đến rò rỉ dữ liệu cá nhân (PII), leo thang đặc quyền (Privilege Escalation), và vi phạm kiểm soát truy cập đối tượng.

Dưới đây là 5 điểm rò rỉ và nguy cơ bảo mật trọng yếu được phát hiện trên 3 endpoint của hệ thống, kèm theo phân tích cơ chế tấn công, tác động thực tế và giải pháp khắc phục triệt để.

---

## 2. DANH MỤC 5 ĐIỂM NGUY CƠ BẢO MẬT TRỌNG YẾU

### Điểm 1: Broken Object Level Authorization (BOLA / IDOR) trên `GET /posts/{id}`
- **Phân loại**: OWASP API1:2023 - Broken Object Level Authorization (Slide 24, 26, 29).
- **Mức độ nghiêm trọng**: **CRITICAL** (CVSS 8.6).
- **Cơ chế rò rỉ**:
  - Endpoint `GET /posts/{id}` nhận tham số định danh bài viết từ đường dẫn (`path`). Nếu middleware chỉ dừng lại ở bước xác thực token hợp lệ (AuthN) và kiểm tra scope chung chung (`posts:read` - AuthZ cấp vĩ mô) mà **không kiểm tra quyền sở hữu đối tượng** (Ownership / Contextual Policy), lỗ hổng BOLA xuất hiện.
  - Kẻ tấn công là một người dùng bình thường (User B) sở hữu Access Token hợp lệ có scope `posts:read`. Bằng cách thay đổi tuần tự hoặc vét cạn tham số ID (`GET /posts/1`, `GET /posts/2`, `GET /posts/3`...), User B có thể đọc được toàn bộ bài viết ở chế độ riêng tư (`is_private: true`), nhật ký mật hoặc tài liệu nội bộ của User A.
- **Tác động**: Rò rỉ toàn bộ dữ liệu bài viết riêng tư của người dùng trên toàn mạng xã hội; vi phạm nghiêm trọng tính bảo mật (Confidentiality).
- **Giải pháp khắc phục (Remediation)**:
  - Triển khai mô hình 3 lớp kiểm tra theo thứ tự (Slide 24):
    1. **AuthN**: Token còn hạn, chữ ký hợp lệ, chưa bị revoke.
    2. **AuthZ Scope**: Token phải chứa scope `posts:read`.
    3. **Ownership / Policy**: Kiểm tra thuộc tính `post.is_private`. Nếu là bài viết riêng tư, chỉ cho phép truy cập khi `post.author_id == current_user.id` hoặc `current_user.role == "admin"`.
  - Đối với các tài nguyên riêng tư mà người dùng không có quyền truy cập, cân nhắc trả về `404 Not Found` thay vì `403 Forbidden` để ngăn chặn kẻ tấn công dò quét sự tồn tại của ID (ID Enumeration).

---

### Điểm 2: User Enumeration & Side-Channel Timing Attack trên `POST /auth/login`
- **Phân loại**: OWASP API2:2023 - Broken Authentication (Slide 7, 27, 28, 29).
- **Mức độ nghiêm trọng**: **HIGH** (CVSS 7.5).
- **Cơ chế rò rỉ**:
  - **Rò rỉ qua thông báo lỗi**: Nếu backend trả về thông báo chi tiết phân biệt giữa *"Email không tồn tại"* (User not found) và *"Mật khẩu không chính xác"* (Wrong password), kẻ tấn công sẽ tự động hóa gửi danh sách email để lọc ra toàn bộ tài khoản có thật trong hệ thống.
  - **Rò rỉ qua độ trễ thời gian (Timing Side-Channel)**: Các hàm băm mật khẩu bảo mật (như Argon2id với `m=65536, t=3, p=4` hoặc bcrypt với cost 12 per Slide 27-28) cố tình tiêu tốn nhiều CPU/Memory (khoảng vài chục đến hàng trăm mili-giây). Nếu hệ thống kiểm tra `if email not in db: return 401` ngay lập tức (chỉ mất ~0.1ms), sự chênh lệch độ trễ phản hồi giữa tài khoản tồn tại và tài khoản không tồn tại sẽ lộ rõ qua phân tích thống kê độ trễ gói tin (RTT), cho phép kẻ tấn công lập danh sách tài khoản ngay cả khi thông điệp lỗi trả về giống nhau.
- **Tác động**: Tạo tiền đề cho các cuộc tấn công Spear-Phishing nhắm mục tiêu, rà quét mật khẩu (Credential Stuffing), và Dictionary Attack.
- **Giải pháp khắc phục (Remediation)**:
  - Chuẩn hóa thông điệp lỗi: Luôn trả về thông báo chung duy nhất: `{"code": 401, "message": "Invalid email or password"}` (Slide 29).
  - Khử độ trễ chênh lệch: Khi email không tồn tại trong cơ sở dữ liệu, backend vẫn phải thực hiện một phép tính dummy hash với chi phí tương đương trước khi trả về `401`.
  - Sử dụng hàm so sánh an toàn `hmac.compare_digest` để chống side-channel trên chuỗi hash.
  - Thiết lập cơ chế **Rate Limiting** (giới hạn tần suất gọi API, ví dụ tối đa 5 lần thử/phút cho mỗi IP hoặc mỗi account) để chống brute-force và credential stuffing.

---

### Điểm 3: Rò rỉ Dữ liệu Nhạy cảm (PII Exposure) trong JWT Claims
- **Phân loại**: OWASP API3:2023 - Information Disclosure / JWT Design Pitfall (Slide 14, 18, 22).
- **Mức độ nghiêm trọng**: **MEDIUM - HIGH** (CVSS 6.5).
- **Cơ chế rò rỉ**:
  - JSON Web Token dạng chuẩn JWS Compact (`header.payload.signature`) chỉ áp dụng thuật toán mã hóa chữ ký (ví dụ HMAC-SHA256) để đảm bảo **tính toàn vẹn** (Integrity), **hoàn toàn không che giấu hay mã hóa bí mật nội dung** (Confidentiality per Slide 14 & 22). Phần Payload thực chất chỉ là chuỗi JSON được encode bằng `base64url`.
  - Các sai lầm phổ biến khi lập trình backend là đưa thông tin định danh cá nhân (Personally Identifiable Information - PII) như số điện thoại, CCCD, địa chỉ email, chuỗi hash mật khẩu hoặc cờ đặc quyền nhạy cảm vào `additional_claims`.
  - Bất kỳ thực thể nào chạm vào token (Reverse Proxy logs, API Gateway, trình duyệt qua devtools/extensions, hoặc script frontend bị tấn công XSS) đều có thể giải mã payload tức thì qua `base64url_decode`.
- **Tác động**: Xâm phạm quyền riêng tư nghiêm trọng của người dùng; lộ dữ liệu định danh theo quy định bảo vệ dữ liệu (GDPR / Nghị định 13/2023/NĐ-CP).
- **Giải pháp khắc phục (Remediation)**:
  - Áp dụng nguyên tắc tối thiểu dữ liệu (Data Minimization): Payload JWT chỉ lưu các claims tiêu chuẩn cần thiết (`sub` là user UUID, `iss`, `aud`, `exp`, `jti`, và mảng `scopes` rút gọn per Slide 14).
  - Tuyệt đối không lưu mật khẩu, session secrets hoặc thông tin nhạy cảm trong claims.
  - Nếu bắt buộc phải truyền dữ liệu bảo mật trong token, phải áp dụng định dạng JWE (JSON Web Encryption) có 5 phần thay cho JWS 3 phần.

---

### Điểm 4: Algorithm Confusion (`HS256` vs `RS256`) và Lỗ hổng Chấp nhận `alg=none`
- **Phân loại**: OWASP API2:2023 - Broken Authentication / Cryptographic Misconfiguration (Slide 18 - Lỗi 01 & 02).
- **Mức độ nghiêm trọng**: **CRITICAL** (CVSS 9.1).
- **Cơ chế rò rỉ / Khai thác**:
  - **Lỗi 01 (alg=none)**: Nếu middleware xác thực token tin tưởng hoàn toàn vào trường `alg` được chỉ định trong header của JWT mà không có whitelist, kẻ tấn công có thể sửa đổi payload thành tài khoản quản trị (`"role": "admin", "scopes": ["posts:read", "posts:write", "admin"]`), đặt `"alg": "none"` và bỏ trống phần chữ ký. Server chấp nhận token không có chữ ký, dẫn đến bypass xác thực 100%.
  - **Lỗi 02 (Algorithm Confusion)**: Khi server cấu hình xác thực bất đối xứng bằng RS256 (Public Key để verify, Private Key để ký). Kẻ tấn công lấy được RSA Public Key công khai của server, chỉnh sửa header token sang `"alg": "HS256"`, và dùng chính RSA Public Key làm secret key để ký đối xứng HMAC. Nếu server dùng chung hàm verify lỏng lẻo và chuyển đổi key sai ngữ cảnh, server sẽ dùng Public Key đó để verify HS256 và chấp nhận token giả mạo là hợp lệ.
- **Tác động**: Toàn quyền leo thang đặc quyền (Privilege Escalation); kẻ tấn công có thể mạo danh bất kỳ ai, chiếm đoạt toàn bộ dữ liệu bài viết và hệ thống API.
- **Giải pháp khắc phục (Remediation)**:
  - Cấu hình tường minh và duy nhất một thuật toán được phép trong cấu hình ứng dụng (`JWT_ALGORITHM="HS256"`).
  - Không bao giờ cho phép thư viện tự động chuyển đổi giữa đối xứng và bất đối xứng dựa trên header token của người dùng.
  - Nghiêm cấm hoàn toàn thuật toán `none`. Sử dụng secret key có độ dài tối thiểu 256 bits ngẫu nhiên từ CSPRNG.

---

### Điểm 5: Token Replay & Thất bại trong Thu hồi Phiên (Inadequate Token Revocation & Stolen Refresh Token)
- **Phân loại**: OWASP API2:2023 - Broken Authentication / Token Lifecycle Mismanagement (Slide 13, 15, 17, 18, 20).
- **Mức độ nghiêm trọng**: **HIGH** (CVSS 7.8).
- **Cơ chế rò rỉ / Khai thác**:
  - JWT mang tính phi trạng thái (Stateless), server không tra cứu DB để verify từng request mà chỉ kiểm tra chữ ký (Slide 13). Nhược điểm chí mạng là **không thể thu hồi token tức thì** một khi đã phát hành.
  - Refresh Token được cấu hình thời gian sống rất dài (ví dụ 30 ngày per Slide 15). Nếu Refresh Token bị lưu trữ sai cách (ví dụ lưu trong `localStorage` bị tấn công XSS đánh cắp, hoặc bị rò rỉ qua log hệ thống), kẻ tấn công sở hữu token này có thể liên tục gọi `POST /auth/refresh` để nhận Access Token mới trong suốt 30 ngày.
  - Ngay cả khi người dùng thực hiện "Đổi mật khẩu" hoặc "Đăng xuất" (Logout), nếu backend không có cơ chế lưu trữ danh sách thu hồi (Revocation Blocklist) và không áp dụng Refresh Token Rotation (RTR), phiên truy cập của kẻ tấn công vẫn tiếp tục duy trì mà không thể bị ngắt.
- **Tác động**: Chiếm quyền điều khiển tài khoản kéo dài (Persistent Account Hijacking); mất khả năng cô lập thiệt hại khi xảy ra rò rỉ khóa/token.
- **Giải pháp khắc phục (Remediation)**:
  - **Revocation Blocklist**: Sử dụng Redis để lưu trữ `jti` (JWT ID độc nhất per Slide 14, 15) của các token đã bị thu hồi hoặc đăng xuất. Mỗi request đến `/auth/refresh` bắt buộc kiểm tra xem `jti` có nằm trong blocklist hay không.
  - **Refresh Token Rotation (RTR)**: Mỗi khi `POST /auth/refresh` được gọi thành công, Refresh Token hiện tại lập tức bị vô hiệu hóa và một cặp (Access Token, Refresh Token) hoàn toàn mới được phát hành.
  - **Automatic Replay Detection**: Nếu một Refresh Token đã từng bị thay thế (cũ) được gửi lên lần thứ hai, hệ thống phát hiện đây là dấu hiệu của hành vi đánh cắp và ngay lập tức thu hồi toàn bộ cây token của phiên đăng nhập đó.
  - Phía Client: Tuyệt đối không lưu token nhạy cảm trong `localStorage` hay `sessionStorage`. Đối với ứng dụng Web, sử dụng Cookie mang cờ `HttpOnly`, `Secure`, và `SameSite=Strict`.

---

## 3. TỔNG HỢP MA TRẬN PHÒNG VỆ VÀ THỰC THI (DEFENSE MATRIX)

| Endpoint | Lỗ hổng tiềm ẩn | Cơ chế phòng thủ đã triển khai trong mã nguồn / OpenAPI Spec |
| :--- | :--- | :--- |
| `POST /auth/login` | Credential Stuffing, Timing Attack, Brute-force | So khớp hash mật khẩu qua `hmac.compare_digest` (constant time); chuẩn hóa thông điệp lỗi 401; khai báo mã 429 Rate Limit; chỉ phát hành Access Token TTL ngắn (15m). |
| `POST /auth/refresh` | Token Replay, Stolen Refresh Token, Type Confusion | Kiểm tra nghiêm ngặt `jwt_required(refresh=True)` (từ chối Access Token ở endpoint refresh); kiểm tra scope `auth:refresh`; tích hợp hook `@jwt.token_in_blocklist_loader` để kiểm tra `jti`. |
| `GET /posts/{id}` | BOLA (IDOR), Rò rỉ bài viết riêng tư, ID Harvesting | Thực thi xác thực Bearer -> kiểm tra scope `posts:read` -> kiểm tra ownership (`caller_id == post.author_id` đối với `is_private=True`); trả 403 Forbidden chặn đứng BOLA. |
| Toàn hệ thống | JWT Alg Confusion, PII Leakage | Khóa chặt thuật toán `HS256` với khóa bí mật $\ge 256$ bits; payload chỉ mang `sub`, `scopes`, `role`; tuần tự hóa dữ liệu ra ngoài bằng Marshmallow Schemas (chặn Mass Assignment). |
