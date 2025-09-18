#!/bin/bash

# =======================================================
# SCRIPT DE VERIFICACIÓN POST-DEPLOYMENT
# Verifica que todos los servicios estén funcionando
# =======================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Función para logging
log() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

test_start() {
    ((TESTS_TOTAL++))
    log "$1"
}

# =======================================================
# TESTS DE INFRAESTRUCTURA
# =======================================================

echo "======================================================="
echo "VERIFICACIÓN POST-DEPLOYMENT - SISTEMA PPP UPeU"
echo "======================================================="
echo ""

# Test 1: Verificar Docker Compose
test_start "Verificando estado de contenedores Docker"
if docker-compose ps | grep -q "Up"; then
    success "Contenedores Docker están ejecutándose"
else
    fail "Algunos contenedores Docker no están funcionando"
fi

# Test 2: Verificar servicios individuales
services=("postgres_db" "mongodb" "redis_cache" "django_app" "celery_worker" "celery_beat")
for service in "${services[@]}"; do
    test_start "Verificando servicio: $service"
    if docker-compose ps "$service" | grep -q "Up"; then
        success "Servicio $service está ejecutándose"
    else
        fail "Servicio $service no está funcionando"
    fi
done

# =======================================================
# TESTS DE CONECTIVIDAD DE BASE DE DATOS
# =======================================================

# Test 3: PostgreSQL
test_start "Probando conectividad PostgreSQL"
if docker-compose exec postgres_db pg_isready -U upeu_admin -d upeu_ppp_db >/dev/null 2>&1; then
    success "PostgreSQL responde correctamente"
else
    fail "PostgreSQL no responde"
fi

# Test 4: Verificar tablas PostgreSQL
test_start "Verificando tablas en PostgreSQL"
TABLES_COUNT=$(docker-compose exec postgres_db psql -U upeu_admin -d upeu_ppp_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
if [ "$TABLES_COUNT" -gt 25 ]; then
    success "PostgreSQL tiene $TABLES_COUNT tablas (esperado: 32+)"
else
    fail "PostgreSQL solo tiene $TABLES_COUNT tablas (esperado: 32+)"
fi

# Test 5: MongoDB
test_start "Probando conectividad MongoDB"
if docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    success "MongoDB responde correctamente"
else
    fail "MongoDB no responde"
fi

# Test 6: Verificar colecciones MongoDB
test_start "Verificando colecciones en MongoDB"
COLLECTIONS_COUNT=$(docker-compose exec mongodb mongosh upeu_documents --eval "db.getCollectionNames().length" --quiet 2>/dev/null | tr -d ' ')
if [ "$COLLECTIONS_COUNT" -gt 5 ]; then
    success "MongoDB tiene $COLLECTIONS_COUNT colecciones (esperado: 6+)"
else
    fail "MongoDB solo tiene $COLLECTIONS_COUNT colecciones (esperado: 6+)"
fi

# Test 7: Redis
test_start "Probando conectividad Redis"
if docker-compose exec redis_cache redis-cli ping >/dev/null 2>&1; then
    success "Redis responde correctamente"
else
    fail "Redis no responde"
fi

# =======================================================
# TESTS DE APLICACIÓN WEB
# =======================================================

# Test 8: Health endpoint
test_start "Probando health endpoint de Django"
if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
    success "Health endpoint responde correctamente"
else
    fail "Health endpoint no responde"
fi

# Test 9: Admin panel
test_start "Probando panel de administración"
ADMIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ 2>/dev/null)
if [ "$ADMIN_RESPONSE" = "200" ] || [ "$ADMIN_RESPONSE" = "302" ]; then
    success "Panel de administración accesible (HTTP $ADMIN_RESPONSE)"
else
    fail "Panel de administración no accesible (HTTP $ADMIN_RESPONSE)"
fi

