'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

type RecordRow = { reference: string; title: string; summary: string; status: string; updatedAt: string };
export default function Dashboard() {
  const [state, setState] = useState<'loading' | 'out' | 'error' | 'in'>('loading');
  useEffect(() => { fetch('/api/v1/auth/me', { credentials: 'include' }).then(async (response) => { if (response.status === 401) { setState('out'); return; } if (!response.ok) throw new Error(); setState('in'); }).catch(() => setState('error')); }, []);
  return <section className="wrap page-section narrow"><div className="page-kicker">MY JANSETU / DASHBOARD</div><span className="eyebrow">PRIVATE SPACE</span><h1>Your civic <em>space.</em></h1>{state === 'loading' ? <p>Checking your session…</p> : state === 'in' ? <DashboardData /> : <><div className="api-error">{state === 'out' ? 'Login required to see your private JanSetu records.' : 'We couldn’t check your session. No profile or citizen record is assumed.'}</div><Link className="button" href="/login">Go to sign in ↗</Link></>}<div className="privacy"><b>Account and files:</b> JanSetu does not currently offer self-service account removal. If app access is removed through support, stored attachment bytes may remain because the storage service does not provide physical deletion.</div></section>;
}
function DashboardData() {
  const [records, setRecords] = useState<RecordRow[] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => { fetch('/api/v1/grievances/mine', { credentials: 'include' }).then((response) => { if (!response.ok) throw new Error(); return response.json(); }).then((data: { items: RecordRow[] }) => setRecords(data.items)).catch(() => setError(true)); }, []);
  return <><p className="lead">Your private JanSetu records are provided by the connected service API.</p>{error ? <div className="api-error">Your JanSetu grievance list is currently unavailable.</div> : records ? records.length ? <div className="record-list">{records.map((record) => <Link className="record-row" href={`/grievances/${encodeURIComponent(record.reference)}`} key={record.reference}><span className="record-ref">{record.reference}</span><strong>{record.title}</strong><span className="record-status">{record.status.replaceAll('_', ' ')}</span><small>Updated {new Date(record.updatedAt).toLocaleDateString()}</small><b>↗</b></Link>)}</div> : <div className="empty"><span className="eyebrow">NO JANSETU RECORDS</span><h3>Nothing has been recorded here.</h3><p>A JanSetu record is not a government filing.</p><Link className="button" href="/grievances/new">Create a JanSetu record ↗</Link></div> : <p>Loading your JanSetu records…</p>}<p className="urgent-notice"><b>JanSetu only.</b> These records do not represent government submissions, government ticket statuses or official outcomes.</p></>;
}
