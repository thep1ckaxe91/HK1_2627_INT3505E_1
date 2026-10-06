# DMOJ API Review

Original API docs: https://docs.dmoj.ca/#/site/api

### 1. Tài nguyên là danh từ

- Các endpoint resources đều là danh từ như: contest(s), problem(s), submission(s), participations, user(s), organizations, languages, judges

### 2. kebab-case cho path, snake_case cho query

- Các path không có >1 từ, nên không thể nói DMOJ có sử dụng kebab-case cho path hay không, nhưng các query parameters có tuân thủ snake_case.
- VD endpoints:
  + `/contests` : `is_rated`
  + `/participations`: `contest`, `user`, `is_disqualified`, `virtual_participation_number`

- ...

### 3. Status code đúng nghĩa

- Trong docs không mô tả tất cả status code có thể trả về, nhưng chúng ta biết rằng:
  
  > "...the site itself may return other codes not listed here or identical codes with different error messages..."

- Các status code có docs cụ thể là:
  + `400 Invalid authorization header` - The **header** you provided is invalid. Make sure it matches the following regex: `Authorization: Bearer ([a-zA-Z0-9_-]{48})`
  + `401 Invalid token` - The **token** you provided is invalid. Make sure it matches the one on your *Edit profile* page.
  + `403 Admin inaccessible` - You are trying to access the inaccessible admin portion of the site.
  

### 4. Idempotency (không) rõ ràng

- Doc chỉ có endpoint GET. Không ghi API là read-only, không ghi safe/idempotent.
  > "The DMOJ supports a simple JSON API for accessing most data" (không nói gì về method khác)
- Envelope có `"method": "<HTTP method that was used>"` nhưng doc không đề cập tới hành vi với POST/PUT/DELETE.
- `fetched` kèm timestamp mỗi request làm body luôn khác nhau. Doc không nhắc tới `ETag`/`Cache-Control`, nên không có conditional GET.
- Không có chỗ nào nói retry GET có an toàn không. Kết hợp với rate limit (mục 2) thì retry ngây thơ dễ ăn captcha.
- `Idempotency-Key`: chưa có POST nên chưa cần.

## 5. Error response có cấu trúc

Format hiện tại:
```json
{ "error": { "code": "<HTTP status code>", "message": "<error message>" } }
```

| RFC 7807/9457              | Doc DMOJ                            |
| -------------------------- | ----------------------------------- |
| `type`                     | Không có                            |
| `title`                    | Không có (gộp vào `message`)        |
| `status`                   | `error.code`, kiểu dữ liệu không rõ |
| `detail`                   | `error.message`                     |
| `instance`                 | Không có                            |
| `application/problem+json` | Không nhắc                          |

Cụ thể:
- **Thiếu `type`**: client phải so khớp chuỗi. Bản thân doc cảnh báo:
  > "identical codes with different error messages, so read the error messages carefully"
- **Không nhất quán**: site có thể trả "other codes not listed here", không có schema cho chúng. Không rõ các lỗi auth có đi qua envelope hay không.
- **Rate limit**: chỉ đơn giản "you will be captcha'd", kéo dài 3 ngày. Không có `429` hay `Retry-After`. Client máy không xử lý được captcha.
- **Phân trang**: response có `page_index`/`total_pages` nhưng doc không ghi tham số query chọn trang.
- **Thiếu `WWW-Authenticate`** cho `400`/`401` (RFC 6750).



### 6. Pagination rõ ràng

- **Đạt**
- Với các endpoint trả về danh sách, DMOJ có cấu trúc pagination rõ ràng trong `data`, gồm:
  + `current_object_count`: số object ở trang hiện tại
  + `objects_per_page`: số object tối đa trên một trang
  + `page_index`: chỉ số trang hiện tại, bắt đầu từ 1
  + `total_objects`: tổng số object
  + `total_pages`: tổng số trang
  + `objects`: danh sách dữ liệu của trang hiện tại
- Ví dụ có thể truy cập trang bằng query parameter:
  + `/api/v2/problems?page=2`
DMOJ đáp ứng yêu cầu collection có pagination và có giới hạn số lượng object trên mỗi trang

### 7. Filter/Sort đa dạng

- **Filter đạt / Sort không đạt**
- DMOJ hỗ trợ filtering khá tốt. Docs mô tả hai kiểu chính:
  + **Basic filtering**: lọc theo một giá trị
  + **List filtering**: lọc theo một danh sách giá trị
- Ví dụ:
  + `/api/v2/problems?partial=True`
  + `/api/v2/problems?organization=1&organization=2&type=Implementation`
- Endpoint `/api/v2/problems` hỗ trợ các filter như:
  + `partial`
  + `code`
  + `group`
  + `type`
  + `organization`
  + `search`
- Endpoint `/api/v2/submissions` hỗ trợ các filter như:
  + `user`
  + `problem`
  + `id`
  + `language`
  + `result`
- Docs không cung cấp query parameter cho phép client tự chọn cách sort
- Nhiều collection được sắp xếp cố định ở phía server, ví dụ theo `id`, thay vì cho client chọn nhiều field để sort
- Docs cũng không mô tả sparse fieldsets như:
  + `?fields=code,name,points`
  để chỉ lấy một số field cần thiết

**Đề xuất cải thiện:**
  + Thêm query parameter `sort` để hỗ trợ sắp xếp theo nhiều field
  + Quy ước dùng dấu `-` để biểu diễn thứ tự giảm dần
  + Ví dụ:
    `/api/v2/problems?sort=-points,name`
    nghĩa là sort theo `points` giảm dần, sau đó theo `name` tăng dần
  + Chỉ cho phép sort trên một danh sách field hợp lệ để tránh query không mong muốn
  + Có thể bổ sung query parameter `fields` để hỗ trợ sparse fieldsets
  + Ví dụ:
    `/api/v2/problems?fields=code,name,points`
    chỉ trả về các field `code`, `name`, `points`.


### 8. Authentication & security

- **Token ở header**: Đạt.
  + Token được gửi qua header theo dạng: `Authorization: Bearer <API token>`
  + Token gồm 48 ký tự, khớp regex `[a-zA-Z0-9_-]{48}`, được tạo ở trang *Edit profile* của user.
  + Header sai định dạng → `400 Invalid authorization header`; token không đúng → `401 Invalid token`.
- **Không lộ qua URL**: Đạt.
  + Query parameters chỉ dùng để lọc/phân trang, không có parameter nào nhận token.
  + VD: `/api/v2/participations?contest=...&user=...&is_disqualified=...`
- **Rate limit rõ ràng**: Đạt một phần.
  + Docs có nêu giới hạn cụ thể: 90 requests/phút.
  + Vượt giới hạn thì bị yêu cầu captcha (captcha hết hạn sau 3 ngày, bị reset nếu lại vượt giới hạn trong 3 ngày đó).
  + Không trả `429 Too Many Requests`, nên client gọi API (không phải người dùng trên trình duyệt) không biết mình đã bị giới hạn và không tự xử lý được.

### 9. Versioning + deprecation

- **Version prefix**: Đạt.
  + Version được đặt ngay trong path, áp dụng cho tất cả endpoint:
    + `/api/v2/contests`, `/api/v2/contest/<contest key>`
    + `/api/v2/problems`, `/api/v2/problem/<problem code>`
    + `/api/v2/submissions`, `/api/v2/submission/<submission id>`
    + `/api/v2/users`, `/api/v2/user/<user username>`
    + `/api/v2/participations`, `/api/v2/organizations`, `/api/v2/languages`, `/api/v2/judges`
