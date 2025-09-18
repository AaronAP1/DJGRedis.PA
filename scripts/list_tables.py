import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print('ERROR during django.setup():', e)
    raise

from django.db import connection

print('DATABASE ENGINE:', settings.DATABASES['default'].get('ENGINE'))
print('DATABASE NAME:', settings.DATABASES['default'].get('NAME'))

intros = connection.introspection
try:
    tables = intros.table_names()
    print('Total tables:', len(tables))
    # show a selected set related to auth and our app
    auth_tables = [t for t in tables if 'auth' in t or 'user' in t or 'users' in t or 'database' in t]
    print('Related tables (auth/user/users/database/...):')
    for t in sorted(auth_tables):
        print(' -', t)
except Exception as e:
    print('Error listing tables:', e)
    raise
