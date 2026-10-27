"""Redacción del guion con Claude (API de Anthropic) y búsqueda web."""
import re
from pathlib import Path

import anthropic

import config

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def escribir_guion(ahora, noticias: str, mercados: str) -> str:
    plantilla = (Path(__file__).parent.parent / "prompts" / "guion.md").read_text(encoding="utf-8")
    sistema = plantilla.replace("{palabras_min}", str(config.PALABRAS_OBJETIVO[0])) \
                       .replace("{palabras_max}", str(config.PALABRAS_OBJETIVO[1]))

    nota_lunes = ("\nHoy es lunes: incluye lo relevante ocurrido durante el fin de semana "
                  "y los cierres de mercado son los del viernes.\n") if ahora.weekday() == 0 else ""

    peticion = f"""Hoy es {fecha_larga(ahora)}; son las {ahora:%H:%M} en Madrid.{nota_lunes}

## Datos de mercado (Yahoo Finance)
{mercados}

## Titulares recientes de las fuentes
{noticias}

Prepara el briefing de hoy siguiendo tus instrucciones. Usa la búsqueda web para completar
lo que falte (Bund, bono español y prima de riesgo, Asia esta mañana, agenda del día) y para
ampliar las 3-5 noticias más importantes."""

    cliente = anthropic.Anthropic()
    herramientas = [{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": config.MAX_BUSQUEDAS_WEB,
        "user_location": {"type": "approximate", "city": "Madrid", "country": "ES",
                          "timezone": config.ZONA_HORARIA},
    }]
    mensajes = [{"role": "user", "content": peticion}]

    for _ in range(6):  # la API puede pausar turnos largos de búsqueda
        resp = cliente.messages.create(
            model=config.MODELO_IA, max_tokens=12000, system=sistema,
            messages=mensajes, tools=herramientas,
        )
        if resp.stop_reason != "pause_turn":
            break
        mensajes.append({"role": "assistant", "content": resp.content})

    texto = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"<guion>(.*?)</guion>", texto, re.S)
    guion = (m.group(1) if m else texto).strip()
    if len(guion.split()) < 300:
        raise RuntimeError(f"Guion demasiado corto ({len(guion.split())} palabras). Respuesta:\n{texto[:2000]}")
    print(f"Guion: {len(guion.split())} palabras. Tokens: {resp.usage.input_tokens} in / {resp.usage.output_tokens} out")
    return guion
