export async function getMockAlerts() {
  // simulate network delay
  await new Promise(resolve => setTimeout(resolve, 800));

  return {
    items: [
      {
        alert_id: crypto.randomUUID(),
        level: "high",
        message: "High flood risk detected in PJS 5 cell",
        cell_id: "PJU 5",
        created_at: new Date(Date.now() - 1000 * 60).toISOString()
      },
    //   {
    //     alert_id: crypto.randomUUID(),
    //     level: "medium",
    //     message: "Moderate landslide probability near SS 10",
    //     cell_id: "PJU 8",
    //     created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString()
    //   },
    //   {
    //     alert_id: crypto.randomUUID(),
    //     level: "low",
    //     message: "Minor drainage overflow risk in Section 18",
    //     cell_id: "PJU 9",
    //     created_at: new Date(Date.now() - 1000 * 60 * 10).toISOString()
    //   }
    ]
  };
}