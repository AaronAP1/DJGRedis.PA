import re

# Leer archivo
with open('src/infrastructure/security/permissions.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar todas las ocurrencias de request.user.role por get_user_role(request.user)
content = re.sub(r'request\.user\.role\s*==', 'get_user_role(request.user) ==', content)

# Guardar archivo
with open('src/infrastructure/security/permissions.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado: todos los 'request.user.role' reemplazados por 'get_user_role(request.user)'")
