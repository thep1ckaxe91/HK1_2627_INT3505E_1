# Lab 4 — Báo cáo phân tích hiệu năng

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 18 | 0.00% | 4.72 |
| B | 50 | 5 | 60s | 17 | 0.00% | 23.46 |
| C | 200 | 50 | 30s | 52 | 0.31% | 98.22 |

---

### 1. Kịch bản nào p95 cao nhất? Vì sao?
- **Kịch bản C (200 users)** cao nhất: **52 ms** (so với 18 ms ở A và 17 ms ở B).
- **Lý do:** 
  - Concurrency tăng vọt (200 users, spawn 50/s) khiến server bị nghẽn CPU và I/O.
  - Flask chạy dev server đơn luồng/mặc định + SQLite bị lock khi ghi (`POST /books`), request phải xếp hàng (queueing delay) nên p95 tăng vọt theo dạng phi tuyến.

### 2. Endpoint nào fail rate tăng theo user? Nguyên nhân?
- **Endpoint:** `GET /books?year=[year]` (kịch bản C fail 9/682 reqs ~ 1.32%, kịch bản A và B fail 0%).
- **Nguyên nhân:**
  - Nhìn vào code `performance/locustfile.py`: có dòng code giả lập lỗi client `if random.random() < 0.01: response.failure(...)` (bắt buộc fail ngẫu nhiên 1%).
  - Số lượng request càng nhiều (kịch bản C gửi gần 3000 reqs) thì xác suất trúng lỗi 1% này càng lộ rõ ra trên thống kê. Thực tế server vẫn trả về HTTP 200, không phải crash 500.

### 3. Đạt SLO p95 < 300ms không? Đề xuất CI gate
- **SLO:** Cả 3 kịch bản đều đạt chuẩn (cao nhất ở C mới là 52 ms < 300 ms).
- **Đề xuất baseline cho CI gate:**
  - Chạy kịch bản **A hoặc B** trong CI (chạy tầm 30s–60s với 10–50 users).
  - Đặt threshold gate: Fail CI nếu `p95 > 100ms` hoặc `failure_rate > 1%`. Không nên chạy kịch bản C trên máy CI vì tài nguyên container yếu dễ gây false alarm.

### Bonus: Pool size = 5 thì 200 user đồng thời bị gì? Test bằng Locust thế nào?
- **Điều gì xảy ra:** 
  - Chỉ có 5 worker/thread lấy được connection vào DB cùng lúc. 195 user còn lại phải chờ (wait queue). 
  - Response time sẽ tăng vọt (p95, p99 nổ tung), nếu chờ quá `pool_timeout` (mặc định SQLAlchemy là 30s) sẽ bị lỗi `TimeoutError: QueuePool limit of size 5 overflow ...` -> server trả 500 Internal Server Error hàng loạt.
- **Cách kiểm chứng bằng Locust:**
  - Chỉnh code Flask cấu hình SQLAlchemy: `app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 5, 'max_overflow': 0, 'pool_timeout': 3}`.
  - Chạy lại kịch bản C (`locust -u 200 -r 50 ...`).
  - Quan sát tab **Failures** trên Locust: sẽ thấy mã lỗi HTTP 500 tăng đột biến và đồ thị Response Time dựng đứng lên.