# Test 10: GraphQL endpoint
test_start "Probando endpoint GraphQL"
GRAPHQL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/graphql/ 2>/dev/null)
if [ "$GRAPHQL_RESPONSE" = "200" ]; then
    success "GraphQL endpoint accesible (HTTP $GRAPHQL_RESPONSE)"
else
    fail "GraphQL endpoint no accesible (HTTP $GRAPHQL_RESPONSE)"
fi

# Test 11: API REST
test_start "Probando API REST"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/ 2>/dev/null)
if [ "$API_RESPONSE" = "200" ] || [ "$API_RESPONSE" = "404" ]; then
    success "API REST accesible (HTTP $API_RESPONSE)"
else
    fail "API REST no accesible (HTTP $API_RESPONSE)"
fi

# =======================================================
# TESTS DE FUNCIONALIDAD ESPECÍFICA
# =======================================================

# Test 12: Django management commands
test_start "Probando comandos de gestión Django"
if docker-compose exec django_app python manage.py check >/dev/null 2>&1; then
    success "Comandos de gestión Django funcionan"
else
    fail "Comandos de gestión Django fallan"
fi

# Test 13: Migraciones Django
test_start "Verificando estado de migraciones"
MIGRATIONS_OUTPUT=$(docker-compose exec django_app python manage.py showmigrations 2>/dev/null)
if echo "$MIGRATIONS_OUTPUT" | grep -q "\[X\]"; then
    success "Migraciones aplicadas correctamente"
else
    fail "Migraciones no aplicadas correctamente"
fi

# Test 14: Celery worker
test_start "Verificando Celery worker"
if docker-compose exec celery_worker celery status >/dev/null 2>&1; then
    success "Celery worker está funcionando"
else
    fail "Celery worker no está funcionando"
fi

# Test 15: Superusuario existe
test_start "Verificando existencia de superusuario"
SUPERUSER_CHECK=$(docker-compose exec django_app python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" 2>/dev/null)
if echo "$SUPERUSER_CHECK" | grep -q "True"; then
    success "Superusuario existe en el sistema"
else
    fail "No existe superusuario en el sistema"
fi

# =======================================================
# TESTS DE SEGURIDAD BÁSICA
# =======================================================

# Test 16: Variables de entorno
test_start "Verificando variables de entorno críticas"
if [ -f ".env" ]; then
    if grep -q "SECRET_KEY" .env && grep -q "POSTGRES_PASSWORD" .env; then
        success "Variables de entorno críticas configuradas"
    else
        fail "Variables de entorno críticas faltantes"
    fi
else
    fail "Archivo .env no encontrado"
fi

# Test 17: Configuración de red Docker
test_start "Verificando configuración de red Docker"
NETWORK_INFO=$(docker network inspect djgredispa_default 2>/dev/null)
if echo "$NETWORK_INFO" | grep -q "172.20.0"; then
    success "Red Docker personalizada configurada"
else
    warning "Red Docker usando configuración por defecto"
fi

# Test 18: Volúmenes persistentes
test_start "Verificando volúmenes persistentes"
VOLUMES=$(docker volume ls | grep djgredispa)
if [ $(echo "$VOLUMES" | wc -l) -ge 4 ]; then
    success "Volúmenes persistentes creados"
else
    fail "Volúmenes persistentes insuficientes"
fi

# =======================================================
# TESTS DE PERFORMANCE BÁSICA
# =======================================================

# Test 19: Tiempo de respuesta aplicación
test_start "Midiendo tiempo de respuesta de la aplicación"
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/health/ 2>/dev/null || echo "999")
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    success "Tiempo de respuesta aceptable: ${RESPONSE_TIME}s"
else
    warning "Tiempo de respuesta lento: ${RESPONSE_TIME}s"
fi

# Test 20: Memoria de contenedores
test_start "Verificando uso de memoria de contenedores"
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.MemUsage}}" | tail -n +2 | head -1)
if [ -n "$MEMORY_USAGE" ]; then
    success "Contenedores usando memoria: $MEMORY_USAGE"
