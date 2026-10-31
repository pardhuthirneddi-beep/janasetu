import Link from 'next/link';
import HomeEffects from '@/components/HomeEffects';

export default function Home() {
  return (
    <div className="home-page">
      <section className="hero wrap">
        <div className="hero-copy" data-reveal>
          <div className="eyebrow"><i aria-hidden="true" /> Civic navigation, with clarity</div>
          <h1>Good questions.<br /><em>Clearer paths.</em></h1>
          <p className="hero-deck">
            A thoughtful starting point for finding public services, understanding your options, and knowing where to go next.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/services">Explore services <span aria-hidden="true">↗</span></Link>
            <Link className="text-link" href="/assistant">Ask a question <span aria-hidden="true">↗</span></Link>
          </div>
          <div className="hero-foot">
            <span>01 — Find official service links</span>
            <span>02 — Understand your next step</span>
          </div>
        </div>
        <div className="hero-art" data-reveal>
          <img
            className="hero-image"
            src="/manus-storage/async-images/KM7UQYNmFMjG5HzoTBGXmE/image-1.webp"
            alt="Editorial illustration of a footbridge connecting a city edge and a neighborhood"
            fetchPriority="high"
          />
          <div className="art-label"><span>A bridge to the right information</span><b aria-hidden="true">✳</b></div>
        </div>
      </section>

      <section className="intro-band" data-reveal>
        <div className="wrap intro-inner">
          <span className="eyebrow">A useful distinction</span>
          <p>JanSetu helps you navigate. <strong>Official portals provide the services.</strong> Our grievance flow is a simulation — it never sends a complaint to a department.</p>
        </div>
      </section>

      <section className="wrap pathways">
        <div className="section-heading" data-reveal>
          <div>
            <span className="eyebrow">Start where you are</span>
            <h2>Three ways to find your way.</h2>
          </div>
          <span className="section-index">01 — 03</span>
        </div>
        <div className="path-grid">
          <Link href="/services" className="path-card" data-reveal>
            <span className="path-num">01</span>
            <div><h3>Browse services</h3><p>Explore sourced service information and continue to official portals.</p></div>
            <b aria-hidden="true">↗</b>
          </Link>
          <Link href="/assistant" className="path-card" data-reveal>
            <span className="path-num">02</span>
            <div><h3>Ask JanSetu</h3><p>Get guided answers in English or Telugu, with citations and uncertainty noted.</p></div>
            <b aria-hidden="true">↗</b>
          </Link>
          <Link href="/grievances/new" className="path-card" data-reveal>
            <span className="path-num">03</span>
            <div><h3>Try a grievance flow</h3><p>Understand how the JanSetu demonstration works. It is not a government filing.</p></div>
            <b aria-hidden="true">↗</b>
          </Link>
        </div>
      </section>

      <section className="callout" data-reveal>
        <div className="wrap callout-inner">
          <span className="eyebrow">Always independent</span>
          <p>Not a government website. Not a substitute for official advice. Just a clearer place to begin.</p>
          <Link href="/services">Find a service <span aria-hidden="true">↗</span></Link>
        </div>
      </section>
      <HomeEffects />
    </div>
  );
}
