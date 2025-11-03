# Ejemplo POST - Crear Carta de Presentación

## Endpoint
```
POST http://localhost:8000/api/v2/cartas-presentacion/
```

## Headers
```json
{
  "Content-Type": "application/json"
}
```

## Body (JSON)
```json
{
  "escuela_id": 7,
  "empresa_id": 1,
  "student_full_name": "María González López",
  "student_code": "2020654321",
  "student_email": "maria.gonzalez@upeu.edu.pe",
  "year_of_study": "Cuarto año",
  "study_cycle": "IX",
  "company_representative": "Carlos Martínez",
  "company_position": "Gerente de RRHH",
  "company_phone": "987654321",
  "practice_area": "Desarrollo Web",
  "start_date": "2025-12-01"
}
```

## Campos Requeridos

### Relaciones (NUEVOS)
- **escuela_id**: ID de la escuela (INTEGER) - Debe existir en `upeu_escuela` con estado ACTIVO
- **empresa_id**: ID de la empresa (INTEGER) - Debe existir en `upeu_empresa` con estado ACTIVO

### Datos del Estudiante
- **student_full_name**: Nombre completo (max 200 caracteres)
- **student_code**: Código del estudiante (10 caracteres)
- **student_email**: Email institucional
- **year_of_study**: Uno de: "Primer año", "Segundo año", "Tercer año", "Cuarto año", "Quinto año", "Sexto año"
- **study_cycle**: Ciclo en números romanos (ej: IX, X, XI)

### Datos de la Práctica
- **company_representative**: Nombre del representante de la empresa
- **company_position**: Cargo del representante
- **company_phone**: Teléfono de contacto
- **practice_area**: Área de práctica
- **start_date**: Fecha de inicio (YYYY-MM-DD, no puede ser pasada)

## IDs Disponibles

### Escuelas (upeu_escuela)
```
ID: 7 - Ingeniería de Sistemas (ACTIVO)
```

### Empresas (upeu_empresa)
```
ID: 1 - TechSol (ACTIVO)
ID: 2 - InnovaTech (ACTIVO)
```

## Respuesta Exitosa (201 Created)
```json
{
  "id": 4,
  "escuela_id": 7,
  "empresa_id": 1,
  "student_full_name": "María González López",
  "student_code": "2020654321",
  "student_email": "maria.gonzalez@upeu.edu.pe",
  "year_of_study": "Cuarto año",
  "study_cycle": "IX",
  "company_representative": "Carlos Martínez",
  "company_position": "Gerente de RRHH",
  "company_phone": "987654321",
  "practice_area": "Desarrollo Web",
  "start_date": "2025-12-01",
  "status": "DRAFT",
  "created_at": "2025-11-02T12:00:00Z",
  "updated_at": "2025-11-02T12:00:00Z"
}
```

## Errores Comunes

### Error: escuela_id inválido
```json
{
  "escuela_id": ["Pk inválido \"999\" - objeto no existe."]
}
```
**Solución**: Usa un ID de escuela válido (ver lista arriba)

### Error: empresa_id inválido
```json
{
  "empresa_id": ["Pk inválido \"999\" - objeto no existe."]
}
```
**Solución**: Usa un ID de empresa válido con estado ACTIVO

### Error: Fecha pasada
```json
{
  "start_date": ["La fecha de inicio no puede ser anterior a hoy."]
}
```
**Solución**: Usa una fecha futura o la fecha actual

### Error: Año de estudios inválido
```json
{
  "year_of_study": ["Año de estudios debe ser uno de: Primer año, Segundo año, ..."]
}
```
**Solución**: Usa uno de los valores permitidos

### Error: Ciclo inválido
```json
{
  "study_cycle": ["Ciclo debe estar en números romanos (ej: IX, X, XI)"]
}
```
**Solución**: Usa números romanos (I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII)

## Verificar Escuelas y Empresas Disponibles

Ejecuta este script para ver los IDs disponibles:
```bash
python scripts/list_schools_companies.py
```
