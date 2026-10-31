import type { Metadata } from 'next';
import '@fontsource-variable/fraunces';
import '@fontsource-variable/manrope';
import '@fontsource/dm-mono/400.css';
import '@fontsource/dm-mono/500.css';
import 'lenis/dist/lenis.css';
import './globals.css';
import './civic.css';
import { Shell } from '@/components/Shell';

export const metadata: Metadata = {
  title: 'JanSetu — civic, made clearer',
  description: 'Independent Telangana civic-service navigation and a transparent JanSetu-only grievance workflow.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
