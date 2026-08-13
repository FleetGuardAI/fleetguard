/**
 * FleetGuard Chat Box — Mock Data
 * 
 * Suggested prompts and sample responses for the AI Co-Pilot.
 * Replace with real AI backend responses when available.
 */

export const SUGGESTED_PROMPTS = [
  'Show today\'s trips',
  'Which trucks are idle?',
  'Fuel summary this week',
  'Remind me for insurance',
  'Show active alerts',
];

export const SAMPLE_RESPONSES = {
  'Show today\'s trips': {
    type: 'table',
    text: 'Here are today\'s active trips:',
    data: {
      headers: ['Vehicle', 'Route', 'Driver', 'Status', 'ETA'],
      rows: [
        ['KA-01-HH-1234', 'Bangalore → Chennai', 'Ramesh Kumar', 'In Transit', '4:30 PM'],
        ['KA-02-AB-5678', 'Bangalore → Mysore', 'Suresh Patil', 'Loading', '2:00 PM'],
        ['KA-03-CD-9012', 'Hubli → Bangalore', 'Mahesh Singh', 'Completed', '—'],
      ],
    },
  },
  'Which trucks are idle?': {
    type: 'list',
    text: '8 trucks are currently available and idle:',
    data: {
      items: [
        { label: 'KA-04-EF-3456', detail: 'Idle for 2 days — yard location' },
        { label: 'KA-05-GH-7890', detail: 'Idle for 1 day — Mysore depot' },
        { label: 'KA-06-IJ-1234', detail: 'Idle for 6 hours — yard location' },
        { label: 'KA-07-KL-5678', detail: 'Just completed trip — available' },
      ],
    },
    suggestion: 'Would you like me to assign loads to any of these vehicles?',
  },
  'Fuel summary this week': {
    type: 'metrics',
    text: 'Here\'s your fleet fuel summary for this week:',
    data: {
      metrics: [
        { label: 'Total Fuel Consumed', value: '4,250 L', trend: '+5%' },
        { label: 'Avg. Fuel Efficiency', value: '3.9 km/L', trend: '-2%' },
        { label: 'Fuel Cost', value: '₹4,03,750', trend: '+8%' },
        { label: 'Suspicious Drops', value: '2', trend: 'flagged' },
      ],
    },
    suggestion: 'I noticed 2 suspicious fuel drops. Want me to show the details?',
  },
  'Remind me for insurance': {
    type: 'text',
    text: '🔔 Insurance reminders set! Here are the upcoming renewals:\n\n• **KA-02-AB-5678** — Expired on 10 May (overdue!)\n• **KA-01-HH-1234** — Due on 28 Aug 2026\n• **KA-03-CD-9012** — Due on 15 Sep 2026\n\nI\'ll notify you 7 days before each renewal date.',
  },
  'Show active alerts': {
    type: 'alerts',
    text: 'You have 3 active alerts:',
    data: {
      alerts: [
        { severity: 'critical', title: 'Insurance expired for KA-02-AB-5678', time: 'Expired on 10 May' },
        { severity: 'warning', title: 'KA-01-HH-1234 requires maintenance', time: 'Due in 2 days' },
        { severity: 'info', title: 'Fuel drop of 5.0L detected on KA-01-HH-1234', time: '06:44 am' },
      ],
    },
  },
};

/**
 * Generate a mock AI response for a given user message.
 * Falls back to a generic response if no match is found.
 */
export function getMockResponse(message) {
  const trimmed = message.trim();
  
  // Check for exact or close matches
  for (const [prompt, response] of Object.entries(SAMPLE_RESPONSES)) {
    if (trimmed.toLowerCase() === prompt.toLowerCase()) {
      return response;
    }
  }

  // Keyword matching
  const lower = trimmed.toLowerCase();
  if (lower.includes('trip')) return SAMPLE_RESPONSES['Show today\'s trips'];
  if (lower.includes('idle') || lower.includes('available')) return SAMPLE_RESPONSES['Which trucks are idle?'];
  if (lower.includes('fuel')) return SAMPLE_RESPONSES['Fuel summary this week'];
  if (lower.includes('insurance') || lower.includes('remind')) return SAMPLE_RESPONSES['Remind me for insurance'];
  if (lower.includes('alert') || lower.includes('warning')) return SAMPLE_RESPONSES['Show active alerts'];

  // Generic fallback
  return {
    type: 'text',
    text: `I understand you're asking about "${trimmed}". This feature is coming soon — I'll be able to help with fleet analytics, driver management, fuel tracking, and more.\n\nFor now, try one of the suggested prompts to see what I can do!`,
  };
}
