# 🔄 MIGRAR BASE DE DATOS LOCAL A AZURE POSTGRESQL

## 📊 Método 1: CUSTOM (Recomendado)

### Paso 1: Export desde DBeaver (Base Local)

**Configuración de Export:**
```
Choose objects to export: [Seleccionar tu base de datos local]

Settings:
├─ Format:       Custom
├─ Compression:  Default
└─ Encoding:     UTF-8

Opciones importantes:
☐ Use SQL INSERT instead of COPY for rows
☐ Do not backup privileges (GRANT/REVOKE)
☐ Discard objects owner
☑ Add drop database statement
☐ Add create database statement

Output:
├─ Output folder: C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio
├─ File name:     backup_upeu_ppp_${timestamp}.backup
└─ Extra args:    (dejar vacío)
```

### Paso 2: Restaurar en Azure PostgreSQL

#### Opción A: Desde DBeaver

1. **Conectar a Azure** (ya lo hiciste antes):
   ```
   Host: psql-upeu-ppp-5628.postgres.database.azure.com
   Database: upeu_ppp_system
   User: upeuadmin
   ```

2. **Click derecho** en la database `upeu_ppp_system` → **Tools** → **Restore**

3. **Configurar Restore:**
   ```
   Input file: C:\...\backup_upeu_ppp_20251030.backup
   Format: Custom
   
   Options:
   ☑ Clean before restore (DROP objects)
   ☐ Create database
   ☑ Disable triggers during restore
   ☑ No owner
   ☑ No privileges
   ```

4. Click **Start**

#### Opción B: Desde Terminal (PowerShell)

```powershell
# Restaurar usando pg_restore
pg_restore `
  --host=psql-upeu-ppp-5628.postgres.database.azure.com `
  --port=5432 `
  --username=upeuadmin `
  --dbname=upeu_ppp_system `
  --clean `
  --no-owner `
  --no-privileges `
  --verbose `
  "C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio\backup_upeu_ppp.backup"
```

---

## 📄 Método 2: PLAIN SQL (Más Simple)

### Paso 1: Export SQL desde DBeaver

**Configuración:**
```
Format:       Plain
Encoding:     UTF-8
Compression:  None

Opciones:
☑ Use SQL INSERT instead of COPY for rows
☐ Do not backup privileges
☐ Discard objects owner  
☑ Add drop database statement
☐ Add create database statement

Output:
└─ File name: backup_upeu_ppp_${timestamp}.sql
```

### Paso 2: Restaurar SQL en Azure

#### Opción A: Desde DBeaver

1. Abrir el archivo `.sql` en DBeaver
2. Conectar a Azure PostgreSQL
3. **Execute SQL Script** (Ctrl+X o F9)

#### Opción B: Desde psql (Terminal)

```powershell
# Usando psql
$env:PGPASSWORD = "3TfnXOcxpgoSR2bAr16vW4IK"

psql `
  --host=psql-upeu-ppp-5628.postgres.database.azure.com `
  --port=5432 `
  --username=upeuadmin `
  --dbname=upeu_ppp_system `
  --file="C:\...\backup_upeu_ppp.sql"
```

---

## 🚀 Método 3: Django Fixtures (Para Datos de Prueba)

### Export desde Local

```powershell
# Exportar todos los datos
python manage.py dumpdata --indent 2 --output data_backup.json

# O por app específica
python manage.py dumpdata auth --indent 2 --output auth_data.json
python manage.py dumpdata src.adapters.db_adapters --indent 2 --output ppp_data.json
```

### Import en Azure

```powershell
# 1. Configurar .env para Azure
cp .env.azure .env

# 2. Ejecutar migraciones (crear estructura)
python manage.py migrate

# 3. Cargar datos
python manage.py loaddata data_backup.json
```

---

## 🎯 RECOMENDACIÓN ESPECÍFICA PARA TI

### Para Base de Datos CON datos importantes:

```
1. Export Local:
   ├─ Format: CUSTOM
   ├─ Compression: Default
   ├─ Encoding: UTF-8
   ├─ ☑ Add drop database statement
   └─ ☑ Discard objects owner

2. Restore Azure:
   ├─ Usar DBeaver GUI
   ├─ ☑ Clean before restore
   ├─ ☑ No owner
   └─ ☑ No privileges
```

### Para Base de Datos VACÍA (solo estructura Django):

```powershell
# Opción más simple: Dejar que Django cree todo

# 1. Copiar configuración
cp .env.azure .env

# 2. Crear estructura
python manage.py migrate

# 3. Crear superuser
python manage.py createsuperuser

# 4. Cargar datos de prueba (si tienes fixtures)
python manage.py loaddata initial_data.json
```

