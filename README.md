# VisorLab

Conteo de personas con Django, OpenCV y PostgreSQL.

## Ejecutar con Docker

```sh
python configurar.py
docker compose up --build
```

Abrir http://localhost:8000 y permitir la cámara del computador.

## Ejecutar sin Docker

Python3.12 y PostgreSQL14 o superior.

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python configurar.py
```

Crear una base PostgreSQL vacía y colocar sus datos de conexión en `.env`.

```sh
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py runserver 127.0.0.1:8000
```

En Linux o macOS usar `.venv/bin/python`. No subir `.env` ni `.venv`.

## Pruebas

```sh
python manage.py test counter --keepdb
node --test tests/*.test.cjs
```

Con Docker: `docker compose exec web python manage.py test counter --keepdb`.
El usuario de pruebas necesita permiso para crear una base de prueba.

Rostros: YuNet preentrenado. Cuerpos completos: HOG/SVM. Los identificadores son temporales; no identifican personas por nombre. Modelo y licencia original incluidos en `counter/assets/`. La precisión depende de iluminación, encuadre y oclusiones. No se almacenan imágenes ni video de las sesiones.
