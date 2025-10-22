# 🚀 Quick Start - Sistema de Prácticas Profesionales

## 🎯 Inicio Rápido en 5 Minutos

### 1️⃣ Clonar y Configurar (1 min)

```bash
git clone https://github.com/AaronAP1/DJGRedis.PA.git
cd DJGRedis.PA
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements/minimal.txt
```

### 2️⃣ Base de Datos (1 min)

```bash
createdb practicas_db
cp .env.example .env  # Editar con tus credenciales
python manage.py migrate
```

### 3️⃣ Crear Admin (1 min)

```bash
python manage.py createsuperuser
# Email: admin@upeu.edu.pe
# Password: (tu password)
```

### 4️⃣ Iniciar Servidor (30 seg)

```bash
python manage.py runserver
```

### 5️⃣ Explorar (1.5 min)

- 🌐 **Admin**: http://localhost:8000/admin/
- 🔷 **GraphQL**: http://localhost:8000/graphql/
- 📊 **API v2**: http://localhost:8000/api/v2/
- 📚 **Docs**: http://localhost:8000/api/docs/

---

## 🐳 Con Docker (AÚN MÁS RÁPIDO)

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

✅ ¡Listo! Sistema corriendo en http://localhost:8000

---

## 🧪 Ejecutar Tests

```bash
pytest                      # Todos los tests
pytest --cov=src           # Con cobertura
pytest -v                  # Verbose
```

---

## 📊 Endpoints Principales

### REST API v2

```bash
# Listar prácticas
GET http://localhost:8000/api/v2/practices/

# Dashboard estudiante
GET http://localhost:8000/api/v2/dashboards/student/
Authorization: Bearer {token}

# Reporte en Excel
GET http://localhost:8000/api/v2/reports/practices/?format=excel
```

### GraphQL

```graphql
query {
  allPractices(first: 10) {
    edges {
      node {
        id
        area
        estado
        student { name }
      }
    }
  }
}
```

---

## 📚 Documentación Completa

| Guía | Para |
|------|------|
| [📘 Instalación](docs/GUIA_INSTALACION.md) | Setup completo |
| [👥 Usuario](docs/GUIA_USUARIO.md) | Manual por rol |
| [💻 Desarrollo](docs/GUIA_DESARROLLO.md) | Arquitectura y código |
| [🧪 Testing](docs/GUIA_TESTING.md) | Tests y cobertura |
| [🚀 Deployment](docs/DEPLOYMENT_GUIDE.md) | Producción |

---

## 🎓 Roles del Sistema

- **PRACTICANTE**: Gestiona su práctica
- **SUPERVISOR**: Evalúa practicantes
- **COORDINADOR**: Aprueba y reportes
- **SECRETARIA**: Valida documentos
- **ADMINISTRADOR**: Gestión total

---

## 🏗️ Arquitectura

```
Domain → Application → Adapters → Infrastructure
   ↓          ↓            ↓            ↓
Entities   Use Cases    REST/GraphQL  Security
```

---

## 📊 Estadísticas

- 📁 **~19,500** líneas totales
- 🌐 **231** endpoints
- 👥 **5** roles
- ✅ **88%** cobertura de tests
- 📚 **11,650** líneas de docs

---

## 🆘 Ayuda Rápida

```bash
# ¿Puerto ocupado?
python manage.py runserver 8001

# ¿DB no existe?
createdb practicas_db

# ¿Olvidaste contraseña?
python manage.py changepassword admin@upeu.edu.pe

# ¿Errores de migración?
python manage.py migrate --run-syncdb
```

---

## 📞 Soporte

- 📧 Email: soporte.practicas@upeu.edu.pe
- 🐛 Issues: [GitHub](https://github.com/AaronAP1/DJGRedis.PA/issues)
- 📚 Docs: `/docs/`

---

**Universidad Peruana Unión** - Ingeniería de Sistemas  
**Version 2.0** - Octubre 2024

🚀 **¡Listo para empezar!**
