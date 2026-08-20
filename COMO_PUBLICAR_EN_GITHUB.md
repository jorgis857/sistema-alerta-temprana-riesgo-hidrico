# Cómo publicar este proyecto en GitHub (paso a paso)

Esta carpeta ya está lista para convertirse en un repositorio de GitHub. Sigue estos pasos:

## 1. Crear el repositorio en GitHub

1. Entra a [github.com](https://github.com) e inicia sesión.
2. Haz clic en **New repository**.
3. Nombre sugerido: `sistema-alerta-temprana-riesgo-hidrico`.
4. Visibilidad: **Public** (debe ser público para poder compartirlo, según el enunciado).
5. **No** marques "Add a README" (ya tienes uno en esta carpeta).
6. Clic en **Create repository**.

## 2. Subir esta carpeta al repositorio

Abre una terminal dentro de esta carpeta (`sistema-alerta-temprana-riesgo-hidrico/`) y ejecuta:

```bash
git init
git add .
git commit -m "Entrega Challenge #1: Sistema de Alerta Temprana de Riesgo Hidrico"
git branch -M main
git remote add origin https://github.com/<TU-USUARIO>/sistema-alerta-temprana-riesgo-hidrico.git
git push -u origin main
```

Reemplaza `<TU-USUARIO>` por tu usuario real de GitHub (o el de la cuenta del equipo).

## 3. Publicar la Wiki de GitHub

El enunciado exige que la documentación esté publicada en una **Wiki** de GitHub/GitLab/Bitbucket (no solo como carpeta de código). Para replicar el contenido de `/wiki` en la Wiki nativa de GitHub:

1. En tu repositorio de GitHub, ve a la pestaña **Wiki** y haz clic en **Create the first page**.
2. Crea una página por cada archivo de la carpeta `wiki/` (puedes copiar y pegar el contenido Markdown tal cual):
   - `Home` ← contenido de `wiki/00-Home.md`
   - `1-Resumen-Motivacion` ← `wiki/01-Resumen-Motivacion.md`
   - `2-Solucion-Propuesta` ← `wiki/02-Solucion-Propuesta.md`
   - `3-Desarrollo-Modular` ← `wiki/03-Desarrollo-Modular.md`
   - `4-Modelo-de-Negocio` ← `wiki/04-Modelo-de-Negocio.md`
   - `5-Configuracion-Experimental-Resultados` ← `wiki/05-Configuracion-Experimental-Resultados.md`
   - `6-Autoevaluacion-Pruebas` ← `wiki/06-Autoevaluacion-Pruebas.md`
   - `7-Conclusiones-Trabajo-Futuro` ← `wiki/07-Conclusiones-Trabajo-Futuro.md`
   - `8-Uso-de-IA` ← `wiki/08-Uso-de-IA.md`
   - `9-Equipo-Roles` ← `wiki/09-Equipo-Roles.md`
3. **Alternativa más rápida (recomendada):** la Wiki de GitHub es en realidad otro repositorio git (`<repo>.wiki.git`). Puedes clonarlo vacío y copiar los archivos directamente:

   ```bash
   git clone https://github.com/<TU-USUARIO>/sistema-alerta-temprana-riesgo-hidrico.wiki.git
   cp wiki/*.md sistema-alerta-temprana-riesgo-hidrico.wiki/
   cp -r wiki/images sistema-alerta-temprana-riesgo-hidrico.wiki/
   cd sistema-alerta-temprana-riesgo-hidrico.wiki
   git add .
   git commit -m "Publicar Wiki tecnica del Challenge 1"
   git push
   ```

   (Debes crear al menos una página manualmente desde la interfaz web de GitHub la primera vez para que el repositorio `.wiki.git` exista antes de poder clonarlo.)

## 4. Compartir el repositorio

Según el enunciado, comparte el acceso/mención a **`@afbeltranp`** y sube el enlace público del repositorio (y el del video) a la actividad habilitada en MS Teams, junto con el `.zip` de archivos adicionales. **Solo se acepta una entrega por equipo.**

## 5. Checklist final antes de entregar

- [ ] Repositorio público en GitHub con todo el contenido de esta carpeta.
- [ ] Wiki de GitHub publicada con las 9 secciones + sección de uso de IA.
- [ ] README.md se ve bien renderizado en la portada del repo (revisar en el navegador).
- [ ] Roles y correos de los 3 integrantes completados en `wiki/09-Equipo-Roles.md`.
- [ ] Video grabado (máx. 5 min, los 3 integrantes con cámara encendida) siguiendo `video/GUION_VIDEO.md`, subido a Teams de forma reproducible sin descarga.
- [ ] Enlace del repositorio + enlace/archivo del video subidos a la actividad de MS Teams.
- [ ] Archivos adicionales comprimidos en `.zip` subidos al mismo enlace.
