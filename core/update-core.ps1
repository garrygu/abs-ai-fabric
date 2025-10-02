cd C:\ABS\core
docker compose -f core.yml --env-file .env pull
docker compose -f core.yml --env-file .env up -d
