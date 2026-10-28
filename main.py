"""
Genera el briefing del día y actualiza el feed de podcast.

Uso:
  python main.py --site site --base-url https://usuario.github.io/repo
  python main.py --solo-guion          # solo imprime el guion (sin audio)
  python main.py --demo --site site    # prueba sin conexión (guion y audio de ejemplo)
  python main.py --solo-si-falta …     # no hace nada si el episodio de hoy ya existe
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402
from briefing import feed  # noqa: E402
from briefing.guion import fecha_larga  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--site", default="site")
    p.add_argument("--base-url", default=os.environ.get("FEED_BASE_URL", "http://localhost"))
    p.add_argument("--solo-guion", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--solo-si-falta", action="store_true",
                   help="no generar nada si el episodio de hoy ya está publicado")
    args = p.parse_args()

    ahora = datetime.now(ZoneInfo(config.ZONA_HORARIA))
    site = Path(args.site)
    site.mkdir(parents=True, exist_ok=True)

    if args.solo_si_falta and feed.existe_episodio(site, f"briefing-{ahora:%Y-%m-%d}"):
        print("El episodio de hoy ya existe: no se genera otro.")
        return

    if args.demo:
        from briefing.guion import fecha_corta
        guion = {"saludo": config.SALUDO.format(fecha=fecha_corta(ahora)),
                 "sumario": "Hoy te cuento dos cosas: una prueba y otra prueba.",
                 "secciones": ["Primera sección de prueba.", "Segunda sección de prueba."],
                 "cierre": "¡Y hasta aquí tu resumen! ¡Y al ataque!"}
    else:
        from briefing.fuentes import recoger_mercados, recoger_noticias
        from briefing.guion import escribir_guion
        print("Recogiendo noticias y datos de mercado…")
        noticias, mercados = recoger_noticias(ahora), recoger_mercados()
        print("Redactando el guion con Claude…")
        guion = escribir_guion(ahora, noticias, mercados)

    texto = "\n\n".join([guion["saludo"], guion["sumario"],
                         "\n\n[RÁFAGA]\n\n".join(guion["secciones"]), guion["cierre"]])
    if args.solo_guion:
        print("\n" + texto)
        return

    mp3 = site / f"briefing-{ahora:%Y-%m-%d}.mp3"
    if args.demo:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "sine=frequency=440:duration=5", "-ac", "1", "-b:a", "64k", str(mp3)], check=True)
    else:
        from briefing.voz import locutar
        print("Generando el audio…")
        locutar(guion, mp3)

    from briefing.voz import duracion_segundos
    duracion = int(duracion_segundos(mp3))
    mp3.with_suffix(".txt").write_text(texto, encoding="utf-8")

    descripcion = guion["sumario"][:600] or " ".join(
        re.split(r"(?<=[.!?])\s+", guion["secciones"][0].replace("\n", " "))[:3])[:600]
    titulo = f"Briefing del {fecha_larga(ahora)}"
    episodios = feed.añadir_episodio(site, feed.datos_episodio(ahora, mp3, duracion, titulo, descripcion))

    portada = Path(__file__).parent / "assets" / "cover.jpg"
    if portada.exists():
        shutil.copy(portada, site / "cover.jpg")
    feed.generar_feed(site, episodios, args.base_url)
    print(f"Listo: {mp3.name} ({duracion // 60} min {duracion % 60} s). Feed: {args.base_url.rstrip('/')}/feed.xml")


if __name__ == "__main__":
    main()
