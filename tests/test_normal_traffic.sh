#!/bin/bash
# IWASMS — Normal (Legitimate) Traffic Test Cases
# These should all be classified as "normal" with no alerts generated
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "=== Normal Traffic Tests (should NOT trigger alerts) ==="
echo ""

echo "1. Product listing:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/products?page=1&limit=20&category=electronics","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36"},"body":"","source_ip":"192.168.1.50"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity|is_attack"

echo ""
echo "2. Search query:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/api/search?q=wireless+headphones&brand=sony&min_price=50&max_price=200","headers":{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15"},"body":"","source_ip":"192.168.1.60"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity|is_attack"

echo ""
echo "3. JSON API call:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/api/orders","headers":{"User-Agent":"Mozilla/5.0 Chrome/118","Content-Type":"application/json"},"body":"{\"product_id\":42,\"quantity\":2,\"shipping\":\"express\"}","source_ip":"192.168.2.10"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity|is_attack"

echo ""
echo "4. User registration:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"POST","url":"/auth/register","headers":{"User-Agent":"Mozilla/5.0 Firefox/119","Content-Type":"application/json"},"body":"{\"username\":\"newuser\",\"email\":\"user@example.com\",\"password\":\"Str0ngP@ss!\"}","source_ip":"192.168.3.25"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity|is_attack"

echo ""
echo "5. Static asset request:"
curl -s -X POST "$BASE_URL/classify/" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"method":"GET","url":"/static/css/main.bundle.css","headers":{"User-Agent":"Mozilla/5.0 Chrome/118"},"body":"","source_ip":"192.168.1.100"}' | python3 -m json.tool | grep -E "attack_type|confidence|severity|is_attack"
