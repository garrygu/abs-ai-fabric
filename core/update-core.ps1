cd C:\ABS\core
docker compose -f docker-compose.yml --env-file .env pull
docker compose -f docker-compose.yml --env-file .env up -d
