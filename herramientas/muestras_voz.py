"""Genera muestras del mismo texto con todas las voces gratuitas en español de España.

Uso: python herramientas/muestras_voz.py carpeta_salida [velocidad]
"""
import asyncio
import sys
from pathlib import Path

import edge_tts

TEXTO = (
    "¡Buenos días! Es jueves, 29 de octubre. ¡Este es tu resumen diario, para que estés al día de todo!\n"
    "Y ahora, Washington, porque hoy hay doble examen. Lo normal es que la Reserva Federal deje los tipos quietos. "
    "Pero lo importante es el tono. Si deja la puerta abierta a otra subida en diciembre, prepárate para un día movido.\n"
    "Los mercados, al grano. El Ibex cae un 1,5 % y se queda por debajo de los 18.900 puntos. "
    "El S&P 500 subió ayer un 0,6 %, hasta los 7.700. Y el oro, en 4.060 dólares.\n"
    "¡Y hasta aquí tu resumen! Mucho ánimo con el día. ¡Y al ataque!"
).replace("S&P 500", "S and P quinientos")


async def main(salida: Path, velocidad: str) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    # Voces de España y voces "multilingües" (más expresivas; pueden leer en español)
    voces = [v for v in await edge_tts.list_voices()
             if v["Locale"] == "es-ES" or "Multilingual" in v["ShortName"]]
    print("Voces de España disponibles:", ", ".join(v["ShortName"] for v in voces))
    for v in voces:
        nombre = v["ShortName"]
        destino = salida / f"{nombre.removesuffix('Neural')}_{v['Gender']}.mp3"
        try:
            await edge_tts.Communicate(TEXTO, nombre, rate=velocidad).save(str(destino))
            print("OK", destino.name)
        except Exception as e:  # noqa: BLE001
            print("Falla", nombre, e)


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "+20%"))
