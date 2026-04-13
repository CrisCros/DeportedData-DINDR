# Backend - DeporteData API

API REST desarrollada con FastAPI y conectada a los CSV reales de empleo deportivo.

## Requisitos

- Python 3.12+
- pip

## Instalación local
```bash
cd backend/
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## Variables de entorno
Copia `backend/.env.example` y ajusta:

- `DATA_DIR`: carpeta donde están los CSV limpios (por defecto se espera `backend/data`).
- `FRONTEND_ORIGIN`: origen permitido por CORS (por defecto `http://localhost:5173`).

## Ejecución
```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/login` | Autenticación JWT básica |
| GET | `/dashboard/kpis` | KPIs reales de empleo deportivo |
| GET | `/dashboard/series` | Serie anual real (años y valores) |
| POST | `/chat` | Respuesta básica basada en datos reales |

### Ejemplo `POST /chat`
```json
{
  "message": "¿Cómo ha crecido el empleo?"
}
```

## Datos CSV
Para despliegues serverless (ej. Vercel), incluye los CSV requeridos en `backend/data/`.
Este repositorio ya incluye `backend/data/medias_anuales_demografia.csv`.

## Estructura del módulo

```text
backend/app/
├── core/config.py
├── main.py
├── models_request.py
├── routes/
│   ├── chat.py
│   └── dashboard.py
└── services/
    └── data_service.py
```

## Tests
```bash
pytest tests/ -v
```
