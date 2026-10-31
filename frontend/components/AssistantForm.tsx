'use client';
import { useState } from 'react';

type Source = { id: string; title: string; url: string };
type Answer = { answer?: string; sources?: Source[]; evidence?: Source[]; uncertainty?: string; disclaimer?: string };

export default function AssistantForm() {
  const [question, setQuestion] = useState('');
  const [language, setLanguage] = useState('en');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) return;
    setBusy(true); setError(''); setAnswer(null);
    try {
      const response = await fetch('/api/v1/assistant', {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), language }),
      });
      if (!response.ok) throw new Error();
      setAnswer(await response.json());
      setQuestion('');
    } catch {
      setError('The JanSetu assistant could not respond. The question was not saved by this page. Try again later or follow an official service link.');
    } finally { setBusy(false); }
  }

  const sources = answer?.evidence ?? answer?.sources ?? [];
  return <>
    <div className="privacy"><b>Privacy, plainly:</b> JanSetu uses your question locally for topic routing and public-source lookup. If a model is configured, it receives only a normalized topic, selected public evidence and a normalized response-language code — not the raw question, grievance narratives or attachments. The question is not saved as a conversation.</div>
    <form className="ask-form" onSubmit={submit}>
      <label htmlFor="language">Response language</label>
      <select id="language" value={language} onChange={(event) => setLanguage(event.target.value)}><option value="en">English</option><option value="te">తెలుగు · Telugu</option></select>
      <label htmlFor="question">What would you like help understanding?</label>
      <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Describe what you’re trying to do — no personal details, please." rows={5} required />
      <button className="button" disabled={busy}>{busy ? 'Checking public sources…' : 'Ask JanSetu ↗'}</button>
    </form>
    {error && <div className="api-error" role="alert">{error}</div>}
    {answer && <section className="answer" aria-live="polite"><div className="uncertain">{answer.uncertainty || 'Information can be incomplete or change. Verify key details with the linked official source.'}</div><p>{answer.answer || 'No answer was returned.'}</p>{sources.length ? <div className="sources"><b>Public source records</b>{sources.map((source) => <a key={source.id} href={source.url} target="_blank" rel="noreferrer">[{source.id}] {source.title} ↗</a>)}</div> : <p className="muted">No sufficiently relevant source evidence was found. The assistant has not guessed.</p>}<small>{answer.disclaimer}</small></section>}
  </>;
}