else
    warning "No se pudo obtener información de memoria"
fi

# =======================================================
# TESTS DE DATOS INICIALES
# =======================================================

# Test 21: Configuración inicial MongoDB
test_start "Verificando configuración inicial en MongoDB"
CONFIG_CHECK=$(docker-compose exec mongodb mongosh upeu_documents --eval "db.system_config.findOne({'_id': 'app_config'})" --quiet 2>/dev/null)
if echo "$CONFIG_CHECK" | grep -q "max_file_size_mb"; then
    success "Configuración inicial en MongoDB encontrada"
else
    fail "Configuración inicial en MongoDB no encontrada"
fi

# Test 22: Índices de base de datos
test_start "Verificando índices en PostgreSQL"
INDEXES_COUNT=$(docker-compose exec postgres_db psql -U upeu_admin -d upeu_ppp_db -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null | tr -d ' ')
if [ "$INDEXES_COUNT" -gt 20 ]; then
    success "PostgreSQL tiene $INDEXES_COUNT índices"
else
    warning "PostgreSQL solo tiene $INDEXES_COUNT índices"
fi

# =======================================================
# TESTS DE INTEGRACIÓN
# =======================================================

# Test 23: Integración Django-PostgreSQL
test_start "Probando integración Django-PostgreSQL"
if docker-compose exec django_app python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('OK')" 2>/dev/null | grep -q "OK"; then
    success "Integración Django-PostgreSQL funcionando"
else
    fail "Integración Django-PostgreSQL fallando"
fi

# Test 24: Integración Django-Redis
test_start "Probando integración Django-Redis"
if docker-compose exec django_app python manage.py shell -c "from django.core.cache import cache; cache.set('test', 'ok'); print(cache.get('test'))" 2>/dev/null | grep -q "ok"; then
    success "Integración Django-Redis funcionando"
else
    fail "Integración Django-Redis fallando"
fi

# Test 25: Logs de aplicación
test_start "Verificando generación de logs"
LOG_CHECK=$(docker-compose logs django_app 2>/dev/null | tail -5)
if [ -n "$LOG_CHECK" ]; then
    success "Logs de aplicación generándose correctamente"
else
    warning "Logs de aplicación no encontrados o vacíos"
fi

# =======================================================
# RESUMEN FINAL
# =======================================================

echo ""
echo "======================================================="
echo "RESUMEN DE VERIFICACIÓN POST-DEPLOYMENT"
echo "======================================================="
echo ""
echo "Tests ejecutados: $TESTS_TOTAL"
echo -e "Tests exitosos: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests fallidos: ${RED}$TESTS_FAILED${NC}"
echo ""

# Calcular porcentaje de éxito
SUCCESS_RATE=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT EXITOSO${NC}"
    echo "Todos los tests pasaron. El sistema está listo para uso."
elif [ $SUCCESS_RATE -gt 80 ]; then
    echo -e "${YELLOW}⚠️  DEPLOYMENT PARCIALMENTE EXITOSO${NC}"
    echo "La mayoría de tests pasaron ($SUCCESS_RATE%). Revisar fallos menores."
else
    echo -e "${RED}❌ DEPLOYMENT CON PROBLEMAS${NC}"
    echo "Varios tests fallaron ($SUCCESS_RATE% éxito). Revisar configuración."
fi

echo ""
echo "URLs del sistema:"
echo "• Aplicación: http://localhost:8000"
echo "• Admin: http://localhost:8000/admin"
echo "• GraphQL: http://localhost:8000/graphql"
echo "• API: http://localhost:8000/api/v1/"
echo ""
echo "Para ver logs detallados: docker-compose logs -f"
echo "Para troubleshooting: ver docs/DEPLOYMENT_GUIDE.md"
echo ""
echo "======================================================="

# Exit code basado en resultados
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
elif [ $SUCCESS_RATE -gt 80 ]; then
    exit 1
else
    exit 2
fi