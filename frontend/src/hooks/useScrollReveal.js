import { useEffect } from 'react';

/**
 * Attaches an IntersectionObserver that adds the 'visible' class
 * to elements matching the given selector when they enter the viewport.
 *
 * Works with: .reveal, .reveal-left, .reveal-right, .reveal-scale, .stagger-children
 */
export function useScrollReveal(selector = '.reveal, .reveal-left, .reveal-right, .reveal-scale, .stagger-children') {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { root: null, rootMargin: '0px 0px -60px 0px', threshold: 0.1 }
    );

    const targets = document.querySelectorAll(selector);
    targets.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [selector]);
}
