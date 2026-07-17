import { mockPayments } from '@/data/mockData';

let localPayments = [...mockPayments];

export async function getPayments(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localPayments];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(p =>
          p.recipient_name.toLowerCase().includes(q) ||
          p.id.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function recordPayout(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newPay = {
        id: `PAY-${Math.floor(1000 + Math.random() * 9000)}`,
        date: new Date().toISOString(),
        status: 'completed',
        ref_num: `TXN-${Math.floor(1000000000 + Math.random() * 9000000000)}`,
        ...data
      };
      localPayments.unshift(newPay);
      resolve(newPay);
    }, 600);
  });
}
