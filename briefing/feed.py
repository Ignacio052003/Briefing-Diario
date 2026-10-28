"""Mantiene la lista de episodios y genera el feed de podcast (RSS compatible con Apple Podcasts)."""
import json
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import config


def _cargar(site: Path) -> list[dict]:
    ruta = site / "episodios.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []


def existe_episodio(site: Path, guid: str) -> bool:
    return any(e["guid"] == guid and (site / e["archivo"]).exists() for e in _cargar(site))


def añadir_episodio(site: Path, episodio: dict) -> list[dict]:
    episodios = [e for e in _cargar(site) if e["guid"] != episodio["guid"]]
    episodios.insert(0, episodio)
    for viejo in episodios[config.EPISODIOS_A_CONSERVAR:]:
        (site / viejo["archivo"]).unlink(missing_ok=True)
        (site / viejo["archivo"].replace(".mp3", ".txt")).unlink(missing_ok=True)
    episodios = episodios[:config.EPISODIOS_A_CONSERVAR]
    (site / "episodios.json").write_text(json.dumps(episodios, ensure_ascii=False, indent=1), encoding="utf-8")
    return episodios


def generar_feed(site: Path, episodios: list[dict], base_url: str) -> None:
    base_url = base_url.rstrip("/")
    items = []
    for e in episodios:
        m, s = divmod(e["duracion"], 60)
        items.append(f"""    <item>
      <title>{escape(e["titulo"])}</title>
      <description>{escape(e["descripcion"])}</description>
      <guid isPermaLink="false">{escape(e["guid"])}</guid>
      <pubDate>{e["fecha_rfc"]}</pubDate>
      <enclosure url="{base_url}/{e["archivo"]}" length="{e["bytes"]}" type="audio/mpeg"/>
      <itunes:duration>{m}:{s:02}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>full</itunes:episodeType>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(config.TITULO_PODCAST)}</title>
    <link>{base_url}/</link>
    <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>es-es</language>
    <description>{escape(config.DESCRIPCION)}</description>
    <itunes:author>{escape(config.AUTOR)}</itunes:author>
    <itunes:summary>{escape(config.DESCRIPCION)}</itunes:summary>
    <itunes:image href="{base_url}/cover.jpg"/>
    <itunes:category text="News"><itunes:category text="Business News"/></itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (site / "feed.xml").write_text(xml, encoding="utf-8")


def datos_episodio(ahora, archivo: Path, duracion: int, titulo: str, descripcion: str) -> dict:
    return {
        "guid": f"briefing-{ahora:%Y-%m-%d}",
        "titulo": titulo,
        "descripcion": descripcion,
        "archivo": archivo.name,
        "bytes": archivo.stat().st_size,
        "duracion": duracion,
        "fecha_rfc": format_datetime(ahora),
    }
