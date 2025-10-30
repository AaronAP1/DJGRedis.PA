# Script para limpiar backup SQL y dejar solo INSERTs
# Ejecutar: python clean_backup.py

import re

# Leer el backup original
with open(r"C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio\backuplocalupeu_ppp_system-202510300859.sql", "r", encoding="utf-8") as f:
    content = f.read()

# Dividir en líneas
lines = content.split('\n')

# Filtrar: mantener solo INSERT INTO y COPY (datos)
clean_lines = []
skip_until_empty = False
in_copy_block = False

for line in lines:
    # Mantener comentarios importantes
    if line.startswith('--'):
        if 'Data for Name:' in line or 'Name:' in line:
            clean_lines.append(line)
        continue
    
    # Mantener configuraciones básicas
    if line.startswith('SET '):
        if 'transaction_timeout' not in line:
            clean_lines.append(line)
        continue
    
    # Mantener INSERTS
    if line.startswith('INSERT INTO '):
        clean_lines.append(line)
        continue
    
    # Detectar inicio de bloque COPY
    if line.startswith('COPY '):
        in_copy_block = True
        clean_lines.append(line)
        continue
    
    # Detectar fin de bloque COPY
    if in_copy_block:
        clean_lines.append(line)
        if line.strip() == '\\.':
            in_copy_block = False
        continue
    
    # Mantener SELECT para secuencias
    if 'SELECT pg_catalog.setval' in line:
        clean_lines.append(line)
        continue

# Guardar archivo limpio
output_file = r"C:\Users\xdxdxdxd\OneDrive - Universidad Peruana Unión\Escritorio\backup_data_only.sql"
with open(output_file, "w", encoding="utf-8") as f:
    f.write('\n'.join(clean_lines))

print(f"✅ Backup limpiado guardado en: {output_file}")
print(f"   Líneas originales: {len(lines)}")
print(f"   Líneas filtradas: {len(clean_lines)}")
