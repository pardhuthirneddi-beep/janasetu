'use client';

import { useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

export default function HomeEffects() {
  useEffect(() => {
    const root = document.querySelector<HTMLElement>('.home-page');
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const lenis = new Lenis({
      duration: 0.9,
      smoothWheel: true,
    });
    lenis.on('scroll', ScrollTrigger.update);

    let frame = 0;
    const raf = (time: number) => {
      lenis.raf(time);
      frame = window.requestAnimationFrame(raf);
    };
    frame = window.requestAnimationFrame(raf);

    const context = gsap.context(() => {
      const sections = gsap.utils.toArray<HTMLElement>('[data-reveal]', root);
      sections.forEach((element) => {
        gsap.fromTo(
          element,
          { autoAlpha: 0, y: 18 },
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.52,
            ease: 'power2.out',
            immediateRender: false,
            scrollTrigger: {
              trigger: element,
              start: 'top 88%',
              once: true,
            },
          },
        );
      });
      requestAnimationFrame(() => ScrollTrigger.refresh());
    }, root);

    return () => {
      window.cancelAnimationFrame(frame);
      context.revert();
      lenis.destroy();
    };
  }, []);

  return null;
}
