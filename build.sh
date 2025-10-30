#!/usr/bin/env bash
# =====================================================
# BUILD SCRIPT FOR RENDER.COM
# Sistema de Gestión de Prácticas Profesionales - UPeU
# =====================================================

set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "🚀 Starting Render build process..."
echo "=================================="

# =====================================================
# 1. UPGRADE PIP
# =====================================================
echo ""
echo "📦 Step 1: Upgrading pip..."
python -m pip install --upgrade pip
echo "✅ Pip upgraded successfully"

# =====================================================
# 2. INSTALL DEPENDENCIES
# =====================================================
echo ""
echo "📚 Step 2: Installing Python dependencies..."
pip install -r requirements/production.txt
echo "✅ Dependencies installed successfully"

# =====================================================
# 3. COLLECT STATIC FILES
# =====================================================
echo ""
echo "🎨 Step 3: Collecting static files..."
python manage.py collectstatic --no-input --clear
echo "✅ Static files collected successfully"

# =====================================================
# 4. RUN DATABASE MIGRATIONS
# =====================================================
echo ""
echo "🗄️  Step 4: Running database migrations..."
python manage.py migrate --no-input
echo "✅ Migrations completed successfully"

# =====================================================
# 5. CREATE CACHE TABLE (if using DB cache)
# =====================================================
echo ""
echo "💾 Step 5: Creating cache tables..."
python manage.py createcachetable || echo "⚠️  Cache table already exists or not needed"

# =====================================================
# 6. VERIFY DEPLOYMENT (Optional health checks)
# =====================================================
echo ""
echo "🔍 Step 6: Verifying deployment..."

# Check if manage.py is accessible
if [ -f "manage.py" ]; then
    echo "✅ manage.py found"
else
    echo "❌ manage.py not found!"
    exit 1
fi

# Check critical settings
python manage.py check --deploy --fail-level WARNING || echo "⚠️  Deployment check warnings (non-critical)"

# =====================================================
# 7. COMPILE MESSAGES (if using i18n)
# =====================================================
# Uncomment if using Django internationalization
# echo ""
# echo "🌍 Step 7: Compiling translation messages..."
# python manage.py compilemessages

# =====================================================
# 8. LOAD INITIAL DATA (Optional)
# =====================================================
# Uncomment to load fixtures on first deployment
# echo ""
# echo "📥 Step 8: Loading initial data..."
# python manage.py loaddata initial_data.json || echo "⚠️  No initial data to load"

echo ""
echo "=================================="
echo "✅ Build completed successfully!"
echo "🎉 Ready to deploy!"
echo "=================================="
