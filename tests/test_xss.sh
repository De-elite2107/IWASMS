#!/bin/bash
# IWASMS — XSS Test Cases
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "=== Cross-Site Scripting (XSS) Tests ==="
echo ""

echo "1. Reflected XSS (script tag):"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/search?q=<script>alert(document.cookie)</script>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.1"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "2. IMG onerror:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/profile?avatar=<img src=x onerror=alert(1)>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.2"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "3. SVG payload:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/api/comments","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"text=<svg onload=alert(1)>","source_ip":"10.0.1.3"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "4. JavaScript protocol:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/redirect?url=javascript:alert(document.domain)","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.4"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "5. Body onload:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/api/feedback","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"message=<body onload=alert(document.cookie)>","source_ip":"10.0.1.5"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"
