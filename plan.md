Instrucciones para desarrollar el Dashboard Web del IDF Departamental

Quiero que desarrolles una versión web interactiva del Índice de Desempeño Fiscal (IDF) Departamental, utilizando como base los archivos que te proporcionaré. El proyecto debe mantener la estructura visual, colores, estilo y experiencia general del HTML de referencia, pero debe adaptar todos los datos y funcionalidades al IDF Departamental.

Antes de desarrollar

No comiences inmediatamente a escribir código.

Primero:

Revisa el Excel.
Localiza la sección Dashboard IDF.
Identifica todas las visualizaciones existentes.
Identifica todos los filtros.
Analiza las columnas y códigos.
Revisa el HTML de referencia.
Identifica qué componentes del HTML corresponden a cada sección del Dashboard IDF.
Revisa los archivos TopoJSON/GeoJSON.
Revisa el JSON de códigos departamentales.
Define cómo se relacionarán los datos con el mapa.
Define qué JSON generará Python.
Define la arquitectura final.
Finalmente comienza el desarrollo.

El objetivo no es simplemente reproducir el HTML municipal. El objetivo es construir el Dashboard Web del IDF Departamental utilizando la misma lógica visual, pero con los datos reales y las relaciones geográficas del Excel departamental.

1. Archivos proporcionados

Para desarrollar el proyecto tendrás disponibles:

Archivo Excel: contiene los datos oficiales del IDF Departamental.
Archivo HTML de referencia: contiene una implementación visual del IDF Municipal. Este HTML debe utilizarse principalmente como referencia de diseño, estructura, distribución, colores, componentes y experiencia de usuario.
Archivos GeoJSON/TopoJSON: contienen las geometrías necesarias para construir el mapa interactivo de Colombia y sus departamentos.
JSON de códigos departamentales: contiene la correspondencia de los códigos de los departamentos que permitirá relacionar los datos con las geometrías del mapa.
Mockup/enlace de referencia: [AGREGAR ENLACE AQUÍ, SI APLICA].
Importante sobre el HTML de referencia

El HTML proporcionado NO representa los datos que debe utilizar la aplicación final, ya que corresponde al IDF Municipal.

Debe utilizarse únicamente como referencia para:

estructura;
colores;
distribución;
colores;
tipografía;
tarjetas;
filtros;
gráficas;
mapa;
navegación;
jerarquía visual;
interacciones;
experiencia de usuario.

La aplicación final debe ser IDF Departamental, por lo que todos los datos, códigos, nombres, filtros y visualizaciones deben corresponder exclusivamente a la información departamental disponible en el Excel.

2. Analizar primero el Excel

Antes de comenzar a desarrollar la aplicación, revisa cuidadosamente el archivo Excel.

Existe una sección/hoja denominada:

Dashboard IDF

Esta sección es especialmente importante porque contiene la información que debe ser representada visualmente en la aplicación web.

Debes analizar:

Las hojas existentes.
La hoja Dashboard IDF.
Las tablas y datos que aparecen en ella.
Los años disponibles.
Los códigos departamentales.
Las variables utilizadas.
Los componentes del IDF.
Los indicadores.
Los rangos de desempeño.
Las categorías.
Los datos utilizados para las gráficas.
Los filtros existentes.
Regla fundamental

Los datos que aparecen en el Dashboard IDF del Excel son la referencia principal para determinar qué información debe visualizarse en la aplicación web.

No inventes datos.

No reemplaces los datos por valores ficticios.

No utilices los datos municipales del HTML de referencia.

Debes tomar los datos correspondientes al IDF Departamental directamente del Excel.

3. Relación entre el Excel y el HTML de referencia

El HTML de referencia ya contiene muchas de las secciones que necesitamos visualmente.

Por ejemplo, el HTML del IDF Municipal contiene una sección de:

Evolución histórica del IDF

Debes comprobar que en la hoja Dashboard IDF del Excel también existe información correspondiente a la evolución histórica del IDF.

Si existe, entonces debes utilizar los datos departamentales del Excel para construir esa misma visualización en la versión web.

Este mismo procedimiento debe aplicarse a todas las demás secciones.

Es decir:

HTML de referencia
↓
Identificar sección visual
↓
Buscar los datos equivalentes
↓
Dashboard IDF del Excel
↓
Utilizar datos departamentales
↓
Construir visualización con D3.js

Por ejemplo:

HTML Municipal
│
├── Evolución histórica del IDF
├── Componente de resultados
├── Distribución por rangos
├── Top 10 departamentos
├── Componente de gestión
├── Promedio IDF
└── Otros indicadores
│
▼
Buscar cada sección en:
"Dashboard IDF" del Excel
│
▼
Construir versión DEPARTAMENTAL

No copies los valores del HTML. Copia la lógica visual y reemplaza completamente la información por los datos del Excel Departamental.

4. Visualizaciones

Todas las visualizaciones deben desarrollarse utilizando principalmente D3.js.

D3.js debe encargarse de:

Gráficos.
Escalas.
Ejes.
Tooltips.
Interacciones.
Transiciones.
Filtrado.
Mapa.
Colores dinámicos.
Actualización de visualizaciones.

El objetivo es que la aplicación sea realmente interactiva y no simplemente una imagen estática de las gráficas.

5. Mapa interactivo

Uno de los componentes más importantes será el mapa interactivo de departamentos de Colombia.

