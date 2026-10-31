'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, Menu, X } from 'lucide-react';
import { useEffect, useState } from 'react';

const links = [
  { href: '/services', label: 'Services' },
  { href: '/assistant', label: 'Ask JanSetu' },
  { href: '/dashboard', label: 'My space' },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  return (
    <>
      <div className="notice">
        <div className="wrap notice-inner">
          <span>Independent civic navigation · Not affiliated with any government</span>
          <span>JanSetu does not send grievances to government departments.</span>
        </div>
      </div>
      <header className="site-header">
        <div className="nav wrap">
          <Link className="brand" href="/" aria-label="JanSetu home" onClick={() => setMenuOpen(false)}>
            <img className="brandmark" src="/bridge-mark.svg" alt="JanSetu" />
          </Link>
          <nav id="primary-navigation" className={`primary-nav${menuOpen ? ' is-open' : ''}`} aria-label="Main navigation">
            {links.map((link) => {
              const active = link.href === '/services'
                ? pathname.startsWith('/services')
                : pathname === link.href;
              return (
                <Link
                  href={link.href}
                  key={link.href}
                  aria-current={active ? 'page' : undefined}
                  onClick={() => setMenuOpen(false)}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
          <div className="nav-actions">
            <Link className="nav-cta" href="/login" onClick={() => setMenuOpen(false)}>
              Sign in <ArrowUpRight size={14} aria-hidden="true" />
            </Link>
            <button
              className="menu"
              type="button"
              aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={menuOpen}
              aria-controls="primary-navigation"
              onClick={() => setMenuOpen((open) => !open)}
              onKeyDown={(event) => {
                if (event.key === 'Escape') setMenuOpen(false);
              }}
            >
              {menuOpen ? <X size={16} aria-hidden="true" /> : <Menu size={16} aria-hidden="true" />}
              <span>{menuOpen ? 'Close' : 'Menu'}</span>
            </button>
          </div>
        </div>
      </header>
      <main id="main-content">{children}</main>
      <footer className="footer">
        <div className="wrap footer-inner">
          <Link className="brand" href="/" aria-label="JanSetu home">
            <img className="brandmark" src="/bridge-mark.svg" alt="JanSetu" />
          </Link>
          <p>Independent civic navigation. Always check official sources for current requirements.</p>
          <nav className="footer-nav" aria-label="Footer navigation">
            <Link href="/services">Explore services</Link>
            <Link href="/assistant">Assistant</Link>
            <Link href="/grievances/new">Grievance demo</Link>
          </nav>
        </div>
        <div className="wrap footer-note">
          JanSetu is an independent, informational service and is not a government website. Grievance workflows are simulated and are not forwarded to government departments.
        </div>
      </footer>
    </>
  );
}
