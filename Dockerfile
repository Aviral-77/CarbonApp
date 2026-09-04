FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN cd frontend && npm ci && npm run build || echo "Frontend build skipped"

RUN python -c "from db.seed import seed_all; seed_all()"

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
