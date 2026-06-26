#!/usr/bin/env bash
# Lightweight load test against /health using a portable concurrency loop.
# A full k6/Locust scenario is added in MD 11; this keeps the global command set
# runnable from MD 01 onward without extra tooling.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
REQUESTS="${REQUESTS:-200}"
CONCURRENCY="${CONCURRENCY:-10}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${SCRIPT_DIR}/wait-for-services.sh"

echo "Running ${REQUESTS} requests against ${API_URL}/health/live with concurrency ${CONCURRENCY}..."

start="$(date +%s)"
fail_file="$(mktemp)"
echo 0 > "${fail_file}"

run_batch() {
  for _ in $(seq 1 "$1"); do
    if ! curl -fsS -o /dev/null "${API_URL}/health/live"; then
      echo "1" >> "${fail_file}"
    fi
  done
}

per_worker=$((REQUESTS / CONCURRENCY))
pids=()
for _ in $(seq 1 "${CONCURRENCY}"); do
  run_batch "${per_worker}" &
  pids+=("$!")
done
for pid in "${pids[@]}"; do
  wait "${pid}"
done

end="$(date +%s)"
duration=$((end - start))
[ "${duration}" -eq 0 ] && duration=1
total=$((per_worker * CONCURRENCY))
failures=$(($(wc -l < "${fail_file}") - 1))
rm -f "${fail_file}"

echo "Completed ${total} requests in ${duration}s (~$((total / duration)) req/s), failures: ${failures}"
if [ "${failures}" -gt 0 ]; then
  echo "ERROR: load test had ${failures} failed requests" >&2
  exit 1
fi
echo "Load test passed."
