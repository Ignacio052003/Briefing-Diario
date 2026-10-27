"""Conversión del guion a audio MP3, con música de entrada y de salida."""
import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

import config

RAIZ = Path(__file__).parent.parent


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


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def duracion_segundos(ruta: Path) -> float:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(ruta)], capture_output=True, text=True, check=True)
    return float(salida.stdout.strip())


def _a_wav(entradas: list[Path], destino: Path) -> None:
    """Une uno o varios audios en un WAV estéreo a 44,1 kHz (formato común para mezclar)."""
    lista = destino.with_suffix(".lista.txt")
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in entradas), encoding="utf-8")
    _ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-ar", "44100", "-ac", "2", str(destino))


# --- Motores de voz -----------------------------------------------------------

def _edge(trozos: list[str], carpeta: Path, prefijo: str, rate: str, pitch: str = "+0Hz") -> list[Path]:
    import edge_tts

    async def generar():
        rutas = []
        for i, t in enumerate(trozos):
            ruta = carpeta / f"{prefijo}{i:03}.mp3"
            await edge_tts.Communicate(t, config.VOZ_EDGE, rate=rate, pitch=pitch).save(str(ruta))
            rutas.append(ruta)
        return rutas

    return asyncio.run(generar())


def _openai(trozos: list[str], carpeta: Path, prefijo: str) -> list[Path]:
    from openai import OpenAI

    cliente, rutas = OpenAI(), []
    for i, t in enumerate(trozos):
        ruta = carpeta / f"{prefijo}{i:03}.mp3"
        with cliente.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice=config.VOZ_OPENAI, input=t,
            instructions=config.INSTRUCCIONES_VOZ_OPENAI, response_format="mp3",
        ) as r:
            r.stream_to_file(ruta)
        rutas.append(ruta)
    return rutas


def _locutar_parte(texto: str, carpeta: Path, nombre: str, energica: bool) -> Path:
    texto = _preparar(texto)
    if config.MOTOR_VOZ == "openai":
        partes = _openai(_trozos(texto, 3500), carpeta, nombre)
    elif energica:
        partes = _edge(_trozos(texto, 4000), carpeta, nombre,
                       config.VELOCIDAD_EDGE_SALUDO, config.TONO_EDGE_SALUDO)
    else:
        partes = _edge(_trozos(texto, 4000), carpeta, nombre, config.VELOCIDAD_EDGE)
    wav = carpeta / f"{nombre}.wav"
    _a_wav(partes, wav)
    return wav


# --- Mezcla con música ----------------------------------------------------------

def _envolvente(subida_en: float | None, bajada_en: float | None) -> str:
    """Expresión de volumen: música alta (V) o de fondo (B), con transiciones de 0,8 s."""
    v, b, r = config.MUSICA_VOLUMEN, config.MUSICA_VOLUMEN_FONDO, 0.8
    if bajada_en is not None:   # empieza alta y baja al fondo
        return f"if(lt(t,{bajada_en - r}),{v},if(lt(t,{bajada_en}),{v}+({b}-{v})*(t-{bajada_en - r})/{r},{b}))"
    return f"if(lt(t,{subida_en}),{b},if(lt(t,{subida_en + r}),{b}+({v}-{b})*(t-{subida_en})/{r},{v}))"


def _con_musica(voz: Path, musica: Path, destino: Path, es_entrada: bool) -> None:
    dv = duracion_segundos(voz)
    if es_entrada:
        retraso = config.MUSICA_ENTRADA_SEG
        largo = retraso + dv + 1.5
        inicio_musica = 0.0
        volumen = _envolvente(None, retraso)
        fundidos = f"afade=t=out:st={largo - 1.5}:d=1.5"
    else:
        retraso = 0.8
        largo = retraso + dv + config.MUSICA_SALIDA_SEG
        inicio_musica = 30.0
        volumen = _envolvente(retraso + dv + 0.2, None)
        fundidos = f"afade=t=in:st=0:d=0.8,afade=t=out:st={largo - 3}:d=3"
    _ffmpeg(
        "-i", str(voz), "-ss", str(inicio_musica), "-i", str(musica),
        "-filter_complex",
        f"[1:a]atrim=0:{largo},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=stereo,"
        f"volume='{volumen}':eval=frame,{fundidos}[m];"
        f"[0:a]adelay={int(retraso * 1000)}|{int(retraso * 1000)}[v];"
        f"[m][v]amix=inputs=2:duration=first:normalize=0[out]",
        "-map", "[out]", "-ar", "44100", "-ac", "2", str(destino),
    )


def _silencio(segundos: float, destino: Path) -> Path:
    _ffmpeg("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(segundos), str(destino))
    return destino


def mezclar(saludo: Path, cuerpo: Path, cierre: Path, destino: Path, carpeta: Path) -> None:
    musica = RAIZ / config.MUSICA
    if musica.exists():
        entrada, salida = carpeta / "entrada.wav", carpeta / "salida.wav"
        _con_musica(saludo, musica, entrada, es_entrada=True)
        _con_musica(cierre, musica, salida, es_entrada=False)
    else:
        print(f"No encuentro {config.MUSICA}: el episodio irá sin música.")
        entrada, salida = saludo, cierre
    piezas = [entrada, _silencio(0.4, carpeta / "s1.wav"), cuerpo,
              _silencio(0.6, carpeta / "s2.wav"), salida]
    unido = carpeta / "unido.wav"
    _a_wav(piezas, unido)
    # Volumen final homogéneo, al nivel habitual de los podcasts
    _ffmpeg("-i", str(unido), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100", "-ac", "1", "-b:a", "96k", str(destino))


def locutar(guion: dict, destino: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        saludo = _locutar_parte(guion["saludo"], carpeta, "saludo", energica=True)
        cuerpo = _locutar_parte(guion["cuerpo"], carpeta, "cuerpo", energica=False)
        cierre = _locutar_parte(guion["cierre"], carpeta, "cierre", energica=True)
        mezclar(saludo, cuerpo, cierre, destino, carpeta)
