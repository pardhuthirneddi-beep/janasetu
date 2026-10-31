'use client';
import { useState } from 'react';
import Link from 'next/link';

export default function NewGrievance() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function send(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setMessage(''); setBusy(true);
    const form = new FormData(event.currentTarget);
    const files = form.getAll('attachments').filter((value): value is File => value instanceof File && value.size > 0);
    if (files.length > 4) { setError('Choose up to four files.'); setBusy(false); return; }
    try {
      const response = await fetch('/api/v1/grievances', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: form.get('title'), narrative: form.get('narrative') }) });
      if (response.status === 401) { setError('Sign in through Manus OAuth before saving a private JanSetu record. No government filing was made.'); return; }
      if (!response.ok) throw new Error();
      const record: { reference: string } = await response.json();
      const failures: string[] = [];
      for (const file of files) {
        const upload = new FormData(); upload.append('file', file);
        const result = await fetch(`/api/v1/grievances/${encodeURIComponent(record.reference)}/attachments`, { method: 'POST', credentials: 'include', body: upload });
        if (!result.ok) failures.push(file.name);
      }
      setMessage(failures.length ? `JanSetu record ${record.reference} was created. These attachments could not be stored: ${failures.join(', ')}. This record is not a government case.` : `JanSetu reference ${record.reference} was created${files.length ? ` with ${files.length} authorized private attachment${files.length === 1 ? '' : 's'}` : ''}. This is not a government case or filing.`);
      (event.currentTarget as HTMLFormElement).reset();
    } catch {
      setError('JanSetu could not save this record. Nothing was submitted to a government department.');
    } finally { setBusy(false); }
  }

  return <section className="wrap page-section narrow">
    <Link className="backlink" href="/dashboard">← My space</Link><div className="page-kicker">JANSETU / LOCAL GRIEVANCE WORKFLOW</div>
    <span className="eyebrow">BEFORE YOU BEGIN</span><h1>Tell us what <em>happened.</em></h1>
    <div className="urgent-notice"><b>Important</b><p>This is a JanSetu-only grievance workflow. It does not send your grievance to a government department and is not an official filing.</p></div>
    <form className="ask-form" onSubmit={send}>
      <label htmlFor="title">Short title</label><input id="title" name="title" minLength={4} maxLength={240} required />
      <label htmlFor="narrative">Describe the issue</label><textarea id="narrative" name="narrative" rows={6} minLength={10} maxLength={20000} required />
      <label htmlFor="attachments">Private supporting files (optional)</label><input id="attachments" name="attachments" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" multiple />
      <div className="privacy"><b>Privacy:</b> grievance text is stored in JanSetu to show your record and is not sent to the AI assistant. Attachments are limited to PDF, PNG or JPEG, up to 8 MiB each. Physical file deletion is not available through the storage service; access can be removed while stored bytes may remain.</div>
      <button className="button" disabled={busy}>{busy ? 'Saving to JanSetu…' : 'Create JanSetu record ↗'}</button>
    </form>
    {error && <div className="api-error" role="alert">{error} <Link href="/login">Sign in ↗</Link></div>}
    {message && <div className="success" role="status">{message} <Link href="/dashboard">Open your JanSetu dashboard ↗</Link></div>}
  </section>;
}
