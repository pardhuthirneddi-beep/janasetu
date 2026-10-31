import { readFile } from 'node:fs/promises';
import path from 'node:path';

export type Service = {
  slug: string;
  name: string;
  category: string;
  description?: string;
  summary?: string;
  officialUrl?: string;
  sourceName?: string;
  sourceDate?: string;
  sourceSupport?: string;
  jurisdiction?: string;
  verificationStatus?: 'partially_verified' | 'not_verified' | string;
  verified?: boolean;
  fields?: Record<string, string>;
  sourceUrl?: string;
};

export async function getServices(): Promise<Service[] | null> {
  try {
    const raw = await readFile(path.join(process.cwd(), 'public', 'services.json'), 'utf8');
    const data: unknown = JSON.parse(raw);
    const rows = Array.isArray(data) ? data : (data as { services?: unknown[] })?.services;
    return Array.isArray(rows) ? rows as Service[] : null;
  } catch {
    return null;
  }
}
