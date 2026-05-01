// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');
const backTop = document.getElementById('back-top');

window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
    backTop.classList.add('visible');
  } else {
    navbar.classList.remove('scrolled');
    backTop.classList.remove('visible');
  }
  updateActiveNav();
});

// ===== HAMBURGER MENU =====
hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('active');
  navMenu.classList.toggle('open');
});

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('active');
    navMenu.classList.remove('open');
  });
});

// ===== ACTIVE NAV LINK ON SCROLL =====
function updateActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const scrollPos = window.scrollY + 120;
  sections.forEach(sec => {
    const top = sec.offsetTop;
    const height = sec.offsetHeight;
    const id = sec.getAttribute('id');
    const navLink = document.querySelector(`.nav-link[href="#${id}"]`);
    if (navLink) {
      if (scrollPos >= top && scrollPos < top + height) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        navLink.classList.add('active');
      }
    }
  });
}

// ===== BACK TO TOP =====
backTop.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ===== SCROLL ANIMATIONS (Intersection Observer) =====
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.classList.add('visible');
      }, i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));

// Stagger children inside grids
const staggerParents = document.querySelectorAll('.services-grid, .courses-grid, .events-grid, .upcoming-list');
staggerParents.forEach(parent => {
  const childObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const children = entry.target.querySelectorAll('.service-card, .course-card, .event-card, .upcoming-item');
        children.forEach((child, i) => {
          child.style.opacity = '0';
          child.style.transform = 'translateY(30px)';
          child.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
          setTimeout(() => {
            child.style.opacity = '1';
            child.style.transform = 'translateY(0)';
          }, 100 + i * 100);
        });
        childObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  childObserver.observe(parent);
});

// ===== FLOATING PARTICLES =====
const particlesContainer = document.getElementById('particles');
if (particlesContainer) {
  for (let i = 0; i < 30; i++) {
    const p = document.createElement('div');
    p.classList.add('particle');
    const size = Math.random() * 4 + 2;
    const colors = ['#0ea5e9', '#7c3aed', '#f59e0b', '#10b981'];
    p.style.cssText = `
      left: ${Math.random() * 100}%;
      width: ${size}px;
      height: ${size}px;
      background: ${colors[Math.floor(Math.random() * colors.length)]};
      animation-duration: ${Math.random() * 10 + 8}s;
      animation-delay: ${Math.random() * 8}s;
      opacity: 0.35;
      border-radius: 50%;
    `;
    particlesContainer.appendChild(p);
  }
}

// ===== COURSES FILTER TABS =====
const tabBtns = document.querySelectorAll('.tab-btn');
const courseCards = document.querySelectorAll('.course-card');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.getAttribute('data-tab');

    courseCards.forEach((card, i) => {
      const cat = card.getAttribute('data-category');
      if (tab === 'all' || cat === tab) {
        card.classList.remove('hidden');
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95) translateY(10px)';
        setTimeout(() => {
          card.style.transition = `opacity 0.4s ease ${i * 0.06}s, transform 0.4s ease ${i * 0.06}s`;
          card.style.opacity = '1';
          card.style.transform = 'scale(1) translateY(0)';
        }, 10);
      } else {
        card.classList.add('hidden');
      }
    });
  });
});

// ===== TESTIMONIALS SLIDER =====
const testitTrack = document.getElementById('testi-track');
const testiDotsContainer = document.getElementById('testi-dots');
const testiPrev = document.getElementById('testi-prev');
const testiNext = document.getElementById('testi-next');
const testiCards = document.querySelectorAll('.testi-card');
let currentTesti = 0;
let testiInterval;

// Create dots
testiCards.forEach((_, i) => {
  const dot = document.createElement('button');
  dot.classList.add('testi-dot');
  if (i === 0) dot.classList.add('active');
  dot.addEventListener('click', () => goToTesti(i));
  testiDotsContainer.appendChild(dot);
});

