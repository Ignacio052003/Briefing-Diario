"""Redacción del guion con Claude (API de Anthropic) y búsqueda web."""
import re
from pathlib import Path

import anthropic

import config

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
CIERRE_POR_DEFECTO = "¡Y hasta aquí tu resumen! Mucho ánimo con el día. ¡Y al ataque!"
RAFAGA = re.compile(r"^\s*\[\s*R[ÁA]FAGA\s*\]\s*$", re.I | re.M)


def fecha_larga(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(d) -> str:
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]}"


def _bloque(texto: str, nombre: str, siguientes: str) -> str:
    """Contenido de <nombre>, aunque falte su etiqueta de cierre."""
    m = re.search(rf"<{nombre}>(.*?)(?:</{nombre}>|{siguientes}|$)", texto, re.S)
    return m.group(1) if m else ""


def separar(texto: str) -> dict:
    limpiar = lambda t: re.sub(r"</?(sumario|cuerpo|cierre)>", "", t).strip()  # noqa: E731
    sumario = limpiar(_bloque(texto, "sumario", "<cuerpo>"))
    cuerpo = limpiar(_bloque(texto, "cuerpo", "<cierre>"))
    cierre = limpiar(_bloque(texto, "cierre", "(?!)"))
    if not cuerpo:  # sin etiquetas: todo es cuerpo
        cuerpo = limpiar(texto)
    secciones = [s.strip() for s in RAFAGA.split(cuerpo) if s.strip()]
    return {"sumario": sumario, "secciones": secciones, "cierre": cierre or CIERRE_POR_DEFECTO}


def _a_texto(guion: dict) -> str:
    cuerpo = "\n[RÁFAGA]\n".join(guion["secciones"])
    return (f"<sumario>\n{guion['sumario']}\n</sumario>\n<cuerpo>\n{cuerpo}\n</cuerpo>\n"
            f"<cierre>\n{guion['cierre']}\n</cierre>")


def _palabras(guion: dict) -> int:
    return sum(len(t.split()) for t in [guion["sumario"], guion["cierre"], *guion["secciones"]])


def revisar(cliente, borrador: dict) -> dict:
    """Segunda pasada: un 'editor' recorta datos y hace el texto más hablado.
    Si algo sale raro, se queda el borrador original."""
    plantilla = (Path(__file__).parent.parent / "prompts" / "editor.md").read_text(encoding="utf-8")
    sistema = plantilla.replace("{palabras_min}", str(config.PALABRAS_OBJETIVO[0])) \
                       .replace("{palabras_max}", str(config.PALABRAS_OBJETIVO[1]))
    try:
        resp = cliente.messages.create(
            model=config.MODELO_IA, max_tokens=8000, system=sistema,
            messages=[{"role": "user", "content": "Este es el guion de hoy:\n\n" + _a_texto(borrador)}],
        )
        revisado = separar("".join(b.text for b in resp.content if b.type == "text"))
    except Exception as e:  # noqa: BLE001
        print(f"La revisión del editor ha fallado ({e}); se usa el borrador.")
        return borrador
    antes, despues = _palabras(borrador), _palabras(revisado)
    print(f"Editor: {antes} → {despues} palabras, {len(revisado['secciones'])} secciones. "
          f"Tokens: {resp.usage.input_tokens} in / {resp.usage.output_tokens} out")
    if (len(revisado["secciones"]) < max(3, len(borrador["secciones"]) - 1)
            or despues < 0.55 * antes or not revisado["sumario"]):
        print("La versión del editor no pasa los controles; se usa el borrador.")
        return borrador
    return revisado


def escribir_guion(ahora, noticias: str, mercados: str) -> dict:
    """Devuelve {"saludo", "sumario", "secciones", "cierre"} listos para locutar."""
    plantilla = (Path(__file__).parent.parent / "prompts" / "guion.md").read_text(encoding="utf-8")
    sistema = plantilla.replace("{palabras_min}", str(config.PALABRAS_OBJETIVO[0])) \
                       .replace("{palabras_max}", str(config.PALABRAS_OBJETIVO[1]))

    nota_lunes = ("\nHoy es lunes: incluye lo relevante del fin de semana; "
                  "los cierres de mercado son los del viernes.\n") if ahora.weekday() == 0 else ""

    peticion = f"""Hoy es {fecha_larga(ahora)}; son las {ahora:%H:%M} en Madrid y el oyente lo escuchará hacia las 7:00.{nota_lunes}

## Datos de mercado (Yahoo Finance)
{mercados}

## Titulares recientes de las fuentes
{noticias}

Elige las historias, usa la búsqueda web solo para ampliar las que vayas a contar y para la agenda de hoy,
y escribe el sumario, el cuerpo y el cierre siguiendo tus instrucciones."""

    cliente = anthropic.Anthropic()
    herramientas = [{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": config.MAX_BUSQUEDAS_WEB,
        "user_location": {"type": "approximate", "city": "Madrid", "country": "ES",
                          "timezone": config.ZONA_HORARIA},
    }]
    mensajes = [{"role": "user", "content": peticion}]

    # La respuesta puede llegar en varias tandas (la API pausa los turnos largos de
    # búsqueda): se junta el texto de todas.
    textos, entrada, salida = [], 0, 0
    for _ in range(6):
        resp = cliente.messages.create(
            model=config.MODELO_IA, max_tokens=16000, system=sistema,
            messages=mensajes, tools=herramientas,
        )
        textos.append("".join(b.text for b in resp.content if b.type == "text"))
        entrada += resp.usage.input_tokens
        salida += resp.usage.output_tokens
        if resp.stop_reason != "pause_turn":
            break
        mensajes.append({"role": "assistant", "content": resp.content})

    texto = "".join(textos)
    guion = separar(texto)
    palabras = _palabras(guion)
    print(f"Fin de la respuesta: {resp.stop_reason}. Borrador: {palabras} palabras, "
          f"{len(guion['secciones'])} secciones. Tokens: {entrada} in / {salida} out")
    if palabras < 300:
        raise RuntimeError(f"Guion demasiado corto ({palabras} palabras). Respuesta:\n{texto[:2000]}")

    if getattr(config, "REVISION_EDITOR", False):
        guion = revisar(cliente, guion)

    guion["saludo"] = config.SALUDO.format(fecha=fecha_corta(ahora))
    return guion