---

## ⚠️ IMPORTANTE: Diferencias Local vs Azure

### Eliminar comandos problemáticos del SQL:

Si usas **PLAIN SQL**, edita el archivo y elimina:

```sql
-- ELIMINAR estas líneas:
CREATE ROLE upeu_admin;
DROP DATABASE IF EXISTS upeu_ppp_system;
CREATE DATABASE upeu_ppp_system;
\connect upeu_ppp_system;
SET ROLE upeu_admin;
ALTER DATABASE ... OWNER TO ...;
ALTER TABLE ... OWNER TO ...;
GRANT ... TO ...;
```

**Reemplazar** `COPY` por `INSERT` si hay errores:
```sql
-- En vez de:
COPY tabla_name (col1, col2) FROM stdin;
dato1	dato2
\.

-- Usar:
INSERT INTO tabla_name (col1, col2) VALUES ('dato1', 'dato2');
```

---

## 🛠️ Script PowerShell Automatizado

```powershell
# backup_and_restore_azure.ps1

param(
    [string]$BackupFile = "backup_upeu_ppp.sql",
    [switch]$CustomFormat = $false
)

$AzureHost = "psql-upeu-ppp-5628.postgres.database.azure.com"
$AzureDb = "upeu_ppp_system"
$AzureUser = "upeuadmin"
$AzurePass = "3TfnXOcxpgoSR2bAr16vW4IK"

Write-Host "=== RESTAURANDO BACKUP EN AZURE ===" -ForegroundColor Cyan

if ($CustomFormat) {
    # Restaurar formato CUSTOM
    pg_restore `
        --host=$AzureHost `
        --port=5432 `
        --username=$AzureUser `
        --dbname=$AzureDb `
        --clean `
        --no-owner `
        --no-privileges `
        --verbose `
        $BackupFile
} else {
    # Restaurar formato PLAIN (SQL)
    $env:PGPASSWORD = $AzurePass
    
    psql `
        --host=$AzureHost `
        --port=5432 `
        --username=$AzureUser `
        --dbname=$AzureDb `
        --file=$BackupFile
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Backup restaurado exitosamente" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Fallo al restaurar backup" -ForegroundColor Red
}
```

**Uso:**
```powershell
# Para archivo SQL
.\backup_and_restore_azure.ps1 -BackupFile "mi_backup.sql"

# Para archivo CUSTOM
.\backup_and_restore_azure.ps1 -BackupFile "mi_backup.backup" -CustomFormat
```

---

## ✅ CHECKLIST PASO A PASO

### Preparación:
- [ ] Verificar conexión a Azure PostgreSQL desde DBeaver
- [ ] Tener backup de la base de datos local
- [ ] Verificar que `.env.azure` tenga las credenciales correctas

### Export (Local):
- [ ] Abrir DBeaver → Conexión local
- [ ] Click derecho en DB → Tools → Backup
- [ ] Configurar formato CUSTOM o PLAIN
- [ ] Seleccionar carpeta de destino
- [ ] Ejecutar backup

### Import (Azure):
- [ ] Abrir DBeaver → Conexión Azure
- [ ] Click derecho en `upeu_ppp_system` → Tools → Restore
- [ ] Seleccionar archivo de backup
- [ ] Configurar opciones (Clean, No owner, No privileges)
- [ ] Ejecutar restore

### Verificación:
- [ ] Refrescar schema en DBeaver
- [ ] Verificar que existan las tablas
- [ ] Contar registros: `SELECT COUNT(*) FROM tabla;`
- [ ] Probar Django: `python manage.py check`

---

## 🆘 Solución de Problemas Comunes

### Error: "permission denied for database"
```sql
-- Conectar como upeuadmin y ejecutar:
GRANT ALL PRIVILEGES ON DATABASE upeu_ppp_system TO upeuadmin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO upeuadmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO upeuadmin;
```

### Error: "role 'xxx' does not exist"
- **Solución**: Usar opciones `--no-owner` y `--no-privileges`

### Error: "COPY command not allowed"
- **Solución**: Exportar con "Use SQL INSERT instead of COPY"

---

## 📞 RESUMEN EJECUTIVO

**Para subir datos a Azure PostgreSQL, usa:**

1. **CUSTOM** si tienes muchos datos (>100MB)
2. **PLAIN SQL** si tienes pocos datos o quieres revisar el contenido
3. **Django Fixtures** si solo necesitas datos de prueba

**Mi recomendación:** Empieza con **PLAIN SQL** con la configuración que te marqué arriba.
