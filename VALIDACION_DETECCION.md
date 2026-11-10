# Validación del detector de personas

El modo Cuerpos utiliza YOLOX-S de OpenCV Zoo, ejecutado con OpenCV DNN.
Se sustituyó HOG/SVM tras comprobar omisiones en imágenes reales. YuNet se
conserva para rostros. Mixto combina ambos resultados.

## Comparación realizada

| Imagen | Personas visibles, verificación manual | HOG, umbral 0.2 | YOLOX, confianza 35% |
|---|---:|---:|---:|
| bus.jpg | 4, incluidas dos personas cortadas por los bordes | 2 | 4 |
| zidane.jpg | 2, con cuerpos parcialmente encuadrados | 0 | 2 |
| Imagen uniforme vacía | 0 | No comparado | 0 |

Imágenes de referencia utilizadas desde el repositorio de Ultralytics:

- https://github.com/ultralytics/ultralytics/blob/main/ultralytics/assets/bus.jpg
- https://github.com/ultralytics/ultralytics/blob/main/ultralytics/assets/zidane.jpg

Las fotos se descargaron para la validación local; no se distribuyen en este
repositorio. Los resultados anotados están en `.tmp-body-check/`, excluido de Git.

Se verificó en Edge con el servidor Django: carga real por el formulario,
recuadros visibles, conteos 4 y 2 en Cuerpos, conteo 2 en Mixto y cancelación
de los registros. La imagen uniforme produjo cero detecciones en Cuerpos.

La inferencia local directa tardó aproximadamente 1.1–1.5 segundos por imagen.
Estos resultados no constituyen una medición general de precisión ni garantizan
detectar todas las personas en otras fotografías o entregar video fluido en CPU.

## Controles y pruebas

### Combinación en modo Mixto

Se conserva la selección de personas de YOLOX sin aplicar otra supresión por
solapamiento: dos personas cercanas pueden tener recuadros superpuestos.
Los rostros se asocian uno a uno con la zona superior de las personas, admitiendo
cabezas parcialmente fuera del recuadro. Los rostros sin asociación se añaden
al resultado; estar dentro de un recuadro a la altura de piernas no basta para
eliminarlos. Esta asociación geométrica es una heurística y puede fallar en
escenas complejas; no representa identificación biométrica.

Se añadieron pruebas para personas superpuestas, múltiples rostros en un mismo
recuadro, rostro independiente, rostro a altura de piernas y cabeza parcialmente
fuera del recuadro. Mixto conserva 4 detecciones en bus.jpg y 2 en zidane.jpg.

- Confianza de personas: 35% inicial, 20% sensible, 10% exploratoria, 60% estricta.
- La confianza de rostros continúa siendo independiente.
- Pruebas del decodificador: clase persona, filtrado por confianza, eliminación
  de duplicados y transformación de coordenadas a la imagen original.
- Prueba real del modelo con imagen vacía y validación de parámetros por la API.
- Modelo y licencia incluidos; inferencia sin descargas al iniciar.

Origen del modelo y especificación de preprocesamiento:
https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox
