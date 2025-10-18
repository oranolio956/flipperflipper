#!/bin/bash

echo "=========================================="
echo "CRITICAL SECURITY CHECK"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CRITICAL_FOUND=0

echo "1. Checking for SQL Injection vulnerabilities..."
SQL_COUNT=$(grep -r "execute\|query" /workspace --include="*.py" | grep -v "#" | grep -E "%s|format|f\"" | wc -l)
if [ $SQL_COUNT -gt 5 ]; then
    echo -e "${RED}✗ CRITICAL: $SQL_COUNT potential SQL injection points found${NC}"
    CRITICAL_FOUND=$((CRITICAL_FOUND+1))
else
    echo -e "${GREEN}✓ SQL queries appear safe${NC}"
fi

echo ""
echo "2. Checking for Command Injection vulnerabilities..."
CMD_COUNT=$(grep -r "shell=True" /workspace --include="*.py" | grep -v "#" | wc -l)
if [ $CMD_COUNT -gt 10 ]; then
    echo -e "${RED}✗ CRITICAL: $CMD_COUNT shell=True calls found${NC}"
    CRITICAL_FOUND=$((CRITICAL_FOUND+1))
else
    echo -e "${GREEN}✓ Command execution appears safe${NC}"
fi

echo ""
echo "3. Checking for hardcoded passwords..."
PWD_COUNT=$(grep -r "password\s*=" /workspace --include="*.py" | grep -v "getenv\|environ\|#\|test" | grep -E "\".*\"|'.*'" | wc -l)
if [ $PWD_COUNT -gt 5 ]; then
    echo -e "${RED}✗ CRITICAL: $PWD_COUNT hardcoded passwords found${NC}"
    echo "  Examples:"
    grep -r "password\s*=" /workspace --include="*.py" | grep -v "getenv\|environ\|#\|test" | grep -E "\".*\"|'.*'" | head -3 | sed 's/^/    /'
    CRITICAL_FOUND=$((CRITICAL_FOUND+1))
else
    echo -e "${GREEN}✓ Password management appears safe${NC}"
fi

echo ""
echo "4. Checking for eval/exec usage..."
EVAL_COUNT=$(grep -r "eval(\|exec(" /workspace --include="*.py" | grep -v "#" | wc -l)
if [ $EVAL_COUNT -gt 5 ]; then
    echo -e "${YELLOW}⚠ WARNING: $EVAL_COUNT eval/exec calls found (review needed)${NC}"
else
    echo -e "${GREEN}✓ Minimal eval/exec usage${NC}"
fi

echo ""
echo "5. Checking for path traversal vulnerabilities..."
PATH_COUNT=$(grep -r "\.\.\/" /workspace --include="*.py" | grep -v "#" | wc -l)
if [ $PATH_COUNT -gt 0 ]; then
    echo -e "${RED}✗ CRITICAL: $PATH_COUNT potential path traversal points${NC}"
    CRITICAL_FOUND=$((CRITICAL_FOUND+1))
else
    echo -e "${GREEN}✓ Path handling appears safe${NC}"
fi

echo ""
echo "6. Checking for missing input validation..."
VALIDATE_COUNT=$(grep -r "request.get\|request.form\|request.args" /workspace --include="*.py" | grep -v "validate\|sanitize\|escape" | wc -l)
if [ $VALIDATE_COUNT -gt 20 ]; then
    echo -e "${YELLOW}⚠ WARNING: $VALIDATE_COUNT unvalidated inputs found${NC}"
else
    echo -e "${GREEN}✓ Input validation present${NC}"
fi

echo ""
echo "=========================================="
if [ $CRITICAL_FOUND -gt 0 ]; then
    echo -e "${RED}RESULT: $CRITICAL_FOUND CRITICAL SECURITY ISSUES FOUND${NC}"
    echo -e "${RED}DO NOT DEPLOY TO PRODUCTION${NC}"
    exit 1
else
    echo -e "${GREEN}RESULT: No critical security issues found${NC}"
    echo -e "${YELLOW}Still recommend full security audit before production${NC}"
    exit 0
fi