Para construirlo debes utilizar los archivos TopoJSON/GeoJSON proporcionados.

Cada departamento está asociado a un código de cinco dígitos.

Ese código debe utilizarse como identificador principal para relacionar:

Datos del Excel
↕
Código departamental
↕
JSON de códigos
↕
TopoJSON / GeoJSON
↕
Geometría del departamento

No debes depender únicamente del nombre del departamento para realizar la relación.

Comportamiento esperado

Cuando el usuario pase el cursor:

Mostrar información contextual.
Resaltar el departamento.

Cuando el usuario haga clic:

Click en departamento
↓
Obtener código de 5 dígitos
↓
Buscar datos correspondientes
↓
Actualizar filtros
↓
Actualizar gráficas
↓
Actualizar indicadores

Por ejemplo:

Usuario selecciona Antioquia
↓
Código: XXXXX
↓
Buscar registros con ese código
↓
Mostrar información de Antioquia

Todas las visualizaciones relacionadas deben actualizarse dinámicamente.

6. Filtros

Los filtros que aparecen en el diseño deben ser funcionales.

No deben ser elementos únicamente decorativos.

Si existe un filtro de:

Año.
Departamento.
Componente.
Categoría.
Rango.
Tipología.
Etc.

debe modificar realmente los datos utilizados por las visualizaciones correspondientes.

Por ejemplo:

Año: 2024
Departamento: Antioquia
↓
Filtrar datos
↓
Actualizar:

- IDF
- evolución
- componentes
- rangos
- gráficas
- indicadores

Cuando el usuario seleccione un departamento desde el mapa, esa selección también debe sincronizarse con los filtros.

7. Preparación de los datos

El Excel es la fuente original.

No quiero que la aplicación dependa directamente de cargar un Excel gigante desde el navegador.

Para ello, desarrolla un script en Python que permita procesar el Excel y generar los archivos de datos optimizados para la aplicación.

El proceso será:

Excel original
↓
Python
↓
Analizar / organizar / transformar
↓
JSON optimizados
↓
Aplicación Web

El script no debe alterar los valores originales, únicamente transformar su estructura para que sea eficiente para el frontend.

Dependiendo del tamaño y estructura del Excel, puedes generar diferentes archivos, por ejemplo:

data/
├── departamentos.json
├── idf.json
├── historico.json
├── componentes.json
├── rangos.json
└── distribuciones.json

O dividirlos por año si resulta más eficiente:

data/
├── 2020.json
├── 2021.json
├── 2022.json
├── 2023.json
└── 2024.json

No decidas arbitrariamente la estructura. Primero analiza el Excel y determina cuál es la forma más eficiente de organizar los datos.

8. Arquitectura del proyecto

La aplicación debe quedar preparada para funcionar mediante GitHub Pages.

Una estructura inicial podría ser:

idf-departamental/
│
├── index.html
│
├── css/
│ ├── styles.css
│ └── components.css
│
├── js/
│ ├── app.js
│ ├── data.js
│ ├── mapa.js
│ ├── graficas.js
│ └── filtros.js
│
├── data/
│ └── archivos JSON
│
├── geo/
│ ├── archivos TopoJSON
│ ├── archivos GeoJSON
│ └── codigos.json
│
├── scripts/
│ └── procesar_excel.py
│
└── assets/

Puedes modificar esta estructura si existe una alternativa mejor, pero debe existir una separación clara entre:

Datos.
Procesamiento.
Mapa.
Visualizaciones.
Interacciones.
Estilos. 9. Flujo general de funcionamiento

La arquitectura final debe funcionar conceptualmente así:

              EXCEL ORIGINAL
                    │
                    ▼
             Python Script
                    │
                    ▼
             JSON optimizados
                    │
                    ▼
              GitHub Pages
                    │
                    ▼
             Aplicación Web
                    │
          ┌─────────┴─────────┐
          │                   │
       D3.js              TopoJSON
          │                   │
          │              Mapa Colombia
          │                   │
          └─────────┬─────────┘
                    │
             Código 5 dígitos
                    │
                    ▼
             Datos filtrados
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        KPIs    Gráficas    Rangos

10. Diseño visual

El HTML de referencia debe utilizarse para mantener la identidad visual.

Mantén, siempre que sea posible:

Paleta de colores.
Estructura.
Espaciado.
Tipografías.
Estilo de tarjetas.
Jerarquía.
Componentes.
Distribución.
Estilo de los gráficos.

Sin embargo, adapta los contenidos al IDF Departamental.

La idea no es crear un dashboard completamente diferente, sino tomar la solución visual existente para IDF Municipal y transformarla correctamente en su versión Departamental.

11. Principio fundamental del proyecto

La aplicación debe responder a esta lógica:

El Excel determina qué datos existen y qué información debe visualizarse. El HTML de referencia determina principalmente cómo debe visualizarse. D3.js se encarga de construir las visualizaciones y las interacciones. Los códigos de cinco dígitos conectan los datos departamentales con las geometrías del mapa.

Por lo tanto:

Excel = fuente de datos

Dashboard IDF del Excel = referencia de contenido

HTML Municipal = referencia visual

TopoJSON/GeoJSON = geometría

JSON de códigos = relación geográfica

Python = preparación de datos

D3.js = visualización e interacción

GitHub Pages = publicación de la aplicación
