[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md) | **[Español](README.es.md)** | [Deutsch](README.de.md)

# Red Sprite Filter

Una herramienta de escritorio para macOS destinada a la observación de eventos luminosos transitorios (TLE) de gran altitud, que criba automáticamente fotogramas y clips sospechosos de destellos de duendes rojos (red sprites) a partir de vídeos de tormentas grabados con cámaras.

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Release](https://img.shields.io/badge/download-DMG-00bcd4?style=flat-square)
![Local](https://img.shields.io/badge/processing-local-4caf50?style=flat-square)

## Qué hace

Los duendes rojos suelen ser breves, tenues, aparecen en lo alto del cielo y tienen formas finas y complejas. Revisar manualmente vídeos largos fotograma a fotograma lleva muchísimo tiempo. Esta herramienta analiza el vídeo completo, puntúa cada fotograma como candidato a duende rojo y exporta automáticamente:

- Fotogramas clave candidatos
- Clips cortos candidatos
- `candidates.csv`
- `contact_sheet.jpg`
- `report.html`
- `confirmed_candidates.csv` tras la revisión manual

No se detiene en el primer candidato: analiza el vídeo entero y luego elige los eventos candidatos con mayor puntuación de toda la grabación.

## Vista previa de la interfaz

La versión actual es una app de ventana nativa de macOS que usa una WebView para alojar la interfaz local. No abre el navegador y el procesado de vídeo nunca se sube a la red.

La interfaz incluye:

- Seleccionar vídeo / carpeta / directorio de salida
- Cribado preciso / cribado de alta recuperación
- Cuadrícula de fotogramas candidatos
- Reproducción de clips candidatos
- Progreso del escaneo, tiempo transcurrido y tiempo restante estimado
- Tiempo del clip en la línea temporal del vídeo original, por ejemplo `3:12-3:14`
- Guía de puntuación con categorías de alta / media / baja sospecha
- Revisión manual: confirmar / sospechoso / descartar
- Abrir informe / abrir directorio de resultados

## Descarga

Descarga desde la sección **Releases** (a la derecha o al final de la página):

```text
red-sprite-filter-1.0.6.dmg
```

Abre el DMG y arrastra la app (`红色精灵筛选器.app`, que se muestra como "Red Sprite Filter") a Aplicaciones o a cualquier carpeta.

## Primer arranque

La compilación actual no está firmada ni notarizada con un Apple Developer ID, por lo que macOS puede mostrar un aviso de "no se puede verificar el desarrollador".

Para abrirla:

1. Haz clic derecho en `红色精灵筛选器.app`
2. Elige "Abrir"
3. Vuelve a hacer clic en "Abrir" en el diálogo

## Dependencias

El paquete de macOS incluye:

- CPython 3.12.13
- NumPy 1.26.4
- Pillow 11.3.0
- FFmpeg 8.1.2
- FFprobe 8.1.2

Homebrew no es necesario. No hace falta instalar Python, pip ni ninguna dependencia de línea de comandos. La app comprueba sus dependencias incluidas al iniciar.

## Uso recomendado

### Cribado preciso de un solo vídeo

Ideal cuando sospechas que un vídeo concreto pudo captar duendes rojos.

Parámetros recomendados:

- Modo: Preciso
- Máx. candidatos: 24
- Puntuación mínima: 0.8
- Píxeles rojos mínimos: 8
- Pre-roll: 1.0 s
- Post-roll: 2.0 s

### Cribado previo en lotes de una carpeta

Ideal para revisar rápidamente un lote de material de tormentas.

Parámetros recomendados:

- Modo: Alta recuperación
- Máx. candidatos: 24
- Puntuación mínima: 0.012
- Píxeles rojos mínimos: 8

Tras el cribado previo, vuelve a ejecutar en modo Preciso los vídeos sospechosos.

## Guía de puntuación y categorías

Los candidatos se etiquetan por prioridad de revisión:

- `≥ 5.0`: objetivo altamente sospechoso
- `1.0 - 5.0`: objetivo medianamente sospechoso
- `< 1.0`: objetivo de baja sospecha

La categoría solo indica prioridad de revisión, no una conclusión final. Conviene confirmar con el fotograma clave, el clip exportado y el vídeo original.

## Cómo distinguir si un candidato es un duende rojo

Los candidatos que se parecen más a duendes rojos suelen tener:

- Una posición por encima del topo de las nubes o en la parte alta del encuadre
- Color claramente rojo o magenta
- Una forma localizada, no un resplandor rojo en todo el horizonte
- Estructura de columna vertical, filamentos, forma de medusa o ramificación fina
- Una duración extremadamente corta, normalmente visible solo en unos pocos fotogramas

Los falsos positivos frecuentes incluyen:

- Relámpagos intramensajeros o nube-suelo corrientes
- Luces de ciudad, faros de coche, luces de torres, luces de aviones
- Resplandor rojo en el horizonte
- Destellos de lente (lens flare)
- Grandes cambios de exposición
- Píxeles calientes fijos o ruido de compresión

## Privacidad

Todo el vídeo se procesa localmente en tu equipo. La herramienta nunca sube vídeos, fotogramas, clips candidatos ni información de rutas.

## Estado actual

Esta es una versión pública temprana de una herramienta de flujo de trabajo fotográfico. Está pensada para ayudar a cribar, no para sustituir la revisión manual. Se agradecen los issue y comentarios: falsos positivos, detecciones fallidas, comportamiento con distintos modelos de cámara y sugerencias de funciones.

## Mejoras completadas recientemente

- El paquete de macOS incluye CPython, NumPy, Pillow, FFmpeg y FFprobe; Homebrew no es necesario
- El instalador de Windows ya incluye `ffmpeg`, `ffprobe`, el entorno de Python y sus dependencias, y el escaneo ya no abre repetidamente ventanas de consola
- El escaneo del vídeo completo conserva varios eventos independientes que superan el umbral, incluidos los duendes consecutivos
- El escaneo por lotes de carpetas reúne los resultados en una lista de candidatos, fotogramas clave, clips, CSV, hoja de contactos e informe HTML
- Se añadieron progreso, tiempo transcurrido, tiempo restante estimado, tiempos del vídeo original, niveles de sospecha y revisión manual

## Próximos pasos

- Completar la firma y notarización con Apple Developer ID
- Permitir elegir el inicio y final del escaneo y la región del cielo
- Mejorar las estadísticas por lotes, el filtrado, la ordenación y la exportación de resúmenes
- Calibrar los umbrales con más muestras reales etiquetadas y publicar resultados de precision / recall
