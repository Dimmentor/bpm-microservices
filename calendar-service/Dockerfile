FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root
COPY . .
ENV PYTHONUNBUFFERED=1
#CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload