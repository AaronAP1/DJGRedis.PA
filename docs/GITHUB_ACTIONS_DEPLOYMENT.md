# 🚀 GUÍA RÁPIDA: DEPLOYMENT CON GITHUB ACTIONS

## ✅ **LO QUE NECESITAS HACER AHORA**

### **Paso 1: Agregar el Publish Profile a GitHub Secrets**

1. **Leer el archivo que acabamos de generar:**
   ```powershell
   Get-Content publish-profile.xml
   ```

2. **Copiar TODO el contenido** (es un XML largo)

3. **Ir a GitHub:**
   - Abre: https://github.com/AaronAP1/DJGRedis.PA/settings/secrets/actions
   - Click en **"New repository secret"**
   - Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Value: **Pegar el XML completo**
   - Click **"Add secret"**

---

### **Paso 2: Hacer Commit y Push**

```powershell
# Agregar cambios
git add .

# Commit
git commit -m "feat: Configure Azure App Service deployment"

# Push (esto activará el workflow automáticamente)
git push origin master
```

---

### **Paso 3: Monitorear el Deployment**

1. **Ver el workflow en GitHub:**
   - https://github.com/AaronAP1/DJGRedis.PA/actions

2. **El workflow hará:**
   - ✅ Build de Python 3.11
   - ✅ Instalar dependencias
   - ✅ Crear ZIP limpio (sin .venv, logs, backups)
   - ✅ Desplegar a Azure
   - ⏱️ Tiempo estimado: 3-5 minutos

---

## 📊 **VENTAJAS DE GITHUB ACTIONS**

| Problema Anterior | Solución GitHub Actions |
|-------------------|------------------------|
| ❌ Sube .venv local (500MB+) | ✅ Solo código fuente |
| ❌ Sube backups/logs | ✅ Ignora archivos innecesarios |
| ❌ Build falla sin detalles | ✅ Logs claros y detallados |
| ❌ Deployment manual | ✅ Automático en cada push |
| ❌ Difícil debuggear | ✅ Logs en GitHub Actions |

---

## 🔧 **COMANDOS ÚTILES**

```powershell
# Ver el publish profile que se subió
Get-Content publish-profile.xml

# Ver status de Git
git status

# Ver workflows de GitHub (requiere GitHub CLI)
gh workflow list

# Trigger manual del workflow
gh workflow run "Deploy to Azure App Service"

# Ver logs del último run
gh run list
```

---

## 🐛 **SI EL DEPLOYMENT FALLA EN GITHUB ACTIONS**

1. **Ver logs detallados:**
   - GitHub → Actions → Click en el workflow fallido
   - Click en "build-and-deploy" job
   - Ver step que falló

2. **Problemas comunes:**
   - **Secret no configurado**: Verifica `AZURE_WEBAPP_PUBLISH_PROFILE`
   - **Dependencias faltantes**: Actualiza `requirements.txt`
   - **Tests fallan**: Comenta línea de tests en el workflow

---

## ✅ **VERIFICACIÓN POST-DEPLOYMENT**

Una vez que GitHub Actions termine (verde ✅):

```powershell
# Verificar la app
.\scripts\verify_deployment.ps1

# O manual:
curl https://upeu-ppp-api-5983.azurewebsites.net

# Ver logs de Azure
az webapp log tail --name upeu-ppp-api-5983 -g rg-upeu-ppp-students
```

---

## 💰 **BAJAR A FREE TIER (F1) DESPUÉS**

Una vez que todo funcione, puedes bajar a F1 para $0/mes:

```powershell
az appservice plan update --name asp-upeu-ppp --resource-group rg-upeu-ppp-students --sku F1
```

**Nota**: F1 tiene limitaciones:
- 60 min CPU/día
- 1 GB RAM
- No auto-scaling
- Ideal para desarrollo/demos

Si el equipo de frontend necesita más estabilidad, mantén B1 ($13/mes con student credit).

---

## 🎯 **SIGUIENTE PASO**

**¡AHORA MISMO!**

1. Ejecuta: `Get-Content publish-profile.xml | clip` (copia al portapapeles)
2. Ve a: https://github.com/AaronAP1/DJGRedis.PA/settings/secrets/actions
3. Crea el secret `AZURE_WEBAPP_PUBLISH_PROFILE`
4. Haz commit y push
5. Observa el magic happening en GitHub Actions 🚀

---

**Fecha**: 30 de Octubre 2025  
**Método**: GitHub Actions + Azure App Service  
**Estado**: ✅ Listo para deploy automático
