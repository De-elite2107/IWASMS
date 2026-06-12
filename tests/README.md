# IWASMS Test Scripts

Test scripts for the Intelligent Web Application Security Monitoring System.

## Prerequisites

- Backend running on `http://localhost:8000`
- Admin user created (`admin` / `admin123`)

## Available Tests

| Script | Description |
|--------|-------------|
| `test_all_attacks.sh` | Full suite — all 6 attack types + normal traffic |
| `test_sql_injection.sh` | 5 SQL injection variants (UNION, blind, stacked, auth bypass, SQLMap) |
| `test_xss.sh` | 5 XSS variants (reflected, IMG, SVG, javascript:, body onload) |
| `test_command_injection.sh` | 5 command injection variants (cat, pipe, wget, reverse shell, uname) |
| `test_normal_traffic.sh` | 5 legitimate requests (should NOT trigger alerts) |
| `test_rapid_fire.sh` | 30 mixed requests sent quickly — tests throughput and live feed |

## Usage

```bash
cd tests/
chmod +x *.sh

# Run individual test
./test_sql_injection.sh

# Run all tests
./test_all_attacks.sh

# Stress test the live feed
./test_rapid_fire.sh
```

## Expected Results

- SQL Injection → `sql_injection` (critical)
- XSS → `xss` (high)
- Command Injection → `command_injection` (critical)
- Path Traversal → `path_traversal` (medium)
- CSRF → `csrf` (medium)
- LDAP Injection → `ldap_injection` (high)
- Normal → `normal` (normal)
