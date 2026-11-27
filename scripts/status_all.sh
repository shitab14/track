#!/usr/bin/env bash
# Read-only status check for the TRACK stack: Docker, PostgreSQL, backend API and
# frontend. Starts nothing. Exits 0 only if Database, Backend and Frontend are up.
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; DIM=$'\033[2m'; NC=$'\033[0m'
UP=0; DOWN=0

report() {
  # $1 = label, $2 = 0(up)/1(down), $3 = detail
  if [ "$2" -eq 0 ]; then
    printf "  ${GREEN}● UP  ${NC} %-10s ${DIM}%s${NC}\n" "$1" "$3"; UP=$((UP + 1))
  else
    printf "  ${RED}● DOWN${NC} %-10s ${DIM}%s${NC}\n" "$1" "$3"; DOWN=$((DOWN + 1))
  fi
}

http_code() { curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$1" 2>/dev/null; }

echo "========================================================"
echo "   TRACK — Service Status"
echo "========================================================"

# --- Docker daemon ------------------------------------------------------
if docker info >/dev/null 2>&1; then
  report "Docker" 0 "daemon running"
  DOCKER_OK=1
else
  report "Docker" 1 "daemon not running"
  DOCKER_OK=0
fi

# Project containers (informational), if Docker is up.
if [ "$DOCKER_OK" -eq 1 ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && printf "  ${DIM}        container: %s${NC}\n" "$line"
  done < <(docker ps -a --filter "name=track" --format "{{.Names}} ({{.Status}})" 2>/dev/null)
fi

# --- PostgreSQL (:5432) -------------------------------------------------
# Verify Postgres actually answers, not just that the port is open (Docker
# Desktop's proxy can keep :5432 bound after the container exits).
db_ok=1; db_detail="not reachable on :5432"
if command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p 5432 -q 2>/dev/null; then
  db_ok=0; db_detail="postgres accepting connections on :5432"
elif [ "$DOCKER_OK" -eq 1 ] && docker compose exec -T db pg_isready -U postgres -d track_db >/dev/null 2>&1; then
  db_ok=0; db_detail="postgres (container) ready on :5432"
elif (exec 3<>/dev/tcp/localhost/5432) 2>/dev/null; then
  exec 3>&- 2>/dev/null; db_detail="port :5432 open but Postgres did not respond"
fi
report "Database" "$db_ok" "$db_detail"

# --- Backend API (:8000) ------------------------------------------------
code=$(http_code "http://localhost:8000/api/v1/health")
if [ "$code" = "200" ]; then
  report "Backend" 0 "API healthy on :8000"
else
  report "Backend" 1 "no 200 from :8000/api/v1/health (got ${code:-none})"
fi

# --- Frontend (:3000) ---------------------------------------------------
code=$(http_code "http://localhost:3000")
case "$code" in
  200|301|302|307|308) report "Frontend" 0 "serving on :3000 (HTTP $code)" ;;
  *) report "Frontend" 1 "not serving on :3000 (got ${code:-none})" ;;
esac

echo "--------------------------------------------------------"
printf "  %s up, %s down\n" "$UP" "$DOWN"
echo "========================================================"

# Core services = Database, Backend, Frontend (Docker is optional for the
# hybrid run). Succeed only if none of those three are down.
[ "$DOWN" -eq 0 ] || { [ "$DOWN" -eq 1 ] && [ "$DOCKER_OK" -eq 0 ]; }
