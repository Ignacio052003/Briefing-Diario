"""Redacción del guion con Claude (API de Anthropic) y búsqueda web."""
import re
from pathlib import Path

import anthropic

import config

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
CIERRE_POR_DEFECTO = "¡Aquí tienes tu resumen! Mucho ánimo con el día. ¡Y al ataque!"


def fecha_larga(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def separar(texto: str) -> tuple[str, str]:
    """Saca el cuerpo y el cierre, aunque falte alguna etiqueta de cierre."""
    cuerpo = re.search(r"<cuerpo>(.*?)(?:</cuerpo>|<cierre>|$)", texto, re.S)
    cierre = re.search(r"<cierre>(.*?)(?:</cierre>|$)", texto, re.S)
    cuerpo = cuerpo.group(1) if cuerpo else texto.split("<cierre>")[0]
    cierre = cierre.group(1) if cierre else ""
    limpiar = lambda t: re.sub(r"</?(cuerpo|cierre)>", "", t).strip()  # noqa: E731
    return limpiar(cuerpo), limpiar(cierre) or CIERRE_POR_DEFECTO


def escribir_guion(ahora, noticias: str, mercados: str) -> dict:
    """Devuelve {"saludo", "cuerpo", "cierre"} listos para locutar."""
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
y escribe el cuerpo y el cierre siguiendo tus instrucciones."""

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
    cuerpo, cierre = separar(texto)
    print(f"Fin de la respuesta: {resp.stop_reason}. Guion: {len(cuerpo.split())} palabras. "
          f"Tokens: {entrada} in / {salida} out")
    if len(cuerpo.split()) < 300:
        raise RuntimeError(f"Guion demasiado corto ({len(cuerpo.split())} palabras). Respuesta:\n{texto[:2000]}")

    return {
        "saludo": config.SALUDO.format(fecha=fecha_corta(ahora)),
        "cuerpo": cuerpo,
        "cierre": cierre,
    }
