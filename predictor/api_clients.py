from __future__ import annotations

import json
import math
import os
import re
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# Cargar variables de entorno
# ============================================================

load_dotenv()
load_dotenv("API_KEYS_AQUI.env")


API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
THE_ODDS_BASE = "https://api.the-odds-api.com/v4"


# ============================================================
# Clasificación competitiva de selecciones
# ============================================================
# Nota: "Bajo" no significa que el equipo sea malo. En esta app significa
# menor experiencia mundialista reciente, menor profundidad de plantilla o
# menor peso competitivo internacional comparado con equipos elite.

TEAM_LEVELS: dict[str, dict[str, str]] = {
    # Elite
    "argentina": {"level": "Elite", "comment": "Selección elite: campeón reciente, jerarquía internacional, experiencia en finales y plantilla de alto impacto."},
    "spain": {"level": "Elite", "comment": "Selección elite: alto nivel técnico, profundidad de plantilla y fuerte expectativa competitiva."},
    "españa": {"level": "Elite", "comment": "Selección elite: alto nivel técnico, profundidad de plantilla y fuerte expectativa competitiva."},
    "france": {"level": "Elite", "comment": "Selección elite: plantilla de máximo nivel, experiencia internacional y gran capacidad física/ofensiva."},
    "francia": {"level": "Elite", "comment": "Selección elite: plantilla de máximo nivel, experiencia internacional y gran capacidad física/ofensiva."},
    "england": {"level": "Elite", "comment": "Selección elite: plantilla profunda, jugadores top y alto poder ofensivo."},
    "inglaterra": {"level": "Elite", "comment": "Selección elite: plantilla profunda, jugadores top y alto poder ofensivo."},
    "portugal": {"level": "Elite", "comment": "Selección elite: mucho talento individual, experiencia y profundidad competitiva."},
    "brazil": {"level": "Elite", "comment": "Selección elite: potencia histórica, talento ofensivo y experiencia mundialista."},
    "brasil": {"level": "Elite", "comment": "Selección elite: potencia histórica, talento ofensivo y experiencia mundialista."},
    "germany": {"level": "Elite", "comment": "Selección elite: potencia histórica, jerarquía competitiva y experiencia mundialista."},
    "alemania": {"level": "Elite", "comment": "Selección elite: potencia histórica, jerarquía competitiva y experiencia mundialista."},
    "netherlands": {"level": "Elite", "comment": "Selección elite: estructura táctica fuerte, talento y alto nivel competitivo."},
    "países bajos": {"level": "Elite", "comment": "Selección elite: estructura táctica fuerte, talento y alto nivel competitivo."},
    "paises bajos": {"level": "Elite", "comment": "Selección elite: estructura táctica fuerte, talento y alto nivel competitivo."},
    "belgium": {"level": "Elite", "comment": "Selección elite: plantilla competitiva, experiencia internacional y jugadores importantes."},
    "bélgica": {"level": "Elite", "comment": "Selección elite: plantilla competitiva, experiencia internacional y jugadores importantes."},
    "belgica": {"level": "Elite", "comment": "Selección elite: plantilla competitiva, experiencia internacional y jugadores importantes."},
    "morocco": {"level": "Elite", "comment": "Selección elite/alta: equipo competitivo, ranking alto reciente y experiencia fuerte en torneo grande."},
    "marruecos": {"level": "Elite", "comment": "Selección elite/alta: equipo competitivo, ranking alto reciente y experiencia fuerte en torneo grande."},

    # Medio competitivo
    "croatia": {"level": "Medio", "comment": "Medio competitivo: mucha experiencia internacional, aunque debe vigilarse recambio y momento actual."},
    "croacia": {"level": "Medio", "comment": "Medio competitivo: mucha experiencia internacional, aunque debe vigilarse recambio y momento actual."},
    "uruguay": {"level": "Medio", "comment": "Medio competitivo: tradición fuerte, intensidad y jugadores competitivos."},
    "colombia": {"level": "Medio", "comment": "Medio competitivo: buenos jugadores, capacidad de competir ante rivales fuertes y buen ritmo sudamericano."},
    "senegal": {"level": "Medio", "comment": "Medio competitivo: físico, experiencia reciente y buen nivel continental."},
    "mexico": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista, condición de anfitrión y fuerte contexto emocional."},
    "méxico": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista, condición de anfitrión y fuerte contexto emocional."},
    "united states": {"level": "Medio", "comment": "Medio competitivo: anfitrión, plantilla joven, física y con jugadores en ligas competitivas."},
    "usa": {"level": "Medio", "comment": "Medio competitivo: anfitrión, plantilla joven, física y con jugadores en ligas competitivas."},
    "estados unidos": {"level": "Medio", "comment": "Medio competitivo: anfitrión, plantilla joven, física y con jugadores en ligas competitivas."},
    "switzerland": {"level": "Medio", "comment": "Medio competitivo: equipo ordenado, difícil de superar y con experiencia internacional."},
    "suiza": {"level": "Medio", "comment": "Medio competitivo: equipo ordenado, difícil de superar y con experiencia internacional."},
    "japan": {"level": "Medio", "comment": "Medio competitivo: equipo táctico, rápido, disciplinado y con experiencia mundialista."},
    "japón": {"level": "Medio", "comment": "Medio competitivo: equipo táctico, rápido, disciplinado y con experiencia mundialista."},
    "japon": {"level": "Medio", "comment": "Medio competitivo: equipo táctico, rápido, disciplinado y con experiencia mundialista."},
    "ecuador": {"level": "Medio", "comment": "Medio competitivo: equipo físico, intenso y competitivo."},
    "ivory coast": {"level": "Medio", "comment": "Medio competitivo: físico, talento y potencial de sorpresa."},
    "costa de marfil": {"level": "Medio", "comment": "Medio competitivo: físico, talento y potencial de sorpresa."},
    "austria": {"level": "Medio", "comment": "Medio competitivo: selección europea organizada, intensa y táctica."},
    "turkey": {"level": "Medio", "comment": "Medio competitivo: talento, intensidad y experiencia internacional."},
    "turquía": {"level": "Medio", "comment": "Medio competitivo: talento, intensidad y experiencia internacional."},
    "turquia": {"level": "Medio", "comment": "Medio competitivo: talento, intensidad y experiencia internacional."},
    "iran": {"level": "Medio", "comment": "Medio competitivo: mundialista recurrente, físico y ordenado."},
    "irán": {"level": "Medio", "comment": "Medio competitivo: mundialista recurrente, físico y ordenado."},
    "south korea": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista, velocidad y jugadores diferenciales."},
    "corea del sur": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista, velocidad y jugadores diferenciales."},
    "australia": {"level": "Medio", "comment": "Medio competitivo: físico, experiencia mundialista y orden competitivo."},
    "algeria": {"level": "Medio", "comment": "Medio competitivo: talento, experiencia africana y potencial ofensivo."},
    "argelia": {"level": "Medio", "comment": "Medio competitivo: talento, experiencia africana y potencial ofensivo."},
    "egypt": {"level": "Medio", "comment": "Medio competitivo: figuras importantes, experiencia continental y capacidad competitiva."},
    "egipto": {"level": "Medio", "comment": "Medio competitivo: figuras importantes, experiencia continental y capacidad competitiva."},
    "canada": {"level": "Medio", "comment": "Medio competitivo: anfitrión, crecimiento reciente y jugadores importantes."},
    "norway": {"level": "Medio", "comment": "Medio competitivo: jugadores diferenciales, aunque con menor experiencia mundialista reciente."},
    "noruega": {"level": "Medio", "comment": "Medio competitivo: jugadores diferenciales, aunque con menor experiencia mundialista reciente."},
    "sweden": {"level": "Medio", "comment": "Medio competitivo: equipo europeo físico, estructurado y competitivo."},
    "suecia": {"level": "Medio", "comment": "Medio competitivo: equipo europeo físico, estructurado y competitivo."},
    "ghana": {"level": "Medio", "comment": "Medio competitivo: tradición mundialista, físico y talento ofensivo."},
    "túnez": {"level": "Medio", "comment": "Medio competitivo: equipo ordenado, físico y con experiencia mundialista."},
    "tunez": {"level": "Medio", "comment": "Medio competitivo: equipo ordenado, físico y con experiencia mundialista."},
    "tunisia": {"level": "Medio", "comment": "Medio competitivo: equipo ordenado, físico y con experiencia mundialista."},
    "scotland": {"level": "Medio", "comment": "Medio competitivo: selección europea intensa, física y competitiva."},
    "escocia": {"level": "Medio", "comment": "Medio competitivo: selección europea intensa, física y competitiva."},
    "czechia": {"level": "Medio", "comment": "Medio competitivo: selección europea ordenada y competitiva."},
    "chequia": {"level": "Medio", "comment": "Medio competitivo: selección europea ordenada y competitiva."},
    "paraguay": {"level": "Medio", "comment": "Medio competitivo: tradición sudamericana, intensidad y experiencia competitiva."},
    "bosnia and herzegovina": {"level": "Medio", "comment": "Medio competitivo: experiencia y jugadores competitivos, aunque irregular ante favoritos fuertes."},
    "bosnia": {"level": "Medio", "comment": "Medio competitivo: experiencia y jugadores competitivos, aunque irregular ante favoritos fuertes."},
    "bosnia y herzegovina": {"level": "Medio", "comment": "Medio competitivo: experiencia y jugadores competitivos, aunque irregular ante favoritos fuertes."},
    "panama": {"level": "Medio", "comment": "Medio competitivo: equipo de Concacaf capaz de competir, aunque con cautela ante rivales fuertes."},
    "panamá": {"level": "Medio", "comment": "Medio competitivo: equipo de Concacaf capaz de competir, aunque con cautela ante rivales fuertes."},
    "qatar": {"level": "Medio", "comment": "Medio competitivo: experiencia reciente como anfitrión mundialista; evaluar según rival y contexto."},
    "catar": {"level": "Medio", "comment": "Medio competitivo: experiencia reciente como anfitrión mundialista; evaluar según rival y contexto."},
    "saudi arabia": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista y capacidad de sorpresa, pero irregular ante equipos top."},
    "arabia saudita": {"level": "Medio", "comment": "Medio competitivo: experiencia mundialista y capacidad de sorpresa, pero irregular ante equipos top."},

    # Bajo competitivo / emergente
    "south africa": {"level": "Bajo", "comment": "Bajo competitivo: puede competir físicamente, pero tiene menor peso relativo ante selecciones top."},
    "sudáfrica": {"level": "Bajo", "comment": "Bajo competitivo: puede competir físicamente, pero tiene menor peso relativo ante selecciones top."},
    "sudafrica": {"level": "Bajo", "comment": "Bajo competitivo: puede competir físicamente, pero tiene menor peso relativo ante selecciones top."},
    "haiti": {"level": "Bajo", "comment": "Bajo competitivo: menor experiencia mundialista reciente y mayor riesgo ante rivales fuertes."},
    "haití": {"level": "Bajo", "comment": "Bajo competitivo: menor experiencia mundialista reciente y mayor riesgo ante rivales fuertes."},
    "curacao": {"level": "Bajo", "comment": "Bajo competitivo: selección emergente con menor experiencia internacional de élite."},
    "curazao": {"level": "Bajo", "comment": "Bajo competitivo: selección emergente con menor experiencia internacional de élite."},
    "curaçao": {"level": "Bajo", "comment": "Bajo competitivo: selección emergente con menor experiencia internacional de élite."},
    "new zealand": {"level": "Bajo", "comment": "Bajo competitivo: equipo ordenado, pero con menor roce frente a selecciones top."},
    "nueva zelanda": {"level": "Bajo", "comment": "Bajo competitivo: equipo ordenado, pero con menor roce frente a selecciones top."},
    "cape verde": {"level": "Bajo", "comment": "Bajo competitivo/emergente: no es mala selección, pero tiene menor experiencia mundialista."},
    "cabo verde": {"level": "Bajo", "comment": "Bajo competitivo/emergente: no es mala selección, pero tiene menor experiencia mundialista."},
    "iraq": {"level": "Bajo", "comment": "Bajo competitivo: puede competir, pero tiene menor experiencia ante rivales de élite."},
    "irak": {"level": "Bajo", "comment": "Bajo competitivo: puede competir, pero tiene menor experiencia ante rivales de élite."},
    "jordan": {"level": "Bajo", "comment": "Bajo competitivo: competitivo en su región, pero con menor peso mundialista."},
    "jordania": {"level": "Bajo", "comment": "Bajo competitivo: competitivo en su región, pero con menor peso mundialista."},
    "dr congo": {"level": "Bajo", "comment": "Bajo competitivo: físico y talento, pero menor estabilidad/experiencia mundialista reciente."},
    "rd congo": {"level": "Bajo", "comment": "Bajo competitivo: físico y talento, pero menor estabilidad/experiencia mundialista reciente."},
    "congo dr": {"level": "Bajo", "comment": "Bajo competitivo: físico y talento, pero menor estabilidad/experiencia mundialista reciente."},
    "uzbekistan": {"level": "Bajo", "comment": "Bajo competitivo/emergente: puede competir, pero con menor historial mundialista."},
    "uzbekistán": {"level": "Bajo", "comment": "Bajo competitivo/emergente: puede competir, pero con menor historial mundialista."},
}

