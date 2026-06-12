#!/bin/bash
# IWASMS — SQL Injection Test Cases
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "=== SQL Injection Tests ==="
echo ""

echo "1. UNION-based extraction:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/users?id=1 UNION SELECT username,password FROM users--","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.0.1"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "2. Boolean-based blind:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/products?id=1 AND 1=2 UNION SELECT NULL,NULL,NULL--","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.0.2"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "3. Stacked queries:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/api/search","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"q=test'\'' ; SELECT * FROM information_schema.tables--","source_ip":"10.0.0.3"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "4. Authentication bypass:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/login","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"username=admin'\''--&password=anything","source_ip":"10.0.0.4"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "5. SQLMap automated scan:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/items?sort=name;SELECT SLEEP(5)--","headers":{"User-Agent":"sqlmap/1.7.2#stable"},"body":"","source_ip":"10.0.0.5"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"
