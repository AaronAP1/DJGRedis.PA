"""
Script para corregir nombres de campos en viewsets.py
De inglés a español según la estructura de la BD
"""

import re

# Leer el archivo
file_path = r'C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio\DJGRedis.PA\src\adapters\primary\rest_api\viewsets.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Contador de cambios
changes = 0

# 1. Importar get_user_role si no existe
if 'from src.infrastructure.security.permission_helpers import get_user_role' not in content:
    # Buscar la sección de imports
    import_section = content.find('from src.infrastructure.security.permissions import')
    if import_section != -1:
        # Insertar después de esta línea
        end_of_line = content.find('\n', import_section)
        content = (content[:end_of_line + 1] + 
                  'from src.infrastructure.security.permission_helpers import get_user_role\n' +
                  content[end_of_line + 1:])
        changes += 1
        print("✅ Agregado import de get_user_role")

# 2. Reemplazar user.role con get_user_role(user)
# Patrones a buscar y reemplazar
patterns = [
    # user.role == 'VALUE'
    (r"(\w+)\.role\s*==\s*'([A-Z_]+)'", r"get_user_role(\1) == '\2'"),
    # user.role != 'VALUE'
    (r"(\w+)\.role\s*!=\s*'([A-Z_]+)'", r"get_user_role(\1) != '\2'"),
    # user.role in ['VALUE1', 'VALUE2']
    (r"(\w+)\.role\s+in\s+\[(.*?)\]", r"get_user_role(\1) in [\2]"),
    # 'role': user.role en diccionarios
    (r"'role':\s*(\w+)\.role", r"'role': get_user_role(\1)"),
    # user_role = request.user.role
    (r"(\w+)\s*=\s*(\w+)\.user\.role\b", r"\1 = get_user_role(\2.user)"),
]

for pattern, replacement in patterns:
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        count = len(re.findall(pattern, content))
        changes += count
        print(f"✅ Reemplazados {count} casos de patrón: {pattern}")
        content = new_content

# 3. Guardar el archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Total de cambios realizados: {changes}")
print("✅ Archivo actualizado exitosamente")
