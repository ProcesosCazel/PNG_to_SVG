# PNG to SVG Converter

Aplicación de escritorio para Windows que convierte imágenes **PNG, JPG y JPEG** a archivos vectoriales **SVG** mediante una interfaz gráfica simple e intuitiva.

El proyecto fue desarrollado para facilitar su uso por personal técnico, evitando herramientas de diseño especializadas y permitiendo realizar la conversión mediante unos pocos clics.

## Características

- Conversión de **PNG, JPG y JPEG a SVG**.
- Interfaz gráfica sencilla para usuarios no técnicos.
- Vista previa de la imagen antes de convertir.
- Cuatro niveles de calidad:
  - Rápida
  - Normal
  - Alta
  - Súper alta
- Opción **Súper alta** para obtener contornos con mayor nitidez y detalle.
- Generación automática del SVG en la misma ubicación de la imagen.
- Botón para abrir el SVG generado.
- Botón para abrir la carpeta de salida.
- Pantalla de carga durante el inicio de la aplicación.
- Protección para evitar múltiples instancias abiertas al mismo tiempo.
- Procesamiento optimizado para equipos Windows de uso industrial/corporativo.
- No requiere `scikit-image`.
- Compatible con empaquetado mediante **PyInstaller**.

## Captura del flujo de trabajo

```text
Seleccionar imagen
      ↓
Vista previa
      ↓
Seleccionar calidad
      ↓
Convertir a SVG
      ↓
Abrir SVG / Abrir carpeta
```

## Formatos compatibles

### Entrada

```text
.png
.jpg
.jpeg
```

### Salida

```text
.svg
```

## Requisitos para desarrollo

Para ejecutar o compilar el proyecto desde código fuente:

- Windows 10 / 11
- Python 3.14 de 64 bits
- pip

Dependencias principales:

```text
Pillow
NumPy
PyInstaller
```

Las versiones utilizadas por el proyecto están definidas en:

```text
requirements.txt
```

## Estructura del proyecto

```text
PNG_to_SVG/
│
├── app.py
├── launcher.py
├── vectorizer.py
├── splash.png
├── requirements.txt
├── build_exe.bat
├── diagnostico.bat
├── INSTRUCCIONES.txt
└── README.md
```

### Archivos principales

**`app.py`**  
Contiene la interfaz gráfica principal de la aplicación.

**`launcher.py`**  
Gestiona el arranque de la aplicación, la pantalla de carga y el control de una sola instancia.

**`vectorizer.py`**  
Contiene el motor de procesamiento y conversión de la imagen a SVG.

**`splash.png`**  
Imagen utilizada para la pantalla de carga.

**`requirements.txt`**  
Lista de dependencias necesarias para ejecutar y compilar el proyecto.

**`build_exe.bat`**  
Automatiza la instalación de dependencias y la creación del ejecutable con PyInstaller.

**`diagnostico.bat`**  
Permite ejecutar la aplicación con consola visible para detectar errores.

**`INSTRUCCIONES.txt`**  
Instrucciones adicionales para compilación y distribución.

## Ejecución desde Python

Abrir PowerShell dentro de la carpeta del proyecto:

```powershell
cd "RUTA\DEL\PROYECTO"
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Ejecutar:

```powershell
python launcher.py
```

## Crear el ejecutable de Windows

La forma recomendada es utilizar:

```text
build_exe.bat
```

### Procedimiento

1. Abrir la carpeta del proyecto.
2. Ejecutar `build_exe.bat`.
3. Esperar a que termine la compilación.
4. El programa generado estará dentro de:

```text
dist\ConvertidorImagenSVG\
```

El ejecutable principal será:

```text
ConvertidorImagenSVG.exe
```

## Distribución

La compilación recomendada utiliza PyInstaller en modo **ONEDIR**.

Por esta razón, para instalar o copiar la aplicación en otra computadora se debe copiar **toda la carpeta**:

```text
dist\ConvertidorImagenSVG\
```

No se debe copiar únicamente el archivo `.exe`.

La computadora del usuario final **no necesita tener Python instalado**.

## Uso de la aplicación

1. Abrir `ConvertidorImagenSVG.exe`.
2. Esperar a que desaparezca la pantalla de carga.
3. Presionar **Seleccionar imagen**.
4. Elegir un archivo PNG, JPG o JPEG.
5. Revisar la vista previa.
6. Elegir el nivel de calidad.
7. Presionar **Convertir a SVG**.
8. Al terminar:
   - abrir el SVG, o
   - abrir la carpeta donde fue guardado.

## Niveles de calidad

| Calidad | Velocidad | Detalle |
|---|---:|---:|
| Rápida | Muy alta | Básico |
| Normal | Alta | Medio |
| Alta | Media | Alto |
| Súper alta | Menor | Máximo |

La opción **Súper alta** utiliza una resolución interna mayor y menor simplificación de los contornos. Puede tardar varios segundos adicionales dependiendo del tamaño y complejidad de la imagen.

## Consideraciones sobre la vectorización

El programa está orientado principalmente a:

- logotipos,
- símbolos,
- pictogramas,
- imágenes de alto contraste,
- figuras monocromáticas,
- siluetas,
- gráficos con bordes definidos.

El resultado SVG se genera a partir de los contornos detectados en la imagen.

Para obtener mejores resultados se recomienda utilizar imágenes con:

- buen contraste,
- fondo limpio,
- bordes definidos,
- buena resolución.

## Diagnóstico de errores

Si la aplicación no abre o presenta un problema durante desarrollo, ejecutar:

```text
diagnostico.bat
```

Esto iniciará la aplicación mostrando la consola de Python para poder identificar el error.

## Archivos que no deben subirse a Git

El archivo `.gitignore` excluye automáticamente elementos como:

```text
build/
dist/
__pycache__/
*.spec
*.exe
```

Estos archivos son generados durante la compilación y no forman parte del código fuente del proyecto.

## Repositorio

```text
ProcesosCazel/PNG_to_SVG
```

## Versión

**v4.0**

Estado: versión funcional validada.

## Tecnologías utilizadas

- Python
- Tkinter
- Pillow
- NumPy
- PyInstaller
- SVG

## Autor / Organización

---

# Autor:

## Ing. José Antonio Guzmán Trujillo
### Becario de Procesos | Industrias Cazel
**tecnicosprocesos@cazel.mx**

---

**PNG to SVG Converter v4.0**
Proyecto desarrollado como herramienta de apoyo para procesos técnicos y de manufactura.
