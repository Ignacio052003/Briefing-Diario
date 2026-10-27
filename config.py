"""
Configuración del briefing. Todo lo que quieras personalizar está aquí
(o en prompts/guion.md para el estilo y la estructura del guion).
"""

# --- Programa ---------------------------------------------------------------
TITULO_PODCAST = "Mi Briefing Diario"
AUTOR = "Briefing personal"
DESCRIPCION = "Resumen diario personalizado de actualidad, mercados y economía."
EPISODIOS_A_CONSERVAR = 10          # episodios que se mantienen en el feed
ZONA_HORARIA = "Europe/Madrid"

# --- Modelo de IA (Claude) --------------------------------------------------
MODELO_IA = "claude-sonnet-5-5"     # "claude-opus-5-5" = mejor y algo más caro
MAX_BUSQUEDAS_WEB = 8               # búsquedas que puede hacer para completar datos
PALABRAS_OBJETIVO = (1800, 2300)    # ~12-15 minutos de audio

# --- Voz ----------------------------------------------------------------------
# "edge"   -> gratis, voces neuronales de Microsoft (no necesita cuenta)
# "openai" -> más natural, ~0,15 € por episodio (necesita OPENAI_API_KEY)
MOTOR_VOZ = "edge"
VOZ_EDGE = "es-ES-AlvaroNeural"     # alternativa femenina: "es-ES-ElviraNeural"
VELOCIDAD_EDGE = "+8%"
VOZ_OPENAI = "ash"
INSTRUCCIONES_VOZ_OPENAI = (
    "Habla en español de España, con acento castellano neutro. "
    "Tono de presentador de informativo económico de radio: claro, ágil y serio, "
    "con pausas naturales entre bloques."
)

# Sustituciones para que la voz lea bien siglas y símbolos.
PRONUNCIACION = {
    "S&P 500": "S and P quinientos",
    "S&P": "S and P",
    "MSCI": "eme ese ce i",
    "Nasdaq": "Násdaq",
    "Euro Stoxx 50": "Euro Stoxx cincuenta",
    "EE.UU.": "Estados Unidos",
    "EEUU": "Estados Unidos",
    " pb ": " puntos básicos ",
    " p.b.": " puntos básicos",
}

# --- Fuentes de noticias (RSS) -----------------------------------------------
# Si alguna deja de funcionar, el programa la salta y sigue con las demás.
FUENTES = {
    "Mundo": [
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("FT World", "https://www.ft.com/world?format=rss"),
        ("El País Internacional", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"),
    ],
    "Europa": [
        ("Politico Europe", "https://www.politico.eu/feed/"),
        ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml"),
    ],
    "España": [
        ("El País España", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/espana/portada"),
        ("El Confidencial España", "https://rss.elconfidencial.com/espana/"),
        ("Europa Press", "https://www.europapress.es/rss/rss.aspx"),
    ],
    "Mercados y macro": [
        ("Expansión Mercados", "https://e00-expansion.uecdn.es/rss/mercados.xml"),
        ("Expansión Economía", "https://e00-expansion.uecdn.es/rss/economia.xml"),
        ("FT Markets", "https://www.ft.com/markets?format=rss"),
        ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
        ("WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
        ("Cinco Días", "https://feeds.elpais.com/mrss-s/pages/ep/site/cincodias.elpais.com/portada"),
    ],
    "Empresas": [
        ("Expansión Empresas", "https://e00-expansion.uecdn.es/rss/empresas.xml"),
        ("FT Companies", "https://www.ft.com/companies?format=rss"),
        ("El Confidencial Empresas", "https://rss.elconfidencial.com/empresas/"),
    ],
}
NOTICIAS_POR_FUENTE = 12
HORAS_ATRAS = 30          # los lunes se amplía a 78 h para cubrir el fin de semana

# --- Datos de mercado (Yahoo Finance) ----------------------------------------
# (nombre que se leerá, ticker, tipo)  tipo: "indice", "rentabilidad", "divisa", "materia"
MERCADOS = [
    ("S&P 500", "^GSPC", "indice"),
    ("Nasdaq 100", "^NDX", "indice"),
    ("Dow Jones", "^DJI", "indice"),
    ("MSCI World (vía ETF URTH)", "URTH", "indice"),
    ("Euro Stoxx 50", "^STOXX50E", "indice"),
    ("DAX", "^GDAXI", "indice"),
    ("IBEX 35", "^IBEX", "indice"),
    ("Nikkei 225", "^N225", "indice"),
    ("Hang Seng", "^HSI", "indice"),
    ("Futuro S&P 500", "ES=F", "indice"),
    ("VIX", "^VIX", "indice"),
    ("Bono EE.UU. 10 años (rentabilidad)", "^TNX", "rentabilidad"),
    ("Bono EE.UU. 30 años (rentabilidad)", "^TYX", "rentabilidad"),
    ("EUR/USD", "EURUSD=X", "divisa"),
    ("Brent", "BZ=F", "materia"),
    ("Oro", "GC=F", "materia"),
    ("Bitcoin", "BTC-USD", "materia"),
]
