import type { Metadata } from 'next';
import './globals.css';
import './civic.css';
import { Shell } from '@/components/Shell';

export const metadata: Metadata = {
  title: 'JanSetu — civic, made clearer',
  description: 'Independent Telangana civic-service navigation and a transparent JanSetu-only grievance workflow.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><Shell>{children}</Shell></body></html>;
}
