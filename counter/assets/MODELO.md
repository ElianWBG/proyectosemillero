# Modelo de detección de rostros
YuNet, OpenCV Zoo. Se utiliza mediante cv2.FaceDetectorYN; no reconoce identidades.
Fuente: https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
Licencia original incluida en LICENSE_YUNET.txt.
SHA256: 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
Se incluye el modelo para que la inferencia funcione sin descargarlo al iniciar.

## Detector de personas/cuerpos

YOLOX-S, OpenCV Zoo. Inferencia con cv2.dnn y filtrado a la clase person de COCO (0). Sustituye HOG/SVM.
Fuente: https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox
Archivo: object_detection_yolox_2022nov.onnx (35,858,002 bytes).
SHA256: c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063
Licencia: Apache 2.0, incluida en LICENSE_YOLOX.txt.
Entrada: RGB 640x640, rango 0-255, relleno 114 alineado arriba a la izquierda; salida decodificada con strides 8, 16 y 32. Confianza: objectness por puntuación de persona; NMS IoU 0.45. Las cajas se escalan y recortan a la imagen original.
