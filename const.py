# custom_components/claude_meter_reader/const.py
"""Constants for the Claude Meter Reader integration."""

DOMAIN = "claude_meter_reader"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_CAMERA_ENTITY = "camera_entity"
CONF_CLAUDE_PROMPT = "claude_prompt"
CONF_LED_ENTITY = "led_entity"
CONF_LED_DELAY = "led_delay"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_LED_ENTITY = "light.wasserzahler_wasserzahler_led"
DEFAULT_LED_DELAY = 10  # Sekunden
DEFAULT_SCAN_INTERVAL = 3600  # 15 minutes

# Services
SERVICE_READ_METER = "read_meter"

# Default Claude prompt
DEFAULT_CLAUDE_PROMPT = """Analysiere dieses Wasserzähler-Bild und lies den aktuellen Zählerstand ab.

STRUKTUR des Zählers:
- OBEN: 5 große schwarze Ziffern (Format: 00000) - das sind die Hauptziffern
- UNTEN: Kleine runde Anzeigen mit roten Zeigern - das sind die Nachkommastellen

WICHTIGE REGELN:
1. Lese ALLE 5 Hauptziffern sorgfältig (auch führende Nullen beachten!)
2. Die Hauptziffern zeigen Kubikmeter (m³)
3. Die runden Anzeigen zeigen 0,1 und 0,01 m³
4. Wenn Hauptziffern '00087' sind, dann ist das 87 (nicht 987!)

BEISPIEL für diesen Zählertyp:
- Hauptziffern: 00087 → 87 m³
- Nachkommastellen: 18 → 0.18 m³
- ERGEBNIS: 87.18

Gib mir nur die finale Zahl zurück (z.B. 87.18).
Falls unklar, antworte mit 'FEHLER'."""