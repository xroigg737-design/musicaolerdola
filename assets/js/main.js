document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll effect ──
  const nav = document.querySelector('.nav');
  const handleScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  };
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // ── Mobile menu ──
  const hamburger = document.querySelector('.nav-hamburger');
  const navLinks = document.querySelector('.nav-links');

  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    navLinks.classList.toggle('open');
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      navLinks.classList.remove('open');
    });
  });

  // ── Scroll reveal ──
  const reveals = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );
  reveals.forEach(el => observer.observe(el));

  // ── Floating music notes ──
  const notesContainer = document.querySelector('.hero-particles');
  const noteChars = ['♪', '♫', '♬', '♩', '\u{1D160}'];
  for (let i = 0; i < 15; i++) {
    const note = document.createElement('div');
    note.classList.add('note');
    note.textContent = noteChars[i % noteChars.length];
    note.style.left = `${(i / 15) * 100}%`;
    note.style.fontSize = `${2 + (i % 4)}rem`;
    note.style.animationDelay = `${(i * 1.3)}s`;
    note.style.animationDuration = `${15 + (i % 10)}s`;
    notesContainer.appendChild(note);
  }

  // ── Smooth scroll for anchor links ──
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        const offset = nav.offsetHeight + 10;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  // ── Contact form ──
  const form = document.querySelector('.contact-form');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const btn = form.querySelector('.btn-submit');
      const originalText = btn.textContent;
      btn.textContent = 'Enviant...';
      btn.disabled = true;

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          btn.textContent = 'Missatge enviat! ✓';
          btn.style.background = 'var(--green-vine)';
          form.reset();
        } else {
          btn.textContent = data.error || 'Error — torna-ho a provar';
          btn.style.background = '#c0392b';
        }
      })
      .catch(() => {
        btn.textContent = 'Error — torna-ho a provar';
        btn.style.background = '#c0392b';
      })
      .finally(() => {
        btn.disabled = false;
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = '';
        }, 4000);
      });
    });
  }
});
