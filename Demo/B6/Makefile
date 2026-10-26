.PHONY: login refresh get-post clean

login:
	@echo "===> Calling POST /auth/login"
	@curl -s -X POST http://127.0.0.1:5000/auth/login \
		-H "Content-Type: application/json" \
		-d '{"email":"alice@vnu.edu.vn","password":"alice123"}' | tee .login.json; echo ""

refresh:
	@echo "===> Calling POST /auth/refresh"
	@TOKEN=$$(test -f .login.json && grep -o '"refresh_token":"[^"]*' .login.json | cut -d'"' -f4 || curl -s -X POST http://127.0.0.1:5000/auth/login -H "Content-Type: application/json" -d '{"email":"alice@vnu.edu.vn","password":"alice123"}' | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4); \
	curl -s -X POST http://127.0.0.1:5000/auth/refresh \
		-H "Authorization: Bearer $$TOKEN"; echo ""

get-post:
	@echo "===> Calling GET /posts/1"
	@TOKEN=$$(test -f .login.json && grep -o '"access_token":"[^"]*' .login.json | cut -d'"' -f4 || curl -s -X POST http://127.0.0.1:5000/auth/login -H "Content-Type: application/json" -d '{"email":"alice@vnu.edu.vn","password":"alice123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4); \
	curl -s -X GET http://127.0.0.1:5000/posts/1 \
		-H "Authorization: Bearer $$TOKEN"; echo ""

clean:
	@echo "===> Cleaning temporary files and caches"
	@rm -f .login.json *.token
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed."
