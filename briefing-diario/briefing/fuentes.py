"""Recogida de noticias (RSS) y datos de mercado (Yahoo Finance)."""
import html
import re
from datetime import datetime, timedelta, timezone

import feedparser

import config


def _limpiar(texto: str, max_chars: int = 280) -> str:
    texto = html.unescape(re.sub(r"<[^>]+>", " ", texto or ""))
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:max_chars] + ("…" if len(texto) > max_chars else "")


def _fecha(entry):
    for campo in ("published_parsed", "updated_parsed"):
        valor = entry.get(campo)
        if valor:
            return datetime(*valor[:6], tzinfo=timezone.utc)
    return None


def recoger_noticias(ahora: datetime) -> str:
    """Devuelve los titulares recientes agrupados por sección, en texto plano."""
    horas = config.HORAS_ATRAS + (48 if ahora.weekday() == 0 else 0)
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    bloques, fallos = [], []

    for seccion, fuentes in config.FUENTES.items():
        lineas = []
        for nombre, url in fuentes:
            try:
                feed = feedparser.parse(url, agent="Mozilla/5.0 (briefing personal)")
                if not feed.entries:
                    raise ValueError("sin entradas")
            except Exception as e:  # noqa: BLE001
                fallos.append(f"{nombre} ({e})")
                continue
            vistos = 0
            for entry in feed.entries:
                fecha = _fecha(entry)
                if fecha and fecha < limite:
                    continue
                titulo = _limpiar(entry.get("title", ""), 200)
                if not titulo:
                    continue
                resumen = _limpiar(entry.get("summary", ""))
                hora = fecha.strftime("%d/%m %H:%M UTC") if fecha else "s/f"
                linea = f"- [{nombre} · {hora}] {titulo}"
                if resumen and resumen.lower() not in titulo.lower():
                    linea += f" — {resumen}"
                lineas.append(linea)
                vistos += 1
                if vistos >= config.NOTICIAS_POR_FUENTE:
                    break
        if lineas:
            bloques.append(f"### {seccion}\n" + "\n".join(lineas))

    if fallos:
        print("Fuentes que no han respondido:", "; ".join(fallos))
    return "\n\n".join(bloques)


def recoger_mercados() -> str:
    """Último precio y variación de cada activo, con la fecha del dato."""
    import yfinance as yf

    lineas = []
    for nombre, ticker, tipo in config.MERCADOS:
        try:
            hist = yf.Ticker(ticker).history(period="10d", interval="1d", auto_adjust=False)
            hist = hist.dropna(subset=["Close"])
            if len(hist) < 2:
                raise ValueError("datos insuficientes")
            ult, ant = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
            fecha = hist.index[-1].strftime("%d/%m/%Y")
            semana = hist["Close"].iloc[-6] if len(hist) >= 6 else None
            if tipo == "rentabilidad":
                txt = f"{ult:.3f} %, variación {(ult - ant) * 100:+.1f} pb"
                if semana is not None:
                    txt += f" (5 sesiones: {(ult - semana) * 100:+.1f} pb)"
            else:
                dec = 4 if tipo == "divisa" else 2
                txt = f"{ult:,.{dec}f}, variación {(ult / ant - 1) * 100:+.2f} %"
                if semana is not None:
                    txt += f" (5 sesiones: {(ult / semana - 1) * 100:+.2f} %)"
            lineas.append(f"- {nombre}: {txt} [último dato: {fecha}]")
        except Exception as e:  # noqa: BLE001
            print(f"Sin datos de {nombre} ({ticker}): {e}")
    return "\n".join(lineas) or "(No se han podido obtener datos de mercado; búscalos en la web.)"