TEAM_LEVEL_ORDER = {
    "Bajo": 1,
    "Medio": 2,
    "Elite": 3,
}


# ============================================================
# Utilidades generales
# ============================================================

def _safe_get_json(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: int = 25,
) -> dict[str, Any] | list[dict[str, Any]]:
    response = requests.get(
        url,
        headers=headers or {},
        params=params or {},
        timeout=timeout,
    )

    response.raise_for_status()

    daily_limit = response.headers.get("x-ratelimit-requests-limit")
    daily_remaining = response.headers.get("x-ratelimit-requests-remaining")
    minute_limit = response.headers.get("X-RateLimit-Limit")
    minute_remaining = response.headers.get("X-RateLimit-Remaining")

    if daily_remaining or minute_remaining:
        print("API-FOOTBALL USO:")
        print("Límite diario:", daily_limit)
        print("Restantes del día:", daily_remaining)
        print("Límite por minuto:", minute_limit)
        print("Restantes por minuto:", minute_remaining)

    return response.json()


def _parse_probability(value: Any) -> float:
    """
    Convierte probabilidades en distintos formatos a escala 0-1.

    Acepta:
    - 0.90
    - 90
    - 90.89
    - "90,89"
    - "90,89%"
    - "90.89%"
    - "0,9089"
    """
    if value is None:
        raise ValueError("Probabilidad vacía.")

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()

        if not text:
            raise ValueError("Probabilidad vacía.")

        text = text.replace("%", "").strip()
        text = text.replace(",", ".")
        text = re.sub(r"[^0-9.\-]", "", text)

        if not text:
            raise ValueError(f"No se pudo leer probabilidad: {value}")

        number = float(text)

    if number > 1.5:
        number = number / 100

    if number < 0:
        number = 0

    if number > 1:
        number = 1

    return number


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.strip().replace(",", ".").replace("%", "")
            value = re.sub(r"[^0-9.\-]", "", value)

        if value == "":
            return default

        return float(value)
    except Exception:
        return default


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def extract_json(text: str) -> dict[str, Any]:
    """
    Extrae un JSON válido desde una respuesta de texto.
    """
    text = str(text).strip()

    if not text:
        raise ValueError("La respuesta de IA llegó vacía.")

    text = (
        text.replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    text = re.sub(r"^\s*\d+\.\s*", "", text)
    text = re.sub(r"^\s*[-•]\s*", "", text)

    try:
        data = json.loads(text)

        if isinstance(data, dict):
            return data

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return data[0]

    except json.JSONDecodeError:
        pass

    start = text.find("{")

    if start == -1:
        raise ValueError(f"No se encontró JSON en la respuesta IA: {text[:500]}")

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        char = text[i]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                candidate = text[start:i + 1]

                try:
                    data = json.loads(candidate)

                    if isinstance(data, dict):
                        return data

                    if (
                        isinstance(data, list)
                        and len(data) > 0
                        and isinstance(data[0], dict)
                    ):
                        return data[0]

                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"No se pudo convertir el JSON extraído. "
                        f"Error: {exc}. Bloque: {candidate[:500]}"
                    )

    raise ValueError(f"No se pudo encontrar un JSON completo: {text[:500]}")


# ============================================================
# API-Football
# ============================================================

class ApiFootballClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        self.headers = {"x-apisports-key": self.api_key} if self.api_key else {}
        self._team_cache: dict[str, int] = {}
        self._official_goals_cache: dict[str, dict[str, Any]] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def search_team_id(self, team_name: str) -> int | None:
        if not self.enabled:
            return None

        team_name = str(team_name).strip()

        if not team_name:
            return None

        if team_name in self._team_cache:
            return self._team_cache[team_name]

        try:
            data = _safe_get_json(
                f"{API_FOOTBALL_BASE}/teams",
                headers=self.headers,
                params={"search": team_name},
            )

            if not isinstance(data, dict):
                return None

            items = data.get("response", [])

            if not items:
                return None

            # Para selecciones nacionales, API-Football puede devolver varios resultados.
            # Preferimos los equipos marcados como nacionales para evitar clubes con nombres similares.
            national_items = [
                item for item in items
                if isinstance(item, dict)
                and isinstance(item.get("team"), dict)
                and item.get("team", {}).get("national") is True
            ]

            chosen = national_items[0] if national_items else items[0]

            team_id = int(chosen["team"]["id"])
            self._team_cache[team_name] = team_id

            return team_id

        except Exception:
            return None

    def head_to_head_context(self, home: str, away: str, last: int = 5) -> str:
        if not self.enabled:
            return "API-Football no configurado."

        home_id = self.search_team_id(home)
        away_id = self.search_team_id(away)

        if not home_id or not away_id:
            return "No se encontraron IDs confiables para head-to-head en API-Football."

        try:
            data = _safe_get_json(
                f"{API_FOOTBALL_BASE}/fixtures/headtohead",
                headers=self.headers,
                params={
                    "h2h": f"{home_id}-{away_id}",
                    "last": last,
                },
            )

            if not isinstance(data, dict):
                return "API-Football respondió en un formato no esperado."

            fixtures = data.get("response", [])

            if not fixtures:
                return "No hay historial head-to-head reciente en API-Football."

            lines = []

            for fixture in fixtures[:last]:
                teams = fixture.get("teams", {})
                goals = fixture.get("goals", {})
                fixture_data = fixture.get("fixture", {})

                date = str(fixture_data.get("date", ""))[:10]

                home_team = teams.get("home", {}).get("name", "Local")
                away_team = teams.get("away", {}).get("name", "Visitante")

                home_goals = goals.get("home")
                away_goals = goals.get("away")

                lines.append(
                    f"{date}: {home_team} {home_goals} - {away_goals} {away_team}"
                )

            return "Historial H2H API-Football: " + " | ".join(lines)

        except Exception as exc:
            return f"No se pudo consultar API-Football: {exc}"


    def _is_official_fixture(self, fixture: dict[str, Any]) -> bool:
        """
        Devuelve True si el partido es oficial.

        Criterio:
        - Debe estar finalizado.
        - Excluye amistosos / friendlies.
        """
        fixture_info = fixture.get("fixture", {}) or {}
        status = fixture_info.get("status", {}) or {}
        status_short = str(status.get("short", "")).upper().strip()

        if status_short not in ["FT", "AET", "PEN"]:
            return False

        league = fixture.get("league", {}) or {}
        league_name = str(league.get("name", "")).lower().strip()

        friendly_terms = [
            "friendly",
            "friendlies",
            "amistoso",
            "amistosos",
            "club friendly",
            "international friendlies",
        ]

        if any(term in league_name for term in friendly_terms):
            return False

        goals = fixture.get("goals", {}) or {}
        if goals.get("home") is None or goals.get("away") is None:
            return False

        return True

    def official_team_goals_stats(
        self,
        team_name: str,
        sample_size: int = 10,
        fetch_last: int = 50,
    ) -> dict[str, Any]:
        """
        Calcula promedio de goles en partidos oficiales, excluyendo amistosos.

        Columnas resultantes:
        - official_matches_sample
        - avg_goals_for_official
        - avg_goals_against_official
        - avg_total_goals_official
        - official_competitions_sample
        """
        empty = {
            "official_matches_sample": 0,
            "avg_goals_for_official": None,
            "avg_goals_against_official": None,
            "avg_total_goals_official": None,
            "official_competitions_sample": "",
        }

        if not self.enabled:
            return empty

        team_name = str(team_name).strip()

        if not team_name:
            return empty

        cache_key = f"{team_name.lower()}|{sample_size}|{fetch_last}"

        if cache_key in self._official_goals_cache:
            return self._official_goals_cache[cache_key]

        team_id = self.search_team_id(team_name)

        if not team_id:
            self._official_goals_cache[cache_key] = empty
            return empty

        try:
            data = _safe_get_json(
                f"{API_FOOTBALL_BASE}/fixtures",
                headers=self.headers,
                params={
                    "team": team_id,
                    "last": fetch_last,
                },
            )

            if not isinstance(data, dict):
                self._official_goals_cache[cache_key] = empty
                return empty

            fixtures = data.get("response", []) or []

            official_rows = []
            competitions = []

            for fixture in fixtures:
                if not isinstance(fixture, dict):
                    continue

                if not self._is_official_fixture(fixture):
                    continue

                teams = fixture.get("teams", {}) or {}
                home_team = teams.get("home", {}) or {}
                away_team = teams.get("away", {}) or {}

                home_id = home_team.get("id")
                away_id = away_team.get("id")

                goals = fixture.get("goals", {}) or {}
                home_goals = goals.get("home")
                away_goals = goals.get("away")

                if home_goals is None or away_goals is None:
                    continue

                home_goals = int(home_goals)
                away_goals = int(away_goals)

                if int(home_id) == int(team_id):
                    goals_for = home_goals
                    goals_against = away_goals
                elif int(away_id) == int(team_id):
                    goals_for = away_goals
                    goals_against = home_goals
                else:
                    continue

                league = fixture.get("league", {}) or {}
                league_name = str(league.get("name", "")).strip()

                if league_name and league_name not in competitions:
                    competitions.append(league_name)

                official_rows.append({
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "total_goals": goals_for + goals_against,
                    "competition": league_name,
                })

                if len(official_rows) >= int(sample_size):
                    break

            if not official_rows:
                self._official_goals_cache[cache_key] = empty
                return empty

            count = len(official_rows)
            goals_for_total = sum(row["goals_for"] for row in official_rows)
            goals_against_total = sum(row["goals_against"] for row in official_rows)
            total_goals = sum(row["total_goals"] for row in official_rows)

            result = {
                "official_matches_sample": count,
                "avg_goals_for_official": round(goals_for_total / count, 2),
                "avg_goals_against_official": round(goals_against_total / count, 2),
                "avg_total_goals_official": round(total_goals / count, 2),
                "official_competitions_sample": " | ".join(competitions[:5]),
            }

            self._official_goals_cache[cache_key] = result
            return result

        except Exception:
            self._official_goals_cache[cache_key] = empty
            return empty

    def official_match_goals_context(
        self,
        home: str,
        away: str,
        sample_size: int = 10,
    ) -> tuple[str, dict[str, Any]]:
        """
        Calcula promedios oficiales para local y visitante y devuelve:
        - Texto para contexto IA.
        - Diccionario plano para columnas del DataFrame/Excel.
        """
        home_stats = self.official_team_goals_stats(home, sample_size=sample_size)
        away_stats = self.official_team_goals_stats(away, sample_size=sample_size)

        flat = {
            "home_official_matches_sample": home_stats.get("official_matches_sample"),
            "home_avg_goals_for_official": home_stats.get("avg_goals_for_official"),
            "home_avg_goals_against_official": home_stats.get("avg_goals_against_official"),
            "home_avg_total_goals_official": home_stats.get("avg_total_goals_official"),
            "home_official_competitions_sample": home_stats.get("official_competitions_sample"),
            "away_official_matches_sample": away_stats.get("official_matches_sample"),
            "away_avg_goals_for_official": away_stats.get("avg_goals_for_official"),
            "away_avg_goals_against_official": away_stats.get("avg_goals_against_official"),
            "away_avg_total_goals_official": away_stats.get("avg_total_goals_official"),
            "away_official_competitions_sample": away_stats.get("official_competitions_sample"),
        }

        context = (
            "Promedio de goles en partidos oficiales recientes, excluyendo amistosos. "
            f"Muestra objetivo: últimos {sample_size} partidos oficiales disponibles. "
            f"{home}: PJ {flat['home_official_matches_sample']}, "
            f"GF/prom {flat['home_avg_goals_for_official']}, "
            f"GC/prom {flat['home_avg_goals_against_official']}, "
            f"Total/prom {flat['home_avg_total_goals_official']}. "
            f"{away}: PJ {flat['away_official_matches_sample']}, "
            f"GF/prom {flat['away_avg_goals_for_official']}, "
            f"GC/prom {flat['away_avg_goals_against_official']}, "
            f"Total/prom {flat['away_avg_total_goals_official']}."
        )

        return context, flat



# ============================================================
# The Odds API
# ============================================================