function goToTesti(index) {
  currentTesti = (index + testiCards.length) % testiCards.length;
  testitTrack.style.transform = `translateX(-${currentTesti * 100}%)`;
  document.querySelectorAll('.testi-dot').forEach((d, i) => {
    d.classList.toggle('active', i === currentTesti);
  });
}

testiPrev.addEventListener('click', () => { goToTesti(currentTesti - 1); resetInterval(); });
testiNext.addEventListener('click', () => { goToTesti(currentTesti + 1); resetInterval(); });

function resetInterval() {
  clearInterval(testiInterval);
  testiInterval = setInterval(() => goToTesti(currentTesti + 1), 5000);
}
testiInterval = setInterval(() => goToTesti(currentTesti + 1), 5000);

// ===== COUNTER ANIMATION (Hero Stats) =====
function animateCounter(el, target, suffix = '') {
  const duration = 2000;
  const step = Math.ceil(target / (duration / 16));
  let current = 0;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current.toLocaleString() + suffix;
    if (current >= target) clearInterval(timer);
  }, 16);
}

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const statNums = entry.target.querySelectorAll('.stat-num');
      const targets = [500, 200, 10000, 50];
      const suffixes = ['+', '+', '+', '+'];
      statNums.forEach((el, i) => {
        animateCounter(el, targets[i], suffixes[i]);
      });
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) statsObserver.observe(heroStats);

// ===== ADMISSION FORM SUBMIT =====
const admissionForm = document.getElementById('admission-form');
const admissionSuccess = document.getElementById('form-success');

if (admissionForm) {
  admissionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('adm-submit-btn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    btn.disabled = true;
    const data = Object.fromEntries(new FormData(admissionForm).entries());
    try {
      const res = await fetch('/api/admission', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });
      const result = await res.json();
      if (result.success) {
        admissionForm.style.display = 'none';
        admissionSuccess.style.display = 'block';
      } else {
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Inquiry';
        btn.disabled = false;
        alert('Submission failed. Please try again.');
      }
    } catch (err) {
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Inquiry';
      btn.disabled = false;
      alert('Could not reach server. Please call us directly.');
    }
  });
}

// ===== CONTACT FORM SUBMIT =====
const contactForm = document.getElementById('contact-form');
const contactSuccess = document.getElementById('contact-success');

if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('ct-submit-btn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    btn.disabled = true;
    const data = Object.fromEntries(new FormData(contactForm).entries());
    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });
      const result = await res.json();
      if (result.success) {
        contactForm.reset();
        contactSuccess.style.display = 'block';
        contactSuccess.innerHTML = '<i class="fas fa-check-circle"></i><h4>Message Sent!</h4><p>' + result.message + '</p>';
        setTimeout(() => { contactSuccess.style.display = 'none'; }, 6000);
      } else {
        alert('Failed to send. Please try again.');
      }
    } catch (err) {
      alert('Could not reach server. Please email us at hello@elevateglobal.in');
    }
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Message';
    btn.disabled = false;
  });
}

// ===== SMOOTH SCROLL FOR ALL ANCHOR LINKS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ===== SERVICE ICON COLORS =====
document.querySelectorAll('.service-icon').forEach(icon => {
  const color = icon.style.getPropertyValue('--icon-color');
  if (color) icon.style.background = `${color}18`;
  if (color) icon.style.color = color;
});

// ===== SESSION CHECK & NAVBAR UPDATE =====
async function checkSession() {
  try {
    const r = await fetch('/api/session');
    const res = await r.json();
    const authBtn = document.getElementById('nav-auth-btn');
    if (authBtn) {
      if (res.success) {
        authBtn.innerText = 'My Dashboard';
        authBtn.href = '/dashboard.html';
        authBtn.classList.remove('btn-outline');
        authBtn.classList.add('btn-primary');
      } else {
        authBtn.innerText = 'Student Login';
        authBtn.href = '/login.html';
      }
    }
  } catch (e) {
    console.error('Session check failed');
  }
}

window.addEventListener('DOMContentLoaded', checkSession);

console.log('%c🚀 Elevate Global Website Loaded', 'color:#0ea5e9;font-size:16px;font-weight:bold;');
