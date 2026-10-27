"""Conversión del guion a audio MP3."""
import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

import config


def _preparar(texto: str) -> str:
    texto = f" {texto} "
    for original, dicho in config.PRONUNCIACION.items():
        texto = texto.replace(original, dicho)
    texto = re.sub(r"[*#_`]", "", texto)          # restos de markdown
    return re.sub(r"[ \t]+", " ", texto).strip()


def _trozos(texto: str, max_chars: int) -> list[str]:
    trozos, actual = [], ""
    for parrafo in [p.strip() for p in texto.split("\n") if p.strip()]:
        if len(actual) + len(parrafo) + 1 > max_chars and actual:
            trozos.append(actual)
            actual = ""
        if len(parrafo) > max_chars:  # párrafo enorme: cortar por frases
            for frase in re.split(r"(?<=[.!?])\s+", parrafo):
                if len(actual) + len(frase) + 1 > max_chars and actual:
                    trozos.append(actual)
                    actual = ""
                actual += frase + " "
        else:
            actual += parrafo + "\n"
    if actual.strip():
        trozos.append(actual)
    return trozos


def _unir(partes: list[Path], destino: Path) -> None:
    lista = destino.with_suffix(".txt")
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in partes), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lista), "-ac", "1", "-b:a", "64k", str(destino)], check=True)
    lista.unlink()


def _edge(trozos: list[str], carpeta: Path) -> list[Path]:
    import edge_tts

    async def generar():
        rutas = []
        for i, t in enumerate(trozos):
            ruta = carpeta / f"p{i:03}.mp3"
            await edge_tts.Communicate(t, config.VOZ_EDGE, rate=config.VELOCIDAD_EDGE).save(str(ruta))
            rutas.append(ruta)
        return rutas

    return asyncio.run(generar())


def _openai(trozos: list[str], carpeta: Path) -> list[Path]:
    from openai import OpenAI

    cliente, rutas = OpenAI(), []
    for i, t in enumerate(trozos):
        ruta = carpeta / f"p{i:03}.mp3"
        with cliente.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice=config.VOZ_OPENAI, input=t,
            instructions=config.INSTRUCCIONES_VOZ_OPENAI, response_format="mp3",
        ) as r:
            r.stream_to_file(ruta)
        rutas.append(ruta)
    return rutas


def locutar(guion: str, destino: Path) -> None:
    texto = _preparar(guion)
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        if config.MOTOR_VOZ == "openai":
            partes = _openai(_trozos(texto, 3500), carpeta)
        else:
            partes = _edge(_trozos(texto, 4000), carpeta)
        _unir(partes, destino)


def duracion_segundos(ruta: Path) -> int:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(ruta)], capture_output=True, text=True, check=True)
    return int(float(salida.stdout.strip()))
