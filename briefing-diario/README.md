# Mi Briefing Diario

Un podcast privado que se genera solo cada mañana de lunes a viernes: noticias del mundo, Europa y España, y después mercados, bonos, macro, empresas y la agenda del día. Dura entre 12 y 15 minutos y aparece en la app Podcasts de Apple como un programa más, así que tu automatización de CarPlay lo reproduce al arrancar el coche.

## Cómo funciona

Cada día laborable, sobre las 6:15 (5:15 en horario de invierno), GitHub ejecuta el programa en la nube, gratis y sin que tu ordenador tenga que estar encendido. El programa hace cuatro cosas:

1. Recoge los titulares de unas 15 fuentes (Expansión, FT, Cinco Días, El País, Bloomberg, BBC, Politico…) y los precios de los principales índices, bonos, divisas y materias primas.
2. Se los pasa a Claude, que busca en la web lo que falta (Bund, bono español, prima de riesgo, Asia, agenda del día) y redacta el guion siguiendo la estructura de `prompts/guion.md`.
3. Convierte el guion en audio con una voz neuronal en español de España.
4. Publica el MP3 y actualiza el feed del podcast, del que se guardan los últimos 10 episodios.

Junto a cada audio se guarda también el guion en texto (`briefing-AAAA-MM-DD.txt`), por si quieres leerlo o comprobar algún dato.

---

## Puesta en marcha (unos 30 minutos, mejor desde un ordenador)

### 1. Crea una cuenta de la API de Claude y una clave

1. Entra en **console.anthropic.com** y crea una cuenta. Es distinta de tu suscripción a Claude.ai.
2. En **Billing**, añade crédito. Con 10 € tienes para más de un mes. Te recomiendo fijar también un límite de gasto mensual (por ejemplo, 15 €) para no llevarte sorpresas.
3. En **API Keys**, pulsa **Create Key**, ponle un nombre (por ejemplo, "briefing") y copia la clave, que empieza por `sk-ant-`. Solo se muestra una vez.

### 2. Crea el repositorio en GitHub

1. Si no tienes cuenta, créala en **github.com** (gratis).
2. Pulsa **+ → New repository**. Nombre: `briefing`. Visibilidad: **Public** (lo explico en "Privacidad", más abajo). Pulsa **Create repository**.
3. En la página del repositorio vacío, pulsa **uploading an existing file**.
4. Descomprime el zip y arrastra **todo su contenido** a la ventana del navegador: los archivos y las carpetas `briefing`, `prompts`, `assets` y `.github`.
   - En Mac, la carpeta `.github` está oculta. En el Finder, pulsa **Cmd + Shift + .** para verla.
   - Si no consigues subirla, mira "Si la carpeta .github no se sube", al final de esta guía.
5. Pulsa **Commit changes**.

### 3. Guarda la clave de la API en GitHub

En el repositorio, ve a **Settings → Secrets and variables → Actions → New repository secret**.

- Name: `ANTHROPIC_API_KEY`
- Secret: la clave `sk-ant-…` que copiaste.

Pulsa **Add secret**. La clave queda cifrada y nadie, ni siquiera tú, puede volver a verla.

### 4. Genera el primer episodio

1. Ve a la pestaña **Actions**. Si te pide activar los workflows, acepta.
2. En la izquierda, pulsa **Briefing diario** y después **Run workflow → Run workflow**.
3. Tarda entre 3 y 6 minutos. Si termina con un ✓ verde, está todo bien. Si sale una ✗ roja, abre la ejecución y mira el paso que ha fallado (consulta "Problemas frecuentes").

### 5. Activa la publicación (GitHub Pages)

Este paso solo puede hacerse después del primer episodio, porque es entonces cuando se crea la rama `gh-pages`.

1. Ve a **Settings → Pages**.
2. En **Source**, elige **Deploy from a branch**. En **Branch**, elige **gh-pages** y **/ (root)**. Pulsa **Save**.
3. Espera uno o dos minutos y abre en el navegador:
   `https://TU-USUARIO.github.io/briefing/feed.xml`
   Pon tu nombre de usuario de GitHub en minúsculas. Si ves un texto XML con el episodio, ya está publicado.

### 6. Suscríbete en la app Podcasts del iPhone

1. Abre **Podcasts → Biblioteca**.
2. Toca **⋯** (arriba a la derecha) y luego **Seguir un programa por URL…**
3. Pega la URL del feed y pulsa **Seguir**. Aparecerá "Mi Briefing Diario" con su portada.
4. En los ajustes del programa, activa la **descarga automática de episodios nuevos**. Así el audio ya está en el móvil cuando subes al coche y no depende de la cobertura.

### 7. Cambia tu automatización de CarPlay

