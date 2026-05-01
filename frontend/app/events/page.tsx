import { Metadata } from 'next';
import EventScannerTerminal from '@/components/events/EventScannerTerminal';

export const metadata: Metadata = {
  title: 'Event Scanner | Merton Credit Terminal',
  description: 'Real-time equity volatility shock detection and structural credit lag alpha gap signals.',
};

export default function EventsPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      <EventScannerTerminal />
    </main>
  );
}