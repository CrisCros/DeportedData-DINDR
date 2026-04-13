from pathlib import Path

import pandas as pd
import pytest

from app.services.data_service import ANNUAL_FILE_NAME, DataService


@pytest.fixture
def sample_service(tmp_path: Path) -> DataService:
    data = pd.DataFrame(
        [
            {
                "indicador": "EMPLEO VINCULADO AL DEPORTE: Valores absolutos (En miles)",
                "sexo_edad_estudios": "TOTAL",
                "periodo": "2020",
                "valor": "100",
            },
            {
                "indicador": "EMPLEO VINCULADO AL DEPORTE: Valores absolutos (En miles)",
                "sexo_edad_estudios": "TOTAL",
                "periodo": "2021",
                "valor": "120",
            },
            {
                "indicador": "EMPLEO VINCULADO AL DEPORTE: Valores absolutos (En miles)",
                "sexo_edad_estudios": "TOTAL",
                "periodo": "2021",
                "valor": "122",
            },
            {
                "indicador": "EMPLEO VINCULADO AL DEPORTE: En porcentaje del total de empleo",
                "sexo_edad_estudios": "TOTAL",
                "periodo": "2021",
                "valor": "5.1",
            },
            {
                "indicador": "EMPLEO VINCULADO AL DEPORTE: Valores absolutos (En miles)",
                "sexo_edad_estudios": "Hombres",
                "periodo": "2021",
                "valor": "80",
            },
        ]
    )
    csv_path = tmp_path / ANNUAL_FILE_NAME
    data.to_csv(csv_path, index=False)
    return DataService(data_dir=tmp_path)


def test_load_raw_data_works(sample_service: DataService):
    raw = sample_service.load_raw_data()
    assert not raw.empty
    assert {"indicador", "sexo_edad_estudios", "periodo", "valor"}.issubset(set(raw.columns))


def test_series_returns_clean_format(sample_service: DataService):
    series = sample_service.get_series()
    assert series == [
        {"year": 2020, "value": 100.0},
        {"year": 2021, "value": 121.0},
    ]


def test_kpis_consistent_with_series(sample_service: DataService):
    series = sample_service.get_series()
    kpis = sample_service.get_kpis()

    assert kpis["latest_year"] == series[-1]["year"]
    assert kpis["empleo_total"] == series[-1]["value"]
    assert kpis["growth_pct"] == 21.0


def test_empty_dataset_raises_value_error(tmp_path: Path):
    pd.DataFrame(columns=["indicador", "sexo_edad_estudios", "periodo", "valor"]).to_csv(
        tmp_path / ANNUAL_FILE_NAME,
        index=False,
    )
    service = DataService(data_dir=tmp_path)

    with pytest.raises(ValueError, match="No hay filas del indicador absoluto"):
        service.get_series()


def test_malformed_csv_raises_value_error(tmp_path: Path):
    pd.DataFrame([{"foo": 1, "bar": 2}]).to_csv(tmp_path / ANNUAL_FILE_NAME, index=False)
    service = DataService(data_dir=tmp_path)

    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        service.load_raw_data()
