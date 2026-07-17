export async function getFleetReportData() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        mileageTrend: [
          { month: 'Jan', avg_mileage: 4.2 },
          { month: 'Feb', avg_mileage: 4.3 },
          { month: 'Mar', avg_mileage: 4.1 },
          { month: 'Apr', avg_mileage: 4.5 },
          { month: 'May', avg_mileage: 4.6 },
          { month: 'Jun', avg_mileage: 4.4 }
        ],
        expenseDistribution: [
          { name: 'Fuel', value: 65 },
          { name: 'Repair', value: 18 },
          { name: 'Toll', value: 12 },
          { name: 'Fines/Other', value: 5 }
        ],
        driverSafetyStats: [
          { name: 'Rajesh Kumar', safetyScore: 72, rating: 2.8 },
          { name: 'Suresh Patel', safetyScore: 95, rating: 4.6 },
          { name: 'Amit Singh', safetyScore: 82, rating: 3.9 },
          { name: 'Vikram Yadav', safetyScore: 98, rating: 4.8 }
        ]
      });
    }, 600);
  });
}

export async function exportReport(format = 'pdf', type = 'fleet') {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ downloadUrl: `https://example.com/exports/${type}_report.${format}`, filename: `${type}_report.${format}` });
    }, 700);
  });
}
