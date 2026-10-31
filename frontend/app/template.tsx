'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { usePathname } from 'next/navigation';

export default function PageTemplate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      key={pathname}
      className="page-transition"
      initial={{ opacity: 0, y: reducedMotion ? 0 : 7 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.22, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
