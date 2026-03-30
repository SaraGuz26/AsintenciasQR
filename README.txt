Inicializar tablas
- docker compose exec backend python -m scripts.create_tables
- docker compose exec backend python -m scripts.seed_load
Bajar
- docker compose down -v
- docker compose build
- docker compose up -d
