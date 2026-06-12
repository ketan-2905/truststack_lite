import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '10s', target: 20 },  // Ramp up to 20 VUs
    { duration: '30s', target: 20 },  // Stay at 20 VUs
    { duration: '10s', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'], // 95th percentile latency < 500ms
    'http_req_failed': ['rate<0.1'],     // Error rate < 10%
  },
};

const API_BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Test 1: Health check
  let res = http.get(`${API_BASE_URL}/health`);
  check(res, {
    'health is ok': (r) => r.status === 200,
  });
  sleep(0.5);

  // Test 2: Get cases (requires auth, will likely fail without token but test the endpoint)
  res = http.get(`${API_BASE_URL}/v1/onboarding-cases`);
  check(res, {
    'cases endpoint is callable': (r) => r.status === 200 || r.status === 401,
  });
  sleep(0.5);

  // Test 3: Audit events
  res = http.get(`${API_BASE_URL}/v1/audit-events`);
  check(res, {
    'audit endpoint is callable': (r) => r.status === 200 || r.status === 401,
  });
  sleep(1);
}