class TheOddsApiClient:
    def __init__(self, api_key: str | None = None, sport_key: str | None = None):
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY", "")
        self.sport_key = sport_key or os.getenv(
            "THE_ODDS_SPORT_KEY",
            "soccer_fifa_world_cup",
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def list_sports(self) -> pd.DataFrame:
        if not self.enabled:
            return pd.DataFrame()

        try:
            data = _safe_get_json(
                f"{THE_ODDS_BASE}/sports",
                params={"apiKey": self.api_key},
            )

            return pd.DataFrame(data)

        except Exception:
            return pd.DataFrame()

    def fetch_odds(
        self,
        regions: str = "us,eu,uk",
        markets: str = "h2h",
        odds_format: str = "decimal",
    ) -> list[dict[str, Any]]:
        if not self.enabled:
            return []

        try:
            url = f"{THE_ODDS_BASE}/sports/{self.sport_key}/odds"

            params = {
                "apiKey": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
                "dateFormat": "iso",
            }

            data = _safe_get_json(url, params=params)

            if isinstance(data, list):
                return data

            return []

        except Exception:
            return []

    def match_odds_snapshot(self, home: str, away: str) -> str:
        if not self.enabled:
            return "The Odds API no configurado; usando cuotas base del archivo."

        try:
            events = self.fetch_odds()

            home_l = str(home).lower().strip()
            away_l = str(away).lower().strip()

            for event in events:
                home_team = str(event.get("home_team", "")).lower().strip()
                away_team = str(event.get("away_team", "")).lower().strip()

                teams = [home_team, away_team]

                if home_l in teams and away_l in teams:
                    bookmakers = event.get("bookmakers", [])[:3]
                    parts = []

                    for bookmaker in bookmakers:
                        markets = bookmaker.get("markets", [])

                        if not markets:
                            continue

                        outcomes = markets[0].get("outcomes", [])

                        parts.append(
                            f"{bookmaker.get('title', 'Bookmaker')}: {outcomes}"
                        )

                    if parts:
                        return "Cuotas actuales The Odds API: " + " | ".join(parts)

                    return "El partido existe en The Odds API, pero no hay cuotas disponibles."

            return "No se encontró el partido en The Odds API; usando cuotas base."

        except Exception as exc:
            return f"No se pudo consultar The Odds API: {exc}"


# ============================================================
# OpenAI Analyzer
# ============================================================

class OpenAIAnalyzer:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        enable_web_search: bool = True,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.enable_web_search = enable_web_search

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def analyze_match(
        self,
        match: dict[str, Any],
        api_context: str = "",
        odds_context: str = "",
    ) -> dict[str, Any]:
        if not self.enabled:
            return {}

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        prompt = self._build_prompt(match, api_context, odds_context)
        schema = self._build_schema()

        tools = []
        if self.enable_web_search:
            tools = [{"type": "web_search_preview"}]

        payload = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": 6000,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "worldcup_match_prediction",
                    "schema": schema,
                    "strict": True,
                }
            },
        }

        if tools:
            payload["tools"] = tools

        response = None
        first_error = ""

        try:
            response = client.responses.create(**payload)

        except Exception as exc:
            msg = str(exc)
            first_error = msg

            if self.enable_web_search and (
                "web_search" in msg
                or "tools" in msg
                or "Unsupported" in msg
                or "not supported" in msg
            ):
                payload.pop("tools", None)
                response = client.responses.create(**payload)
            else:
                raise Exception(msg)

        data = self._response_to_data(response)

        if not data or not isinstance(data, dict) or len(data.keys()) == 0:
            data = self._fallback_analysis(client, match, api_context, odds_context)

        if not data or not self._has_probability_keys(data):
            data = self._deterministic_fallback(
                match,
                reason="La IA devolvió una respuesta vacía o incompleta después del fallback.",
            )

        # Guardar nombres del partido para conclusiones legibles.
        # Estas llaves internas no se exportan como columnas.
        data["_home_team_name"] = match.get("home", "Local")
        data["_away_team_name"] = match.get("away", "Visitante")

        data = self._normalize_ai_probabilities(data)
        data = self._complete_expected_goals_and_luck(data)
        data = self._complete_entropy(data)
        data = self._complete_team_level_analysis(data)
        data = self._complete_betting_conclusion(data)
        data = self._validate_ai_response(data)

        usage = getattr(response, "usage", None) if response is not None else None
        if usage:
            data["openai_input_tokens"] = getattr(usage, "input_tokens", None)
            data["openai_output_tokens"] = getattr(usage, "output_tokens", None)
            data["openai_total_tokens"] = getattr(usage, "total_tokens", None)

        if first_error:
            data["openai_first_error"] = first_error

        return data

    def _response_to_data(self, response: Any) -> dict[str, Any]:
        text = getattr(response, "output_text", None)

        if not text:
            text = self._extract_text_from_response(response)

        if not text:
            return {}

        try:
            data = json.loads(text)
        except Exception:
            try:
                data = extract_json(text)
            except Exception:
                return {}

        if isinstance(data, dict):
            return data

        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]

        return {}

    def _has_probability_keys(self, data: dict[str, Any]) -> bool:
        return all(
            key in data and data.get(key) not in [None, ""]
            for key in ["prob_home_ai", "prob_draw_ai", "prob_away_ai"]
        )

    def _fallback_analysis(
        self,
        client: Any,
        match: dict[str, Any],
        api_context: str,
        odds_context: str,
    ) -> dict[str, Any]:
        """
        Segundo intento cuando Structured Outputs devuelve {} o respuesta incompleta.
        Este prompt es más simple y no usa web_search ni json_schema.

        Si también falla, devuelve un fallback determinístico basado en mercado,
        en vez de romper toda la ejecución.
        """
        fallback_prompt = f"""
Devuelve SOLO un objeto JSON válido. No uses markdown. No escribas texto fuera del JSON.

Analiza este partido:
{match.get("home")} vs {match.get("away")} - Grupo {match.get("group")}

{self._team_level_context(match.get("home"), match.get("away"))}

Cuotas:
Local {match.get("home_odds")}
Empate {match.get("draw_odds")}
Visitante {match.get("away_odds")}

Probabilidades de mercado ajustadas:
Local {match.get("prob_home_market", 0):.4f}
Empate {match.get("prob_draw_market", 0):.4f}
Visitante {match.get("prob_away_market", 0):.4f}

Contexto deportivo:
{api_context}

Contexto cuotas:
{odds_context}

Responde con este JSON exacto:
{{
  "prob_home_ai": 0.0,
  "prob_draw_ai": 0.0,
  "prob_away_ai": 0.0,
  "ai_prediction": "local",
  "ai_confidence": "Alta",
  "risk_level": "Bajo",
  "summary": "resumen corto",
  "market_reading": "lectura corta del mercado",
  "team_context": "contexto corto de equipos",
  "draw_risk": "riesgo corto de empate",
  "expected_result": "2-0",
  "expected_goals_home_ai": 1.8,
  "expected_goals_away_ai": 0.5,
  "expected_total_goals_ai": 2.3,
  "goal_expectation_summary": "promedio de goles esperado",
  "luck_factor": "Medio",
  "luck_explanation": "explicación corta del factor suerte",
  "entropy_score": 0.0,
  "entropy_factor": "Medio",
  "entropy_explanation": "explicación corta de la incertidumbre del partido",
  "volatility_factors": ["penalti", "tarjeta roja", "rebote"],
  "expert_factors": ["calidad de ocasiones xG", "balón parado", "disciplina"],
  "key_factors": ["factor 1", "factor 2", "factor 3"],
  "red_flags": ["riesgo principal"],
  "sources_used": ["cuotas", "contexto disponible"]
}}

Reglas:
- prob_home_ai, prob_draw_ai y prob_away_ai deben sumar 1.
- expected_goals_home_ai y expected_goals_away_ai deben ser números decimales.
- expected_total_goals_ai debe ser la suma esperada de goles del partido.
- expected_result debe ser marcador probable en formato 1-0, 2-1, 1-1, etc.
- luck_factor debe ser Bajo, Medio o Alto.
- entropy_score debe ser un número entre 0 y 1.
- entropy_factor debe ser Bajo, Medio o Alto.
- Usa números decimales entre 0 y 1 para probabilidades, ejemplo 0.89.
- Si el favorito de mercado es muy fuerte, no respondas 0.33/0.34/0.33.
- summary máximo 250 caracteres.
"""

        payload = {
            "model": self.model,
            "input": fallback_prompt,
            "max_output_tokens": 3000,
        }

        try:
            response = client.responses.create(**payload)
            data = self._response_to_data(response)

            if data and self._has_probability_keys(data):
                return data

            return self._deterministic_fallback(
                match,
                reason="La IA devolvió respuesta vacía o incompleta incluso en fallback.",
            )

        except Exception as exc:
            return self._deterministic_fallback(
                match,
                reason=f"Falló el fallback de OpenAI: {exc}",
            )


    def _deterministic_fallback(
        self,
        match: dict[str, Any],
        reason: str = "",
    ) -> dict[str, Any]:
        """
        Fallback final sin IA textual.

        Usa probabilidades de mercado ajustadas para que la app no se detenga.
        Esto es mejor que devolver error, porque mantiene el análisis operativo.
        """
        home = _safe_float(match.get("prob_home_market"))
        draw = _safe_float(match.get("prob_draw_market"))
        away = _safe_float(match.get("prob_away_market"))

        total = home + draw + away

        if total <= 0:
            # Si no hay probabilidades de mercado, intenta calcular desde cuotas.
            home_odds = _safe_float(match.get("home_odds"))
            draw_odds = _safe_float(match.get("draw_odds"))
            away_odds = _safe_float(match.get("away_odds"))

            implied_home = 1 / home_odds if home_odds > 0 else 0
            implied_draw = 1 / draw_odds if draw_odds > 0 else 0
            implied_away = 1 / away_odds if away_odds > 0 else 0
            implied_total = implied_home + implied_draw + implied_away

            if implied_total > 0:
                home = implied_home / implied_total
                draw = implied_draw / implied_total
                away = implied_away / implied_total
            else:
                home, draw, away = 0.34, 0.32, 0.34
        else:
            home = home / total
            draw = draw / total
            away = away / total

        max_prob = max(home, draw, away)

        if home >= draw and home >= away:
            prediction = "local"
        elif away >= home and away >= draw:
            prediction = "visitante"
        else:
            prediction = "empate"

        if max_prob >= 0.70:
            confidence = "Alta"
        elif max_prob >= 0.55:
            confidence = "Media"
        else:
            confidence = "Baja"

        if max_prob >= 0.72 and draw < 0.20:
            risk = "Bajo"
        elif max_prob >= 0.58:
            risk = "Medio"
        else:
            risk = "Alto"

        data = {
            "_home_team_name": match.get("home", "Local"),
            "_away_team_name": match.get("away", "Visitante"),
            "prob_home_ai": home,
            "prob_draw_ai": draw,
            "prob_away_ai": away,
            "ai_prediction": prediction,
            "ai_confidence": confidence,
            "risk_level": risk,
            "summary": (
                "Fallback automático: OpenAI no entregó una respuesta utilizable. "
                "Se usaron probabilidades de mercado ajustadas para no detener el análisis."
            ),
            "market_reading": (
                "Lectura basada en cuotas y probabilidades implícitas ajustadas por margen."
            ),
            "team_context": (
                "Contexto limitado por respuesta vacía de IA; revisar análisis manual, noticias y alineaciones."
            ),
            "draw_risk": (
                "Riesgo de empate calculado desde la probabilidad ajustada del mercado."
            ),
            "expected_result": "1-0" if prediction == "local" else "0-1" if prediction == "visitante" else "1-1",
            "expected_goals_home_ai": None,
            "expected_goals_away_ai": None,
            "expected_total_goals_ai": None,
            "goal_expectation_summary": (
                "Goles esperados calculados de forma heurística por fallback."
            ),
            "luck_factor": "Medio",
            "luck_explanation": (
                "El fútbol tiene varianza por penales, rojas, VAR, rebotes, errores individuales y balón parado."
            ),
            "volatility_factors": [
                "Penales o VAR",
                "Tarjeta roja",
                "Balón parado",
                "Error individual o rebote",
            ],
            "expert_factors": [
                "Calidad de ocasiones tipo xG",
                "Balón parado",
                "Disciplina",
                "Contexto de grupo",
                "Diferencia de nivel estimada por mercado",
            ],
            "key_factors": [
                "Probabilidad de mercado ajustada",
                "Cuota del favorito",
                "Riesgo de empate",
            ],
            "red_flags": [
                "Respuesta de IA vacía; validar con noticias y alineaciones antes de tomar decisiones."
            ],
            "sources_used": [
                "Cuotas base",
                "Probabilidades ajustadas",
                "Fallback determinístico",
            ],
            "ai_fallback_used": True,
            "ai_fallback_reason": reason,
        }

        data = self._complete_expected_goals_and_luck(data)
        data = self._complete_entropy(data)
        data = self._complete_team_level_analysis(data)
        data = self._complete_betting_conclusion(data)

        return data


    def _build_prompt(
        self,
        match: dict[str, Any],
        api_context: str,
        odds_context: str,
    ) -> str:
        return f"""
Eres un analista deportivo cuantitativo especializado en fútbol internacional.

Objetivo:
Generar una predicción probabilística completa para un partido de fase de grupos del Mundial FIFA 2026.

Reglas:
- No prometas certeza.
- No digas que algo es seguro.
- No recomiendes apostar de forma irresponsable.
- Entrega una predicción prudente y basada en señales disponibles.
- Responde de forma concisa.
- No uses textos largos.
- Cierra siempre el JSON completo.
- Usa las cuotas como señal fuerte del mercado, pero no como única fuente.
- La suma de prob_home_ai + prob_draw_ai + prob_away_ai debe ser aproximadamente 1.0.
- No devuelvas probabilidades iguales 0.33/0.34/0.33 salvo que realmente no haya ninguna señal diferencial.
- Si el mercado tiene un favorito fuerte, explica si estás de acuerdo o si ves sobrevaloración.
- summary máximo 300 caracteres.
- market_reading máximo 250 caracteres.
- team_context máximo 250 caracteres.
- draw_risk máximo 200 caracteres.
- goal_expectation_summary máximo 250 caracteres.
- luck_explanation máximo 250 caracteres.
- key_factors máximo 4 elementos.
- red_flags máximo 3 elementos.
- sources_used máximo 4 elementos.
- volatility_factors máximo 4 elementos.
- expert_factors máximo 5 elementos.

Datos del partido:
- Partido: {match.get("home")} vs {match.get("away")}
- Grupo: {match.get("group")}
- Fecha Colombia: {match.get("date_col")} {match.get("time_col")}

{self._team_level_context(match.get("home"), match.get("away"))}

Cuotas base decimales:
- Local: {match.get("home_odds")}
- Empate: {match.get("draw_odds")}
- Visitante: {match.get("away_odds")}

Probabilidad de mercado ajustada:
- Local: {match.get("prob_home_market", 0):.4f}
- Empate: {match.get("prob_draw_market", 0):.4f}
- Visitante: {match.get("prob_away_market", 0):.4f}

Contexto API-Football, incluyendo H2H y promedios de goles en partidos oficiales no amistosos:
{api_context}

Contexto cuotas externas:
{odds_context}

Debes analizar:
1. Favorito del mercado.
2. Diferencia real de nivel entre selecciones.
3. Ranking FIFA/ELO o fuerza histórica reciente si está disponible.
4. Forma reciente.
5. Fortaleza ofensiva.
6. Fortaleza defensiva.
7. Riesgo de empate.
8. Lesiones, sanciones o rotaciones si hay señales disponibles.
9. Contexto del grupo.
10. Señales de que la cuota pueda estar sobrevalorando al favorito.
11. Resultado esperado en marcador exacto probable, ejemplo 2-0 o 1-1.
12. Promedio de goles esperado del local, visitante y total del partido.
13. Factor suerte o varianza del fútbol: penales, rojas, VAR, rebotes, autogoles, errores individuales, clima, portero inspirado.
14. Factores expertos adicionales: calidad de ocasiones tipo xG, balón parado, disciplina, estilo táctico, motivación/contexto de grupo y estado del partido.
15. Factor entropía: mide qué tan repartidas están las probabilidades entre local, empate y visitante. Entropía alta = partido más incierto. Entropía baja = favorito más claro.
16. Clasificación competitiva de equipos: Elite, Medio o Bajo competitivo. Bajo no significa malo; significa menor experiencia, menor profundidad o menor peso internacional relativo.

Devuelve un análisis completo y útil para interpretar el riesgo.
"""

    def _build_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "prob_home_ai": {"type": ["number", "string"]},
                "prob_draw_ai": {"type": ["number", "string"]},
                "prob_away_ai": {"type": ["number", "string"]},
                "ai_prediction": {
                    "type": "string",
                    "enum": ["local", "empate", "visitante"],
                },
                "ai_confidence": {
                    "type": "string",
                    "enum": ["Alta", "Media", "Baja"],
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["Bajo", "Medio", "Alto"],
                },
                "summary": {"type": "string", "maxLength": 350},
                "market_reading": {"type": "string", "maxLength": 300},
                "team_context": {"type": "string", "maxLength": 300},
                "draw_risk": {"type": "string", "maxLength": 250},

                "expected_result": {
                    "type": "string",
                    "maxLength": 20,
                    "description": "Marcador esperado, por ejemplo 2-0, 1-1 o 2-1.",
                },
                "expected_goals_home_ai": {"type": ["number", "string"]},
                "expected_goals_away_ai": {"type": ["number", "string"]},
                "expected_total_goals_ai": {"type": ["number", "string"]},
                "goal_expectation_summary": {"type": "string", "maxLength": 300},
                "luck_factor": {
                    "type": "string",
                    "enum": ["Bajo", "Medio", "Alto"],
                },
                "luck_explanation": {"type": "string", "maxLength": 300},
                "entropy_score": {"type": ["number", "string"]},
                "entropy_factor": {
                    "type": "string",
                    "enum": ["Bajo", "Medio", "Alto"],
                },
                "entropy_explanation": {"type": "string", "maxLength": 300},
                "volatility_factors": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string", "maxLength": 140},
                },
                "expert_factors": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 5,
                    "items": {"type": "string", "maxLength": 160},
                },

                "key_factors": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 4,
                    "items": {"type": "string", "maxLength": 160},
                },
                "red_flags": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {"type": "string", "maxLength": 160},
                },
                "sources_used": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {"type": "string", "maxLength": 120},
                },
            },
            "required": [
                "prob_home_ai",
                "prob_draw_ai",
                "prob_away_ai",
                "ai_prediction",
                "ai_confidence",
                "risk_level",
                "summary",
                "market_reading",
                "team_context",
                "draw_risk",
                "expected_result",
                "expected_goals_home_ai",
                "expected_goals_away_ai",
                "expected_total_goals_ai",
                "goal_expectation_summary",
                "luck_factor",
                "luck_explanation",
                "entropy_score",
                "entropy_factor",
                "entropy_explanation",
                "volatility_factors",
                "expert_factors",
                "key_factors",
                "red_flags",
                "sources_used",
            ],
        }

    def _extract_text_from_response(self, response: Any) -> str:
        """
        Extrae texto de distintas formas posibles de la Responses API.

        Algunos modelos pueden devolver output_text vacío si la respuesta viene
        en una estructura diferente o si se consume el presupuesto en razonamiento.
        """
        parts: list[str] = []

        def add(value: Any) -> None:
            if value is None:
                return

            value_text = str(value).strip()

            if value_text and value_text not in ["None", "[]", "{}"]:
                parts.append(value_text)

        try:
            output = getattr(response, "output", None)

            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict):
                        content = item.get("content", []) or []

                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict):
                                    add(c.get("text"))
                                    add(c.get("output_text"))
                                    add(c.get("value"))
                                else:
                                    add(getattr(c, "text", None))
                                    add(getattr(c, "output_text", None))
                                    add(getattr(c, "value", None))

                        add(item.get("text"))
                        add(item.get("output_text"))

                    else:
                        content = getattr(item, "content", []) or []

                        if isinstance(content, list):
                            for c in content:
                                add(getattr(c, "text", None))
                                add(getattr(c, "output_text", None))
                                add(getattr(c, "value", None))

                        add(getattr(item, "text", None))
                        add(getattr(item, "output_text", None))

            # Fallback adicional para SDKs que permiten model_dump
            if not parts and hasattr(response, "model_dump"):
                dumped = response.model_dump()

                def walk(obj: Any) -> None:
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key in ["text", "output_text", "value"] and isinstance(value, str):
                                add(value)
                            else:
                                walk(value)
                    elif isinstance(obj, list):
                        for value in obj:
                            walk(value)

                walk(dumped)

        except Exception:
            pass

        if parts:
            return "\n".join(parts)

        return ""

    def _normalize_ai_probabilities(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            home = _parse_probability(data.get("prob_home_ai"))
            draw = _parse_probability(data.get("prob_draw_ai"))
            away = _parse_probability(data.get("prob_away_ai"))

            total = home + draw + away

            if total <= 0:
                raise ValueError("Las probabilidades IA llegaron en cero.")

            data["prob_home_ai"] = home / total
            data["prob_draw_ai"] = draw / total
            data["prob_away_ai"] = away / total

        except Exception as exc:
            raise ValueError(
                f"La IA no entregó probabilidades válidas. Detalle: {exc}. "
                f"Datos recibidos: {data}"
            )

        return data

    def _complete_expected_goals_and_luck(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Completa resultado esperado, goles esperados y factor suerte si el modelo
        no los devuelve o los devuelve en formato inválido.
        """
        home_prob = _safe_float(data.get("prob_home_ai"))
        draw_prob = _safe_float(data.get("prob_draw_ai"))
        away_prob = _safe_float(data.get("prob_away_ai"))

        # Leer goles esperados si llegaron desde IA
        home_xg = _safe_float(data.get("expected_goals_home_ai"), default=-1)
        away_xg = _safe_float(data.get("expected_goals_away_ai"), default=-1)
        total_xg = _safe_float(data.get("expected_total_goals_ai"), default=-1)

        # Si faltan, calcular estimación heurística a partir de probabilidades
        if home_xg < 0 or away_xg < 0 or total_xg <= 0:
            superiority = abs(home_prob - away_prob)
            base_total = 2.25 + superiority * 1.05 - draw_prob * 0.45
            total_xg = _clamp(base_total, 1.55, 4.25)

            non_draw_total = home_prob + away_prob
            if non_draw_total > 0:
                home_share = home_prob / non_draw_total
            else:
                home_share = 0.50

            # Suavizar para no irse a extremos irreales
            home_share = _clamp(home_share, 0.18, 0.82)
            home_xg = total_xg * home_share
            away_xg = total_xg * (1 - home_share)

        home_xg = round(_clamp(home_xg, 0.0, 5.0), 2)
        away_xg = round(_clamp(away_xg, 0.0, 5.0), 2)
        total_xg = round(_clamp(total_xg if total_xg > 0 else home_xg + away_xg, 0.5, 8.0), 2)

        data["expected_goals_home_ai"] = home_xg
        data["expected_goals_away_ai"] = away_xg
        data["expected_total_goals_ai"] = round(home_xg + away_xg, 2)

        # Resultado esperado en marcador entero
        expected_result = str(data.get("expected_result", "")).strip()
        if not expected_result or not re.match(r"^\d+\s*-\s*\d+$", expected_result):
            home_goals = int(round(home_xg))
            away_goals = int(round(away_xg))

            # Ajuste para que el marcador esperado no contradiga demasiado la predicción
            pred = data.get("ai_prediction")
            if pred == "local" and home_goals <= away_goals:
                home_goals = away_goals + 1
            elif pred == "visitante" and away_goals <= home_goals:
                away_goals = home_goals + 1
            elif pred == "empate":
                avg = int(round((home_xg + away_xg) / 2))
                home_goals = avg
                away_goals = avg

            data["expected_result"] = f"{home_goals}-{away_goals}"

        if "goal_expectation_summary" not in data or not isinstance(data.get("goal_expectation_summary"), str) or len(data.get("goal_expectation_summary", "").strip()) < 10:
            data["goal_expectation_summary"] = (
                f"Promedio estimado de goles: local {home_xg}, visitante {away_xg}, "
                f"total {data['expected_total_goals_ai']}. Resultado esperado: {data['expected_result']}."
            )

        # Factor suerte / varianza
        luck_factor = data.get("luck_factor")
        if luck_factor not in ["Bajo", "Medio", "Alto"]:
            max_prob = max(home_prob, draw_prob, away_prob)
            if draw_prob >= 0.28 or max_prob < 0.52:
                luck_factor = "Alto"
            elif draw_prob >= 0.20 or max_prob < 0.65:
                luck_factor = "Medio"
            else:
                luck_factor = "Bajo"
            data["luck_factor"] = luck_factor

        if "luck_explanation" not in data or not isinstance(data.get("luck_explanation"), str) or len(data.get("luck_explanation", "").strip()) < 10:
            if data["luck_factor"] == "Alto":
                data["luck_explanation"] = "Partido sensible a eventos aleatorios: penalti, roja, rebote, VAR, error individual o portero inspirado pueden cambiar el resultado."
            elif data["luck_factor"] == "Medio":
                data["luck_explanation"] = "Existe varianza normal de fútbol: una jugada aislada, balón parado o decisión arbitral puede modificar el escenario."
            else:
                data["luck_explanation"] = "La diferencia estimada reduce el peso de la suerte, aunque ningún partido elimina completamente la varianza."

        if "volatility_factors" not in data or not isinstance(data.get("volatility_factors"), list) or len(data.get("volatility_factors", [])) < 1:
            data["volatility_factors"] = [
                "Penales o VAR",
                "Tarjeta roja",
                "Balón parado",
                "Error individual o rebote",
            ]

        if "expert_factors" not in data or not isinstance(data.get("expert_factors"), list) or len(data.get("expert_factors", [])) < 3:
            data["expert_factors"] = [
                "Calidad de ocasiones tipo xG",
                "Balón parado y juego aéreo",
                "Disciplina: rojas, faltas y penales",
                "Contexto de grupo y motivación",
                "Duelo táctico y ritmo del partido",
            ]

        return data


    def _complete_entropy(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Calcula entropía normalizada con base en las probabilidades de local, empate y visitante.

        Interpretación:
        - 0.00 = casi sin incertidumbre, un resultado domina totalmente.
        - 1.00 = máxima incertidumbre, probabilidades muy repartidas.
        """
        probs = [
            _safe_float(data.get("prob_home_ai")),
            _safe_float(data.get("prob_draw_ai")),
            _safe_float(data.get("prob_away_ai")),
        ]

        total = sum(probs)

        if total <= 0:
            data["entropy_score"] = None
            data["entropy_factor"] = "Alto"
            data["entropy_explanation"] = "No fue posible calcular la entropía porque las probabilidades no son válidas."
            return data

        probs = [max(0.0, p / total) for p in probs]

        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * math.log(p)

        max_entropy = math.log(3)
        entropy_score = entropy / max_entropy if max_entropy > 0 else 0.0
        entropy_score = round(_clamp(entropy_score, 0.0, 1.0), 4)

        data["entropy_score"] = entropy_score

        if entropy_score >= 0.90:
            data["entropy_factor"] = "Alto"
            data["entropy_explanation"] = (
                "Las probabilidades están muy repartidas; el partido es abierto y tiene alta incertidumbre."
            )
        elif entropy_score >= 0.75:
            data["entropy_factor"] = "Medio"
            data["entropy_explanation"] = (
                "Hay un favorito, pero empate o sorpresa aún tienen peso relevante en el resultado."
            )
        else:
            data["entropy_factor"] = "Bajo"
            data["entropy_explanation"] = (
                "Las probabilidades se concentran en un resultado principal; existe un favorito más claro."
            )

        return data



    def _normalize_team_key(self, team_name: Any) -> str:
        text = str(team_name or "").lower().strip()
        text = text.replace(".", "").replace("-", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    def _team_level_info(self, team_name: Any) -> dict[str, str]:
        key = self._normalize_team_key(team_name)
        info = TEAM_LEVELS.get(key)

        if info:
            return {
                "level": info.get("level", "Medio"),
                "comment": info.get("comment", "Clasificación competitiva disponible."),
            }

        return {
            "level": "Medio",
            "comment": "Sin clasificación específica; la app lo trata como Medio competitivo por defecto y exige cautela.",
        }

    def _team_level_context(self, home: Any, away: Any) -> str:
        home_info = self._team_level_info(home)
        away_info = self._team_level_info(away)
        home_level = home_info["level"]
        away_level = away_info["level"]
        gap = TEAM_LEVEL_ORDER.get(home_level, 2) - TEAM_LEVEL_ORDER.get(away_level, 2)

        if abs(gap) >= 2:
            matchup = "Diferencia alta de nivel competitivo"
        elif abs(gap) == 1:
            matchup = "Diferencia moderada de nivel competitivo"
        else:
            matchup = "Nivel competitivo similar"

        return (
            f"Clasificación competitiva previa: {home} = {home_level}. {home_info['comment']} "
            f"{away} = {away_level}. {away_info['comment']} "
            f"Lectura del cruce: {matchup}. Esta clasificación no decide sola la predicción; "
            f"debe combinarse con cuotas, entropía, suerte, goles oficiales, forma y contexto del grupo."
        )

    def _complete_team_level_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        home_name = str(data.get("_home_team_name") or "Local").strip() or "Local"
        away_name = str(data.get("_away_team_name") or "Visitante").strip() or "Visitante"

        home_info = self._team_level_info(home_name)
        away_info = self._team_level_info(away_name)

        home_level = home_info["level"]
        away_level = away_info["level"]
        home_score = TEAM_LEVEL_ORDER.get(home_level, 2)
        away_score = TEAM_LEVEL_ORDER.get(away_level, 2)
        gap = home_score - away_score

        data["home_team_level"] = home_level
        data["away_team_level"] = away_level
        data["home_team_level_comment"] = home_info["comment"]
        data["away_team_level_comment"] = away_info["comment"]
        data["team_level_gap"] = gap

        if abs(gap) >= 2:
            matchup = "Elite vs Bajo competitivo"
        elif abs(gap) == 1:
            matchup = "Diferencia moderada de nivel"
        else:
            matchup = "Nivel competitivo similar"

        data["team_level_matchup"] = matchup

        entropy_score = _safe_float(data.get("entropy_score"))
        risk_level = str(data.get("risk_level", "")).strip()
        luck_factor = str(data.get("luck_factor", "")).strip()
        team_level_betting_comment = str(data.get("team_level_betting_comment", "")).strip()
        clear_favorite = str(data.get("clear_favorite", "")).strip().lower() in ["sí", "si", "true", "1"]
        favorite_team = str(data.get("favorite_team", "")).strip()

        if abs(gap) >= 2:
            stronger = home_name if gap > 0 else away_name
            weaker = away_name if gap > 0 else home_name
            caution = (
                f"Hay diferencia alta de jerarquía: {stronger} tiene más experiencia/profundidad que {weaker}. "
                "Aun así, revisar rotación, intensidad, roja, penal o baja motivación antes de asumir apuesta directa."
            )
        elif abs(gap) == 1:
            stronger = home_name if gap > 0 else away_name
            weaker = away_name if gap > 0 else home_name
            caution = (
                f"Hay diferencia moderada: {stronger} parte con ventaja de jerarquía frente a {weaker}, "
                "pero no es suficiente por sí sola para forzar apuesta directa."
            )
        else:
            caution = (
                "Los equipos tienen nivel competitivo similar; conviene ser prudente con ganador directo "
                "y revisar doble oportunidad, goles o no apostar."
            )

        if entropy_score >= 0.90:
            caution += " La entropía alta refuerza la cautela porque las probabilidades están muy repartidas."
        if risk_level == "Alto":
            caution += " El riesgo general alto reduce valor en mercados 1X2 directos."
        if luck_factor == "Alto":
            caution += " El factor suerte alto aumenta la exposición a eventos aleatorios."

        data["team_level_caution"] = caution

        if clear_favorite and favorite_team:
            data["team_level_betting_comment"] = (
                f"La clasificación de niveles respalda revisar al favorito {favorite_team}, "
                "pero la decisión final debe validarse con entropía, riesgo, goles esperados y cuotas."
            )
        elif abs(gap) >= 1:
            data["team_level_betting_comment"] = (
                "Existe diferencia de nivel, pero la app no detecta favorito suficientemente claro; "
                "preferir cobertura, goles o esperar mejor señal."
            )
        else:
            data["team_level_betting_comment"] = (
                "Nivel similar: evitar confianza excesiva en ganador directo salvo que mercado, entropía y forma lo respalden."
            )

        return data

    def _complete_betting_conclusion(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Genera una conclusión tipo mercado de apuesta.

        Incluye:
        - Si hay favorito claro.
        - Cuál es el favorito.
        - Si la IA apostaría al favorito directo.
        - Si la IA preferiría cubrir al favorito con gana/empata.
        - Si prefiere mercado de goles o no apostar.
        """
        home = _safe_float(data.get("prob_home_ai"))
        draw = _safe_float(data.get("prob_draw_ai"))
        away = _safe_float(data.get("prob_away_ai"))

        total_probs = home + draw + away
        if total_probs > 0:
            home = home / total_probs
            draw = draw / total_probs
            away = away / total_probs
        else:
            home, draw, away = 0.34, 0.32, 0.34

        home_name = str(data.get("_home_team_name") or "Local").strip() or "Local"
        away_name = str(data.get("_away_team_name") or "Visitante").strip() or "Visitante"

        outcomes = [
            {"side": "local", "team": home_name, "selection": "Gana local", "prob": home},
            {"side": "empate", "team": "Empate", "selection": "Empate", "prob": draw},
            {"side": "visitante", "team": away_name, "selection": "Gana visitante", "prob": away},
        ]
        outcomes_sorted = sorted(outcomes, key=lambda item: item["prob"], reverse=True)
        favorite = outcomes_sorted[0]
        second = outcomes_sorted[1]
        favorite_prob = float(favorite["prob"])
        favorite_margin = favorite_prob - float(second["prob"])

        entropy_score = _safe_float(data.get("entropy_score"))
        risk_level = str(data.get("risk_level", "")).strip()
        luck_factor = str(data.get("luck_factor", "")).strip()
        team_level_betting_comment = str(data.get("team_level_betting_comment", "")).strip()

        # Definición práctica de favorito claro:
        # - Debe ser local o visitante, no empate.
        # - Debe tener probabilidad y margen relevantes.
        # - Si la entropía es muy alta, no lo marcamos como claro aunque gane en probabilidad.
        clear_favorite = (
            favorite["side"] in ["local", "visitante"]
            and favorite_prob >= 0.58
            and favorite_margin >= 0.12
            and entropy_score < 0.90
        )

        if clear_favorite and favorite_prob >= 0.70 and favorite_margin >= 0.20:
            favorite_strength = "Muy claro"
        elif clear_favorite:
            favorite_strength = "Claro"
        elif favorite["side"] in ["local", "visitante"] and favorite_prob >= 0.50:
            favorite_strength = "Moderado"
        else:
            favorite_strength = "No claro"

        if favorite["side"] == "local":
            favorite_double_chance = "Local o empate 1X"
            favorite_direct_selection = "Gana local"
        elif favorite["side"] == "visitante":
            favorite_double_chance = "Visitante o empate X2"
            favorite_direct_selection = "Gana visitante"
        else:
            favorite_double_chance = "No aplica"
            favorite_direct_selection = "Empate"

        data["clear_favorite"] = "Sí" if clear_favorite else "No"
        data["favorite_side"] = favorite["side"]
        data["favorite_team"] = favorite["team"]
        data["favorite_probability"] = round(favorite_prob, 4)
        data["favorite_margin_to_second"] = round(favorite_margin, 4)
        data["favorite_strength"] = favorite_strength
        data["favorite_double_chance_selection"] = favorite_double_chance

        if clear_favorite:
            data["favorite_conclusion"] = (
                f"Favorito {favorite_strength.lower()}: {favorite['team']} "
                f"con probabilidad IA {round(favorite_prob * 100, 1)}% y margen "
                f"de {round(favorite_margin * 100, 1)} puntos frente al segundo escenario."
            )
        elif favorite["side"] in ["local", "visitante"]:
            data["favorite_conclusion"] = (
                f"Hay favorito moderado: {favorite['team']}, pero no es suficientemente claro "
                f"por probabilidad, margen o entropía del partido."
            )
        else:
            data["favorite_conclusion"] = (
                "No hay favorito claro; el empate o la dispersión de probabilidades hacen el partido más abierto."
            )

        dc_home_draw = _clamp(home + draw, 0.0, 1.0)
        dc_away_draw = _clamp(away + draw, 0.0, 1.0)
        dc_home_away = _clamp(home + away, 0.0, 1.0)

        data["prob_double_chance_home_draw"] = round(dc_home_draw, 4)
        data["prob_double_chance_away_draw"] = round(dc_away_draw, 4)
        data["prob_double_chance_home_away"] = round(dc_home_away, 4)

        expected_total_goals = _safe_float(data.get("expected_total_goals_ai"))

        # Si no hay goles esperados, usar promedios oficiales si están disponibles.
        if expected_total_goals <= 0:
            home_total_official = _safe_float(data.get("home_avg_total_goals_official"))
            away_total_official = _safe_float(data.get("away_avg_total_goals_official"))

            if home_total_official > 0 and away_total_official > 0:
                expected_total_goals = (home_total_official + away_total_official) / 2
            else:
                max_prob = max(home, draw, away)
                expected_total_goals = 2.10 + abs(home - away) * 0.90 - draw * 0.30 + max(0.0, max_prob - 0.60) * 0.30
                expected_total_goals = _clamp(expected_total_goals, 1.25, 4.30)

        expected_total_goals = _clamp(expected_total_goals, 0.20, 7.00)

        # Probabilidades over con Poisson total de goles.
        prob_over_0_5 = 1 - math.exp(-expected_total_goals)
        prob_over_1_5 = 1 - math.exp(-expected_total_goals) * (1 + expected_total_goals)
        prob_over_2_5 = 1 - math.exp(-expected_total_goals) * (
            1 + expected_total_goals + (expected_total_goals ** 2) / 2
        )

        data["prob_over_0_5_goals"] = round(_clamp(prob_over_0_5, 0.0, 1.0), 4)
        data["prob_over_1_5_goals"] = round(_clamp(prob_over_1_5, 0.0, 1.0), 4)
        data["prob_over_2_5_goals"] = round(_clamp(prob_over_2_5, 0.0, 1.0), 4)

        candidates: list[dict[str, Any]] = []

        # Mercado resultado final 1X2.
        if home >= draw and home >= away:
            candidates.append({
                "market": "Resultado final 1X2",
                "selection": "Gana local",
                "prob": home,
                "score": home,
                "reason": "La mayor probabilidad individual está en la victoria del local.",
            })
        elif away >= home and away >= draw:
            candidates.append({
                "market": "Resultado final 1X2",
                "selection": "Gana visitante",
                "prob": away,
                "score": away,
                "reason": "La mayor probabilidad individual está en la victoria del visitante.",
            })
        else:
            candidates.append({
                "market": "Resultado final 1X2",
                "selection": "Empate",
                "prob": draw,
                "score": draw,
                "reason": "El empate es el resultado individual con mayor probabilidad.",
            })

        # Mercado doble oportunidad.
        dc_options = [
            ("Doble oportunidad", "Local o empate 1X", dc_home_draw),
            ("Doble oportunidad", "Visitante o empate X2", dc_away_draw),
            ("Doble oportunidad", "Local o visitante 12", dc_home_away),
        ]
        best_dc = max(dc_options, key=lambda item: item[2])
        candidates.append({
            "market": best_dc[0],
            "selection": best_dc[1],
            "prob": best_dc[2],
            # Penalización leve porque doble oportunidad normalmente tiene cuota más baja.
            "score": best_dc[2] - 0.04,
            "reason": "La doble oportunidad cubre dos de tres resultados y reduce exposición al empate o sorpresa.",
        })

        # Si hay favorito claro, evaluar explícitamente la opción gana/empata del favorito.
        if clear_favorite and favorite_double_chance != "No aplica":
            favorite_dc_prob = dc_home_draw if favorite["side"] == "local" else dc_away_draw
            candidates.append({
                "market": "Doble oportunidad favorito",
                "selection": favorite_double_chance,
                "prob": favorite_dc_prob,
                "score": favorite_dc_prob - 0.025,
                "reason": f"Cubre que {favorite['team']} gane o empate, reduciendo el riesgo frente al 1X2 directo.",
            })

        # Mercado total goles.
        candidates.append({
            "market": "Total goles",
            "selection": "Más de 0.5 goles",
            "prob": prob_over_0_5,
            # Muy probable, pero usualmente de valor/cuota bajo.
            "score": prob_over_0_5 - 0.08,
            "reason": "El modelo estima alta probabilidad de al menos un gol en el partido.",
        })
        candidates.append({
            "market": "Total goles",
            "selection": "Más de 1.5 goles",
            "prob": prob_over_1_5,
            "score": prob_over_1_5 - 0.02,
            "reason": "El promedio esperado de goles respalda un escenario de dos o más goles.",
        })
        if prob_over_2_5 >= 0.56 and expected_total_goals >= 2.55:
            candidates.append({
                "market": "Total goles",
                "selection": "Más de 2.5 goles",
                "prob": prob_over_2_5,
                "score": prob_over_2_5 - 0.01,
                "reason": "El promedio esperado de goles permite considerar un partido de tres o más goles.",
            })

        adjusted_candidates: list[dict[str, Any]] = []
        for candidate in candidates:
            score = float(candidate["score"])

            # En partidos de alta incertidumbre, castigar más el 1X2.
            if entropy_score >= 0.90 and candidate["market"] == "Resultado final 1X2":
                score -= 0.08
            elif entropy_score >= 0.80 and candidate["market"] == "Resultado final 1X2":
                score -= 0.04

            if risk_level == "Alto" and candidate["market"] == "Resultado final 1X2":
                score -= 0.07
            elif risk_level == "Medio" and candidate["market"] == "Resultado final 1X2":
                score -= 0.03

            if luck_factor == "Alto" and candidate["market"] == "Resultado final 1X2":
                score -= 0.04

            candidate["adjusted_score"] = score
            adjusted_candidates.append(candidate)

        best = max(adjusted_candidates, key=lambda item: item["adjusted_score"])

        best_prob = float(best["prob"])
        best_score = float(best["adjusted_score"])

        def classify_bet_vs_favorite(selection: str, market: str) -> str:
            if not clear_favorite:
                if market == "Total goles":
                    return "No hay favorito claro; la IA prefiere mercado de goles."
                if market == "Sin apuesta":
                    return "No hay favorito claro; la IA no apuesta."
                return "No hay favorito claro; la IA evita tomar favorito directo."

            if selection == favorite_direct_selection and market == "Resultado final 1X2":
                return f"Apuesta al favorito directo: {favorite['team']} gana."

            if selection == favorite_double_chance:
                return f"Apuesta gana o empata favorito: {favorite['team']} gana o empata."

            if market == "Total goles":
                return f"Hay favorito claro ({favorite['team']}), pero la IA prefiere mercado de goles."

            if market == "Sin apuesta":
                return f"Hay favorito claro ({favorite['team']}), pero la IA no ve valor suficiente para apostar."

            return f"Hay favorito claro ({favorite['team']}), pero la IA prefiere otro mercado."

        # Umbral mínimo para no forzar una apuesta en partidos sin señal suficiente.
        if best_prob < 0.58 or best_score < 0.54:
            data["ai_bet_market"] = "Sin apuesta"
            data["ai_bet_selection"] = "No apostar"
            data["ai_bet_probability"] = round(best_prob, 4)
            data["ai_bet_confidence"] = "Baja"
            data["ai_bet_vs_favorite"] = classify_bet_vs_favorite("No apostar", "Sin apuesta")
            data["favorite_bet_recommendation"] = data["ai_bet_vs_favorite"]
            data["ai_bet_conclusion"] = (
                f"{data['favorite_conclusion']} {data['ai_bet_vs_favorite']}"
            )
            data["ai_bet_reason"] = (
                "La mejor opción no supera el umbral mínimo de confianza. "
                "Conviene esperar alineaciones, noticias o mejores cuotas. "
                + team_level_betting_comment
            )
            return data

        if best_prob >= 0.78 and best_score >= 0.70:
            confidence = "Alta"
        elif best_prob >= 0.66 and best_score >= 0.61:
            confidence = "Media"
        else:
            confidence = "Baja"

        data["ai_bet_market"] = best["market"]
        data["ai_bet_selection"] = best["selection"]
        data["ai_bet_probability"] = round(best_prob, 4)
        data["ai_bet_confidence"] = confidence
        data["ai_bet_vs_favorite"] = classify_bet_vs_favorite(best["selection"], best["market"])
        data["favorite_bet_recommendation"] = data["ai_bet_vs_favorite"]
        data["ai_bet_conclusion"] = (
            f"{data['favorite_conclusion']} {data['ai_bet_vs_favorite']} "
            f"Selección sugerida: {best['selection']} ({best['market']}) con confianza {confidence}."
        )
        data["ai_bet_reason"] = (best["reason"] + " " + team_level_betting_comment).strip()

        return data

    def _validate_ai_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Valida y completa la respuesta de IA.

        Importante:
        - Las probabilidades sí son obligatorias.
        - Los textos de análisis se completan si la IA los omite.
        - Los goles esperados también se completan con una heurística si faltan.
        """
        required_probs = [
            "prob_home_ai",
            "prob_draw_ai",
            "prob_away_ai",
        ]

        missing_probs = [key for key in required_probs if key not in data]

        if missing_probs:
            raise ValueError(f"La IA no entregó probabilidades obligatorias: {missing_probs}")

        if "ai_prediction" not in data or data.get("ai_prediction") not in ["local", "empate", "visitante"]:
            home = float(data.get("prob_home_ai", 0) or 0)
            draw = float(data.get("prob_draw_ai", 0) or 0)
            away = float(data.get("prob_away_ai", 0) or 0)

            if home >= draw and home >= away:
                data["ai_prediction"] = "local"
            elif away >= home and away >= draw:
                data["ai_prediction"] = "visitante"
            else:
                data["ai_prediction"] = "empate"

        if "ai_confidence" not in data or data.get("ai_confidence") not in ["Alta", "Media", "Baja"]:
            max_prob = max(
                float(data.get("prob_home_ai", 0) or 0),
                float(data.get("prob_draw_ai", 0) or 0),
                float(data.get("prob_away_ai", 0) or 0),
            )

            if max_prob >= 0.70:
                data["ai_confidence"] = "Alta"
            elif max_prob >= 0.55:
                data["ai_confidence"] = "Media"
            else:
                data["ai_confidence"] = "Baja"

        if "risk_level" not in data or data.get("risk_level") not in ["Bajo", "Medio", "Alto"]:
            draw_prob = float(data.get("prob_draw_ai", 0) or 0)
            max_prob = max(
                float(data.get("prob_home_ai", 0) or 0),
                float(data.get("prob_draw_ai", 0) or 0),
                float(data.get("prob_away_ai", 0) or 0),
            )

            if max_prob >= 0.72 and draw_prob < 0.20:
                data["risk_level"] = "Bajo"
            elif max_prob >= 0.58:
                data["risk_level"] = "Medio"
            else:
                data["risk_level"] = "Alto"

        if "summary" not in data or not isinstance(data.get("summary"), str) or len(data.get("summary", "").strip()) < 10:
            data["summary"] = (
                "Predicción generada con base en cuotas ajustadas, contexto disponible "
                "y análisis probabilístico. Revisar noticias y alineaciones antes del partido."
            )

        if "market_reading" not in data or not isinstance(data.get("market_reading"), str) or len(data.get("market_reading", "").strip()) < 10:
            data["market_reading"] = (
                "El mercado se interpreta a partir de las cuotas base y su probabilidad ajustada, "
                "considerando al favorito como la selección con menor cuota."
            )

        if "team_context" not in data or not isinstance(data.get("team_context"), str) or len(data.get("team_context", "").strip()) < 10:
            data["team_context"] = (
                "Contexto estimado con la información disponible de selecciones, diferencia de nivel "
                "y señales generales del mercado."
            )

        if "draw_risk" not in data or not isinstance(data.get("draw_risk"), str) or len(data.get("draw_risk", "").strip()) < 10:
            draw_prob = float(data.get("prob_draw_ai", 0) or 0)

            if draw_prob >= 0.25:
                data["draw_risk"] = "Riesgo de empate relevante; la probabilidad de igualdad es alta para tomar el favorito como fijo."
            elif draw_prob >= 0.18:
                data["draw_risk"] = "Riesgo de empate medio; el favorito domina, pero el empate sigue siendo un escenario posible."
            else:
                data["draw_risk"] = "Riesgo de empate bajo; el mercado y la IA favorecen claramente a una selección."

        data = self._complete_expected_goals_and_luck(data)
        data = self._complete_entropy(data)
        data = self._complete_team_level_analysis(data)
        data = self._complete_betting_conclusion(data)

        if "key_factors" not in data or not isinstance(data.get("key_factors"), list) or len(data.get("key_factors", [])) < 3:
            data["key_factors"] = [
                "Probabilidad de mercado ajustada",
                "Diferencia estimada de nivel entre selecciones",
                "Lectura de riesgo según cuota favorita y empate",
            ]

        if "red_flags" not in data or not isinstance(data.get("red_flags"), list) or len(data.get("red_flags", [])) < 1:
            data["red_flags"] = [
                "Revisar alineaciones, lesiones y noticias cercanas al partido."
            ]

        if "sources_used" not in data or not isinstance(data.get("sources_used"), list) or len(data.get("sources_used", [])) < 1:
            data["sources_used"] = [
                "Cuotas base",
                "Probabilidades ajustadas",
                "Contexto disponible en la app",
            ]

        return data