En **Atajos → Automatización**, abre la que creaste, toca **La Primera de Expansión** en la acción **Play** y elige **Mi Briefing Diario**. La condición de la hora sigue funcionando igual.

---

## Personalizarlo

Puedes editar cualquier archivo directamente en GitHub: ábrelo, pulsa el lápiz ✏️ y luego **Commit changes**. El cambio se aplica desde el siguiente episodio.

- **`prompts/guion.md`** controla qué se cuenta, en qué orden, el criterio editorial y el tono. Es el archivo más importante. Si quieres más peso en algún tema, menos política, que siga ciertas empresas o sectores, o un tono más analítico, cámbialo aquí con lenguaje normal.
- **`config.py`** contiene las fuentes de noticias, los activos de mercado, la duración, la voz y el modelo de IA.
- **`.github/workflows/briefing.yml`** fija la hora y los días de ejecución (línea `cron`, en hora UTC).

**Voz.** Por defecto se usa una voz gratuita de Microsoft (`es-ES-AlvaroNeural`; hay una femenina, `es-ES-ElviraNeural`). Si quieres una voz más natural, crea una clave en **platform.openai.com**, añádela como secreto `OPENAI_API_KEY` en GitHub y cambia `MOTOR_VOZ = "openai"` en `config.py`. Cuesta unos 15 céntimos por episodio.

**Modelo.** `claude-sonnet-5-5` ofrece una buena relación entre calidad y precio. Si quieres el mejor análisis posible, cambia a `claude-opus-5-5`, que cuesta aproximadamente el doble.

## Costes

Con Sonnet, cada episodio cuesta entre 0,20 y 0,35 € (tokens más búsquedas web). Eso supone unos 5-7 € al mes de lunes a viernes. GitHub y la voz por defecto son gratis.

---

## Lo que conviene saber (limitaciones honestas)

- **La calidad depende de las fuentes.** El FT y Expansión solo ofrecen titulares y entradillas en sus RSS. La búsqueda web compensa en parte, pero no es lo mismo que leer el artículo completo.
- **La IA puede equivocarse.** El guion le prohíbe inventar cifras, y los precios de índices, bonos estadounidenses y divisas vienen de datos reales de Yahoo Finance. En cambio, el Bund, el bono español y la prima de riesgo salen de la búsqueda web, así que tienen más margen de error. Sirve para informarte, no para decidir una operación; para eso, contrasta con la fuente.
- **Actualización en el iPhone.** Los programas seguidos por URL los actualiza el propio móvil y a veces tarda. Por eso el episodio se genera con más de una hora de margen. Si algún día no aparece, abre Podcasts y desliza hacia abajo en el programa para refrescarlo.
- **GitHub puede retrasar** las ejecuciones programadas entre unos minutos y, en días de mucha carga, algo más.
- **La voz gratuita** es un servicio no oficial de Microsoft. Si algún día deja de funcionar, cambia a OpenAI como se explica arriba.

### Privacidad

GitHub Pages gratuito exige que el repositorio sea público, así que técnicamente cualquiera con la URL podría escuchar el briefing. En la práctica no se puede encontrar: el feed está marcado para no aparecer en el directorio de Apple Podcasts y nadie conoce la dirección. Es para uso personal: no compartas la URL ni lo distribuyas, porque se basa en contenido de medios con derechos. No hay nada personal en el repositorio, y tu clave de la API está cifrada en los secretos de GitHub.

---

## Problemas frecuentes

**Falla "Generar briefing" con un error de autenticación o `401`.** El secreto `ANTHROPIC_API_KEY` está mal copiado o no tiene ese nombre exacto.

**Error de crédito o `credit balance is too low`.** Tienes que añadir saldo en console.anthropic.com → Billing.

**Falla "Publicar" con `403` o `permission denied`.** Ve a Settings → Actions → General → Workflow permissions, marca **Read and write permissions** y guarda.

**En el log aparece "Fuentes que no han respondido: …".** Es normal que alguna fuente falle algún día: el programa la salta y sigue. Si una falla siempre, quítala o cámbiala en `config.py`.

**El feed da error 404.** Revisa el paso 5 y que la URL esté en minúsculas y con el nombre correcto del repositorio. Si tu repositorio se llama `TU-USUARIO.github.io`, la URL no lleva `/briefing`.

**Si la carpeta .github no se sube.** En el repositorio, pulsa **Add file → Create new file**, escribe como nombre `.github/workflows/briefing.yml` (las barras crean las carpetas), pega dentro el contenido de ese archivo del zip y pulsa **Commit changes**.

## Probarlo en tu ordenador (opcional)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --solo-guion          # imprime el guion de hoy, sin generar audio
python main.py --site site           # genera audio y feed en la carpeta site/ (necesita ffmpeg)
```
