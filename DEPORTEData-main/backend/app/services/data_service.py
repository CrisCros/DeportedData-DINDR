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

    def annual_totals(self) -> pd.DataFrame:
        csv_path = self._dataset_path()
        df = pd.read_csv(csv_path)

        expected_columns = {"periodo", "valor", "sexo_edad_estudios"}
        missing = expected_columns - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"El CSV no contiene columnas requeridas: {', '.join(sorted(missing))}",
            )

        totals = df[df["sexo_edad_estudios"].str.upper() == "TOTAL"].copy()
        totals["year"] = pd.to_numeric(totals["periodo"], errors="coerce")
        totals["empleo"] = pd.to_numeric(totals["valor"], errors="coerce")
        totals = totals.dropna(subset=["year", "empleo"])

        if totals.empty:
            raise HTTPException(status_code=500, detail="No hay datos válidos de empleo total en el CSV.")

        totals = totals.sort_values("year")
        return totals[["year", "empleo"]].reset_index(drop=True)

    def dashboard_kpis(self) -> dict:
        totals = self.annual_totals()

        latest = totals.iloc[-1]
        previous = totals.iloc[-2] if len(totals) > 1 else latest
        growth_pct = ((latest["empleo"] - previous["empleo"]) / previous["empleo"] * 100) if previous["empleo"] else 0.0

        last_values = [
            {"year": int(row.year), "empleo": round(float(row.empleo), 1)}
            for row in totals.tail(5).itertuples(index=False)
        ]

        return {
            "empleo_total": round(float(latest["empleo"]), 1),
            "growth_pct": round(float(growth_pct), 2),
            "latest_year": int(latest["year"]),
            "latest_values": last_values,
        }

    def dashboard_series(self) -> dict:
        totals = self.annual_totals()
        return {
            "years": [int(year) for year in totals["year"].tolist()],
            "values": [round(float(value), 1) for value in totals["empleo"].tolist()],
        }

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
            first_year = series["years"][0]
            last_year = series["years"][-1]
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
