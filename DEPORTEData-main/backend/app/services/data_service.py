from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from app.core.config import DATA_DIR, FALLBACK_DATA_DIR

ANNUAL_FILE_NAME = "medias_anuales_demografia.csv"


class DataService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _dataset_path(self) -> Path:
        preferred = self.data_dir / ANNUAL_FILE_NAME
        if preferred.exists():
            return preferred

        fallback = FALLBACK_DATA_DIR / ANNUAL_FILE_NAME
        if fallback.exists():
            return fallback

        raise HTTPException(
            status_code=500,
            detail=(
                f"No se encontró el dataset '{ANNUAL_FILE_NAME}' en '{self.data_dir}' "
                f"ni en '{FALLBACK_DATA_DIR}'."
            ),
        )

    def _read_csv(self, csv_path: Path) -> pd.DataFrame:
        # CSVs públicos pueden venir con distintas codificaciones.
        for encoding in ("utf-8", "latin-1"):
            try:
                return pd.read_csv(csv_path, sep=",", encoding=encoding)
            except UnicodeDecodeError:
                continue

        raise HTTPException(status_code=500, detail="No se pudo leer el CSV con codificación soportada")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized.columns = [col.strip().lower().replace(" ", "_") for col in normalized.columns]
        return normalized

    def annual_totals(self) -> pd.DataFrame:
        csv_path = self._dataset_path()
        df = self._read_csv(csv_path)
        df = self._normalize_columns(df)

        expected_columns = {"periodo", "valor", "sexo_edad_estudios"}
        missing = expected_columns - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"El CSV no contiene columnas requeridas: {', '.join(sorted(missing))}",
            )

        cleaned = df.copy()

        # 1) Filtramos solo total poblacional para evitar series "exploded" por segmentos.
        cleaned = cleaned[cleaned["sexo_edad_estudios"].astype(str).str.upper().str.strip() == "TOTAL"]

        # 2) Limpieza de tipos y nulos.
        cleaned["periodo"] = cleaned["periodo"].astype(str).str.extract(r"(\d{4})", expand=False)
        cleaned["year"] = pd.to_numeric(cleaned["periodo"], errors="coerce")
        cleaned["valor"] = cleaned["valor"].astype(str).str.replace(",", ".", regex=False)
        cleaned["value"] = pd.to_numeric(cleaned["valor"], errors="coerce")
        cleaned = cleaned.dropna(subset=["year", "value"])

        # 3) Eliminamos valores imposibles.
        cleaned = cleaned[cleaned["value"] >= 0]

        # 4) Quitamos duplicados exactos y agregamos por año para tener 1 punto/año.
        cleaned = cleaned.drop_duplicates(subset=["year", "value"])
        annual = (
            cleaned.groupby("year", as_index=False)["value"]
            .mean()
            .sort_values("year")
        )

        # 5) Outliers extremos (regla IQR) solo si hay suficiente historia.
        if len(annual) >= 8:
            q1 = annual["value"].quantile(0.25)
            q3 = annual["value"].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr
            annual = annual[(annual["value"] >= lower) & (annual["value"] <= upper)]

        annual["year"] = annual["year"].astype(int)
        annual["value"] = annual["value"].astype(float)

        if annual.empty:
            raise HTTPException(status_code=500, detail="No hay datos válidos de empleo total tras limpieza.")

        return annual.reset_index(drop=True)

    def dashboard_kpis(self) -> dict:
        annual = self.annual_totals()

        latest = annual.iloc[-1]
        previous = annual.iloc[-2] if len(annual) > 1 else latest

        previous_value = float(previous["value"])
        growth_pct = ((float(latest["value"]) - previous_value) / previous_value * 100) if previous_value else 0.0

        latest_values = [
            {"year": int(row.year), "value": round(float(row.value), 1)}
            for row in annual.tail(5).itertuples(index=False)
        ]

        return {
            "empleo_total": round(float(latest["value"]), 1),
            "growth_pct": round(float(growth_pct), 2),
            "latest_year": int(latest["year"]),
            "latest_values": latest_values,
        }

    def dashboard_series(self) -> list[dict]:
        annual = self.annual_totals()
        return [
            {"year": int(row.year), "value": round(float(row.value), 1)}
            for row in annual.itertuples(index=False)
        ]

    def answer_chat(self, message: str) -> str:
        clean_msg = message.lower()
        kpis = self.dashboard_kpis()
        series = self.dashboard_series()

        if "crec" in clean_msg or "sub" in clean_msg or "baj" in clean_msg:
            trend = "creció" if kpis["growth_pct"] >= 0 else "disminuyó"
            return (
                f"Entre {kpis['latest_values'][-2]['year']} y {kpis['latest_year']}, el empleo deportivo {trend} "
                f"un {abs(kpis['growth_pct'])}% y cerró en {kpis['empleo_total']} miles de personas."
            )

        if "año" in clean_msg or "serie" in clean_msg or "histor" in clean_msg:
            first_year = series[0]["year"]
            last_year = series[-1]["year"]
            return (
                f"Tengo datos anuales desde {first_year} hasta {last_year}. "
                f"El valor más reciente es {kpis['empleo_total']} miles de personas en {kpis['latest_year']}."
            )

        return (
            f"El último dato de empleo deportivo es {kpis['empleo_total']} miles en {kpis['latest_year']}, "
            f"con una variación interanual de {kpis['growth_pct']}%."
        )


@lru_cache
def get_data_service() -> DataService:
    return DataService(data_dir=DATA_DIR)
