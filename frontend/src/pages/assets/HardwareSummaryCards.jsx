import React from 'react';
import { Cpu, Wifi, WifiOff, Clock, Truck, ShieldAlert } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';

export default function HardwareSummaryCards({ summary, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="p-4 bg-surface">
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-7 w-12" />
          </Card>
        ))}
      </div>
    );
  }

  const s = summary || {
    total_devices: 0,
    connected_devices: 0,
    disconnected_devices: 0,
    pending_devices: 0,
    vehicles_with_gps: 0,
    vehicles_without_gps: 0,
  };

  const cards = [
    {
      title: 'Total Devices',
      value: s.total_devices,
      icon: Cpu,
      colorText: 'text-content',
      bgIcon: 'bg-surface-secondary text-content-secondary',
      sub: 'All registered units',
    },
    {
      title: 'Connected',
      value: s.connected_devices,
      icon: Wifi,
      colorText: 'text-green-600',
      bgIcon: 'bg-green-50 text-green-600',
      dot: 'bg-green-500 animate-pulse',
      sub: 'Actively reporting',
    },
    {
      title: 'Disconnected',
      value: s.disconnected_devices,
      icon: WifiOff,
      colorText: 'text-amber-600',
      bgIcon: 'bg-amber-50 text-amber-600',
      dot: 'bg-amber-500',
      sub: '> 15m silence',
    },
    {
      title: 'Pending Config',
      value: s.pending_devices,
      icon: Clock,
      colorText: 'text-blue-600',
      bgIcon: 'bg-blue-50 text-blue-600',
      dot: 'bg-blue-500',
      sub: 'Awaiting first packet',
    },
    {
      title: 'Vehicles With GPS',
      value: s.vehicles_with_gps,
      icon: Truck,
      colorText: 'text-brand-600',
      bgIcon: 'bg-brand-50 text-brand-600',
      sub: 'Monitored in fleet',
    },
    {
      title: 'Vehicles W/O GPS',
      value: s.vehicles_without_gps,
      icon: ShieldAlert,
      colorText: s.vehicles_without_gps > 0 ? 'text-red-500' : 'text-content-secondary',
      bgIcon: s.vehicles_without_gps > 0 ? 'bg-red-50 text-red-500' : 'bg-surface-secondary text-content-muted',
      sub: 'Need installation',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c, idx) => {
        const Icon = c.icon;
        return (
          <Card
            key={idx}
            className="p-4 border border-border/70 hover:border-brand-300 transition-colors shadow-card flex flex-col justify-between"
          >
            <div className="flex items-center justify-between gap-1 mb-2">
              <span className="text-xs font-medium text-content-secondary line-clamp-1">{c.title}</span>
              <div className={`p-1.5 rounded-lg ${c.bgIcon}`}>
                <Icon className="h-4 w-4" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                {c.dot && <span className={`w-2 h-2 rounded-full ${c.dot}`} />}
                <span className={`text-2xl font-bold tracking-tight ${c.colorText}`}>
                  {c.value.toLocaleString()}
                </span>
              </div>
              <p className="text-[11px] text-content-muted mt-0.5">{c.sub}</p>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
