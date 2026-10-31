import Link from 'next/link';
import { getServices } from '@/lib/data';

export default async function ServiceDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const services = await getServices();
  const service = services?.find((item) => item.slug === decodeURIComponent(slug));
  if (!service) {
    return <section className="wrap page-section"><Link className="backlink" href="/services">← All services</Link><div className="empty"><span className="eyebrow">SERVICE RECORD UNAVAILABLE</span><h1>We can’t verify this listing.</h1><p>No matching sourced record is available. Return to the directory or use an official portal you already trust.</p><Link className="button" href="/services">Back to services</Link></div></section>;
  }
  const status = service.verificationStatus ?? (service.verified === false ? 'not_verified' : 'partially_verified');
  const details = service.fields ?? { Eligibility: 'Not verified', Documents: 'Not verified', Fees: 'Not verified', Timeline: 'Not verified', Procedure: 'Not verified' };
  return <section className="wrap page-section">
    <Link className="backlink" href="/services">← All services</Link>
    <div className="page-kicker">SERVICE / {service.category}</div>
    <h1 className="detail-title">{service.name}</h1>
    <div className="detail-grid">
      <div>
        <span className="eyebrow">SOURCE-BOUNDED INFORMATION</span>
        <p className="detail-copy">{service.description || service.summary || 'Not verified — no supported description is available.'}</p>
        <div className="verified-note">Verification state: {status === 'not_verified' ? 'Not verified' : 'Partially verified'} · This is not a fully verified service profile.</div>
        <h2 className="section-subhead">Service facts</h2>
        <dl className="fact-list">{Object.entries(details).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || 'Not verified'}</dd></div>)}</dl>
        <div className="source-meta"><b>Jurisdiction context</b><p>{service.jurisdiction || 'Not verified'}</p><small>Source reviewed {service.sourceDate || 'date not verified'}.</small></div>
      </div>
      <aside className="source-card"><span className="eyebrow">OFFICIAL SOURCE</span><h3>{service.sourceName || 'Not verified'}</h3>{service.officialUrl ? <a className="button" href={service.officialUrl} target="_blank" rel="noreferrer">Continue to official source ↗</a> : <p>Official link: Not verified</p>}<p>{service.sourceSupport || 'The source support details are not verified.'}</p><small>JanSetu is an independent guide. Service applications and decisions are handled only by the official provider.</small></aside>
    </div>
  </section>;
}
