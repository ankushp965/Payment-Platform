import http from 'k6/http';
import { check, sleep } from 'k6';

// 50 Virtual Users ramping up to generate realistic payment traffic
export const options = {
    stages: [
        { duration: '30s', target: 20 }, // Ramp-up to 20 users
        { duration: '1m', target: 50 },  // Steady load at 50 users
        { duration: '20s', target: 0 },  // Ramp-down
    ],
    thresholds: {
        http_req_failed: ['rate<0.05'], // Error rate should be below 5%
        http_req_duration: ['p(95)<500'], // 95% of payments should complete under 500ms
    },
};

export default function () {
    const url = __ENV.TARGET_URL || 'http://localhost:8080/api/v1/payments';

    const payload = JSON.stringify({
        account_id: `ACC-K6-${Math.floor(Math.random() * 10000)}`,
        amount: (Math.random() * 500 + 10).toFixed(2),
        currency: 'USD',
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const res = http.post(url, payload, params);

    // Validate response status
    check(res, {
        'payment status is 200': (r) => r.status === 200,
    });

    sleep(0.5); // 500ms think time between payment transactions
}