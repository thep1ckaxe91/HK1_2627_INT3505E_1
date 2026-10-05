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
  
