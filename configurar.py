"""Crea .env local sin sobrescribir configuración ni publicar credenciales."""
from pathlib import Path
import secrets
path=Path(__file__).parent/'.env'
if path.exists():raise SystemExit('.env ya existe; se conserva sin cambios.')
text=(path.parent/'.env.example').read_text(encoding='utf-8')
text=text.replace('GENERAR_CON_CONFIGURAR_PY',secrets.token_urlsafe(48)).replace('POSTGRES_PASSWORD=REEMPLAZAR','POSTGRES_PASSWORD='+secrets.token_urlsafe(24))
path.write_text(text,encoding='utf-8')
print('Creado .env. Si usa PostgreSQL local, coloque allí su usuario y contraseña. No suba este archivo a GitHub.')
