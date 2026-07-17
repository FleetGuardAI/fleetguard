import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export default function HomePage() {
  const containerRef = useRef(null);
  const [cssLoaded, setCssLoaded] = useState(false);

  useEffect(() => {
    // Load homepage CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/homepage.css';
    link.id = 'homepage-css';
    link.onload = () => setCssLoaded(true);
    document.head.appendChild(link);

    // Load Google Fonts for homepage
    const fontLink = document.createElement('link');
    fontLink.rel = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap';
    fontLink.id = 'homepage-font';
    document.head.appendChild(fontLink);

    return () => {
      document.getElementById('homepage-css')?.remove();
      document.getElementById('homepage-font')?.remove();
    };
  }, []);

  // Homepage script logic
  useEffect(() => {
    if (!containerRef.current || !cssLoaded) return;
    const container = containerRef.current;

    // Navbar scroll
    const navbar = container.querySelector('.navbar');
    const onScroll = () => navbar?.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll);

    // Mobile menu
    const toggle = container.querySelector('.nav-toggle');
    const links = container.querySelector('.nav-links');
    const onToggle = () => {
      links?.classList.toggle('open');
      if (toggle) toggle.textContent = links?.classList.contains('open') ? '✕' : '☰';
    };
    toggle?.addEventListener('click', onToggle);
    links?.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => { links?.classList.remove('open'); if (toggle) toggle.textContent = '☰'; });
    });

    // Scroll reveal
    const reveals = container.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(entries => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('visible'), i * 80);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    reveals.forEach(el => observer.observe(el));

    // Counter animation
    const counters = container.querySelectorAll('[data-count]');
    const counterObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.dataset.count || '0');
          const suffix = el.dataset.suffix || '';
          let current = 0;
          const step = Math.max(1, Math.floor(target / 60));
          const timer = setInterval(() => {
            current += step;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = current.toLocaleString() + suffix;
          }, 20);
          counterObserver.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => counterObserver.observe(el));

    // Chat replay
    const chatBody = container.querySelector('.chat-body');
    if (chatBody) {
      const chatObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            chatBody.querySelectorAll('.msg').forEach(m => {
              m.style.animation = 'none';
              m.offsetHeight;
              m.style.animation = '';
            });
          }
        });
      }, { threshold: 0.3 });
      chatObserver.observe(chatBody);
    }

    // Smooth scroll
    container.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        const href = anchor.getAttribute('href');
        if (!href || href === '#') return;
        e.preventDefault();
        const target = container.querySelector(href);
        target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    return () => {
      window.removeEventListener('scroll', onScroll);
      observer.disconnect();
      counterObserver.disconnect();
    };
  }, [cssLoaded]);

  return (
    <div ref={containerRef} style={{ opacity: cssLoaded ? 1 : 0, transition: 'opacity 0.3s' }}>
      {/* NAVBAR */}
      <nav className="navbar" id="navbar">
        <div className="container">
          <a href="#" className="nav-logo">
            <svg viewBox="0 0 32 32" fill="none" width="32" height="32"><rect width="32" height="32" rx="8" fill="#25D366"/><path d="M16 6L8 12v8l8 6 8-6v-8L16 6z" fill="#fff" opacity="0.9"/><path d="M16 10l-4 3v5l4 3 4-3v-5l-4-3z" fill="#25D366"/></svg>
            Fleet<span className="gradient-text">Guard</span>
          </a>
          <div className="nav-links">
            <a href="#problem">Problem</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#demo">Demo</a>
            <a href="#founder">About</a>
          </div>
          <div className="nav-cta">
            <Link to="/login" className="btn btn-primary">Dashboard Login</Link>
          </div>
          <button className="nav-toggle" aria-label="Menu">☰</button>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero" id="hero">
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge"><span className="dot"></span> WhatsApp-First Verification Platform</div>
            <h1>Verify Every Emergency Truck Expense <span className="gradient-text">Before Payment</span></h1>
            <p>FleetGuard helps fleet owners prevent fake repair, fuel and puncture claims using AI + human verification directly on WhatsApp.</p>
            <div className="hero-buttons">
              <a href="mailto:fleetguardinfo@gmail.com?subject=Enquiry&body=Hi%20FleetGuard%20Team%2C%0A%0AI%20would%20like%20to%20book%20a%20demo.%0A%0AName%3A%20%0AMobile%3A%20%0A%0AThank%20you." className="btn btn-primary btn-lg">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17 2H7a5 5 0 00-5 5v10a5 5 0 005 5h10a5 5 0 005-5V7a5 5 0 00-5-5zm-1 14H8a1 1 0 010-2h8a1 1 0 010 2zm0-4H8a1 1 0 010-2h8a1 1 0 010 2zm0-4H8a1 1 0 010-2h8a1 1 0 010 2z"/></svg>
                Book Demo
              </a>
              <a href="#demo" className="btn btn-secondary btn-lg">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
                Watch Demo
              </a>
            </div>
            <div className="hero-stats">
              <div className="hero-stat"><h3><span data-count="40" data-suffix="%" className="gradient-text">0%</span></h3><p>Fake Claims Blocked</p></div>
              <div className="hero-stat"><h3><span data-count="500" data-suffix="+" className="gradient-text">0+</span></h3><p>Trucks Monitored</p></div>
              <div className="hero-stat"><h3><span data-count="0" className="gradient-text">0</span></h3><p>App Downloads Needed</p></div>
            </div>
          </div>
          <div className="hero-visual">
            <img src="/assets/dashboard-mockup.png" alt="FleetGuard Dashboard"/>
            <div className="float-card card-1"><div className="fc-icon green">✅</div><div className="fc-text"><h4>Claim Verified</h4><p>Truck RJ14 XX 1234</p></div></div>
            <div className="float-card card-2"><div className="fc-icon blue">📍</div><div className="fc-text"><h4>Location Matched</h4><p>NH-48, Udaipur</p></div></div>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className="section problems" id="problem">
        <div className="container">
          <div className="section-label">The Problem</div>
          <h2 className="section-title reveal">Fleet Owners Lose Lakhs to <span className="gradient-text">Unverified Claims</span></h2>
          <p className="section-subtitle reveal">Drivers send emergency payment requests — but there's no way to know what's real and what's fabricated.</p>
          <div className="problems-grid">
            {[
              { icon: '🛞', title: 'Fake Puncture Claims', desc: 'Drivers report punctures that never happened to pocket repair money.' },
              { icon: '⛽', title: 'Inflated Fuel Requests', desc: 'Fuel amounts overstated with no receipts or verifiable proof.' },
              { icon: '📵', title: 'No Proof Before Payment', desc: 'Owners pay blindly over phone calls with zero documentation.' },
              { icon: '📞', title: 'Pressure Calls from Drivers', desc: 'Urgent calls create pressure to send money immediately without checks.' },
            ].map(p => (
              <div key={p.title} className="problem-card reveal">
                <div className="pc-icon">{p.icon}</div>
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="section" id="how-it-works">
        <div className="container">
          <div style={{ textAlign: 'center' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>How It Works</div>
            <h2 className="section-title reveal">Three Steps to <span className="gradient-text">Verified Payments</span></h2>
            <p className="section-subtitle reveal" style={{ margin: '0 auto' }}>Simple, fast, and works entirely on WhatsApp — no apps to install.</p>
          </div>
          <div className="steps-grid">
            {[
              { icon: '📤', num: 1, title: 'Driver Uploads Proof', desc: 'Driver sends repair video, bill photo, live location and requested amount on WhatsApp.' },
              { icon: '🤖', num: 2, title: 'AI + Human Verification', desc: 'Our system checks bill authenticity, duplicate claims, location match and suspicious pricing.' },
              { icon: '✅', num: 3, title: 'Owner Gets Verified Report', desc: 'Fleet owner receives a complete verified approval request with all proof before making payment.' },
            ].map(s => (
              <div key={s.num} className="step-card reveal">
                <span className="step-icon">{s.icon}</span>
                <div className="step-number">{s.num}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section features" id="features">
        <div className="container">
          <div style={{ textAlign: 'center' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>Features</div>
            <h2 className="section-title reveal">Everything You Need to <span className="gradient-text">Control Fleet Expenses</span></h2>
            <p className="section-subtitle reveal" style={{ margin: '0 auto' }}>Built for the realities of Indian trucking operations.</p>
          </div>
          <div className="features-grid">
            {[
              { icon: '💬', title: 'WhatsApp-First Workflow', desc: 'Entire verification process runs on WhatsApp. Drivers and owners already use it daily.' },
              { icon: '🤖', title: 'AI + Human Verification', desc: 'Dual-layer check combining AI analysis with human review for maximum accuracy.' },
              { icon: '📍', title: 'Live Location Verification', desc: 'Cross-check claimed location with actual GPS data to catch location fraud.' },
              { icon: '🧾', title: 'Bill Photo Verification', desc: 'AI scans bills for tampering, duplicate entries and inflated pricing.' },
              { icon: '🚨', title: 'Fraud Detection Alerts', desc: 'Automatic flagging of suspicious patterns, repeat claims and anomalies.' },
              { icon: '📂', title: 'Centralized Expense Records', desc: 'Every claim, receipt and verification stored in one searchable dashboard.' },
              { icon: '🔔', title: 'Instant Owner Alerts', desc: 'Real-time notifications the moment a claim is submitted and verified.' },
              { icon: '📲', title: 'Zero App Installation', desc: 'No downloads. No training. Just WhatsApp. Works on any phone your drivers already have.' },
            ].map(f => (
              <div key={f.title} className="feature-card reveal">
                <div className="fi">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DEMO CHAT */}
      <section className="section chat-demo" id="demo">
        <div className="container">
          <div>
            <div className="section-label">Live Demo</div>
            <h2 className="section-title reveal">See FleetGuard <span className="gradient-text">in Action</span></h2>
            <p className="section-subtitle reveal">A real WhatsApp conversation showing how driver claims get verified before you pay a single rupee.</p>
            <div style={{ marginTop: '32px' }}>
              {[
                { num: '1️⃣', title: 'Driver Reports Issue', desc: 'The driver messages the FleetGuard bot about an emergency expense.' },
                { num: '2️⃣', title: 'Bot Collects Proof', desc: 'FleetGuard asks for video, bill photo, location and amount — all on WhatsApp.' },
                { num: '3️⃣', title: 'Owner Gets Verified Alert', desc: 'You receive a clean, verified summary with all proof before approving payment.' },
              ].map(w => (
                <div key={w.num} className="why-card reveal" style={{ marginBottom: '16px' }}>
                  <div className="wi">{w.num}</div>
                  <div><h3>{w.title}</h3><p>{w.desc}</p></div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="chat-window reveal">
              <div className="chat-header">
                <div className="chat-avatar">FG</div>
                <div className="chat-name"><h4>FleetGuard Bot</h4><p>online</p></div>
              </div>
              <div className="chat-body">
                <div className="msg msg-out">Puncture issue on highway<span className="time">10:14 AM</span></div>
                <div className="msg msg-in">Hello! I'll help verify this expense. Please upload:<br/><br/>📹 Repair video<br/>🧾 Bill photo<br/>📍 Live location<br/>💰 Requested amount<span className="time">10:14 AM</span></div>
                <div className="msg msg-out">📹 <em>video_repair.mp4</em><span className="time">10:16 AM</span></div>
                <div className="msg msg-out">🧾 <em>bill_photo.jpg</em><br/>📍 NH-48, Udaipur<br/>💰 ₹450<span className="time">10:17 AM</span></div>
                <div className="msg msg-in">✅ <strong>Verification Complete</strong><br/><br/>🚛 Truck: RJ14 XX 1234<br/>🔧 Issue: Tyre Puncture<br/>💰 Amount: ₹450<br/>📍 Location: Verified ✓<br/>🧾 Bill: Authentic ✓<br/>⚠️ Fraud Risk: Low<br/><br/>Forwarding to fleet owner...<span className="time">10:19 AM</span></div>
                <div className="msg msg-in" style={{ background: 'rgba(37,211,102,0.15)', border: '1px solid rgba(37,211,102,0.2)' }}>👤 <strong>Owner Alert</strong><br/><br/>Verified expense request:<br/>Truck RJ14 XX 1234<br/>Issue: Puncture — ₹450<br/><br/>✅ All checks passed<br/>📎 View full proof report<span className="time">10:19 AM</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* WHY FLEETGUARD */}
      <section className="section" id="why" style={{ background: 'var(--bg-tertiary)' }}>
        <div className="container">
          <div style={{ textAlign: 'center' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>Why FleetGuard</div>
            <h2 className="section-title reveal">Benefits That <span className="gradient-text">Impact Your Bottom Line</span></h2>
            <p className="section-subtitle reveal" style={{ margin: '0 auto' }}>FleetGuard isn't just software — it's operational control for your fleet.</p>
          </div>
          <div className="why-grid">
            {[
              { icon: '🛡️', title: 'Reduce Fake Expenses', desc: 'AI-powered verification catches fabricated claims before they cost you money.' },
              { icon: '👁️', title: 'Operational Visibility', desc: 'See every expense across your entire fleet in real-time from your phone.' },
              { icon: '📋', title: 'Proof Before Payment', desc: 'Never pay without verified documentation again. Every claim is backed by evidence.' },
              { icon: '⚡', title: 'Faster Decision Making', desc: 'Get verified reports instantly. Approve or reject claims in seconds, not hours.' },
              { icon: '💰', title: 'Better Expense Control', desc: 'Track, analyze and optimize fleet expenses with centralized data and insights.' },
              { icon: '🔒', title: 'Build Driver Accountability', desc: 'Structured verification creates a culture of honesty and transparency.' },
            ].map(w => (
              <div key={w.title} className="why-card reveal">
                <div className="wi">{w.icon}</div>
                <div><h3>{w.title}</h3><p>{w.desc}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOUNDERS */}
      <section className="section founders" id="founder">
        <div className="container">
          <div style={{ textAlign: 'center' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>Meet the Founders</div>
            <h2 className="section-title reveal">The Team Behind <span className="gradient-text">FleetGuard</span></h2>
            <p className="section-subtitle reveal" style={{ margin: '0 auto' }}>Young entrepreneurs solving operational trust problems in India's trucking industry through technology and WhatsApp-first workflows.</p>
          </div>
          <div className="founders-grid">
            <div className="founder-card reveal">
              <div className="founder-info">
                <h3>Rudra Rathore</h3>
                <p className="founder-role">Co-Founder &amp; CEO</p>
                <blockquote>"I saw fleet owners losing lakhs every month to unverified expense claims. I built FleetGuard to bring trust and transparency using the one platform every driver already uses: WhatsApp."</blockquote>
                <div className="founder-links">
                  <a href="https://www.linkedin.com/in/rudrapratap-singh-rathore-930060205" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">in</a>
                  <a href="https://www.instagram.com/rudrapratapsinghrathore001" target="_blank" rel="noopener noreferrer" aria-label="Instagram">📷</a>
                </div>
              </div>
            </div>
            <div className="founder-card reveal">
              <div className="founder-info">
                <h3>Suryansh Chaudhary</h3>
                <p className="founder-role">Co-Founder &amp; COO</p>
                <blockquote>"Logistics runs on trust — but trust without verification is risk. We're building the verification layer that fleet operations have always needed, right inside WhatsApp."</blockquote>
                <div className="founder-links">
                  <a href="https://www.linkedin.com/in/suryansh-chaudhary-cse/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">in</a>
                  <a href="https://www.instagram.com/_suryanzh" target="_blank" rel="noopener noreferrer" aria-label="Instagram">📷</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="section" id="testimonials">
        <div className="container">
          <div style={{ textAlign: 'center' }}>
            <div className="section-label" style={{ justifyContent: 'center' }}>Testimonials</div>
            <h2 className="section-title reveal">Trusted by <span className="gradient-text">Fleet Operators</span></h2>
            <p className="section-subtitle reveal" style={{ margin: '0 auto' }}>Hear from fleet owners who transformed their expense management.</p>
          </div>
          <div className="testimonials-grid">
            {[
              { stars: '★★★★★', text: '"Before FleetGuard, my drivers would call and demand ₹2,000 for a puncture. Now I get video proof, bill photo and GPS location — all verified. My fake claims dropped by 40% in the first month."', initials: 'MK', name: 'Mahesh Kumar', role: 'Fleet Owner · 45 Trucks · Jaipur' },
              { stars: '★★★★★', text: '"The best part is zero app installation. My drivers are not tech-savvy — they can barely use smartphones. But WhatsApp? They all know it. FleetGuard just works without any training."', initials: 'PS', name: 'Priya Sharma', role: 'Logistics Manager · TransLink Corp · Mumbai' },
              { stars: '★★★★★', text: '"I manage 120+ trucks across 3 states. FleetGuard gives me a single dashboard for every emergency expense. The fraud detection alone saved us ₹3 lakhs last quarter."', initials: 'RS', name: 'Rajveer Singh', role: 'Transport Operator · Singh Logistics · Delhi NCR' },
            ].map(t => (
              <div key={t.name} className="testimonial-card reveal">
                <div className="tc-stars">{t.stars}</div>
                <p className="tc-text">{t.text}</p>
                <div className="tc-author">
                  <div className="tc-avatar">{t.initials}</div>
                  <div className="tc-info"><h4>{t.name}</h4><p>{t.role}</p></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section cta-section" id="cta">
        <div className="container">
          <div className="section-label" style={{ justifyContent: 'center' }}>Get Started</div>
          <h2 className="section-title reveal">Modernize Emergency <span className="gradient-text">Fleet Payments</span></h2>
          <p className="section-subtitle reveal">Stop losing money to unverified claims. Start verifying every expense on WhatsApp today.</p>
          <a href="mailto:fleetguardinfo@gmail.com?subject=Enquiry&body=Hi%20FleetGuard%20Team%2C%0A%0AI%20would%20like%20to%20book%20a%20demo.%0A%0AName%3A%20%0AMobile%3A%20%0A%0AThank%20you." className="btn btn-primary btn-lg reveal" style={{ marginTop: '8px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
            Book Free Demo
          </a>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-brand">
              <a href="#" className="nav-logo">
                <svg viewBox="0 0 32 32" fill="none" width="28" height="28"><rect width="32" height="32" rx="8" fill="#25D366"/><path d="M16 6L8 12v8l8 6 8-6v-8L16 6z" fill="#fff" opacity="0.9"/><path d="M16 10l-4 3v5l4 3 4-3v-5l-4-3z" fill="#25D366"/></svg>
                Fleet<span className="gradient-text">Guard</span>
              </a>
              <p>AI-powered expense verification for fleet owners. Built on WhatsApp. No apps needed.</p>
            </div>
            <div className="footer-col">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#how-it-works">How It Works</a>
              <a href="#demo">Live Demo</a>
              <a href="#cta">Book Demo</a>
            </div>
            <div className="footer-col">
              <h4>Company</h4>
              <a href="#founder">About</a>
              <a href="#testimonials">Testimonials</a>
              <a href="#">Careers</a>
              <a href="#">Blog</a>
            </div>
            <div className="footer-col">
              <h4>Contact</h4>
              <a href="mailto:fleetguardinfo@gmail.com">fleetguardinfo@gmail.com</a>
              <a href="https://www.instagram.com/fleetgaurd/" target="_blank" rel="noopener noreferrer">Instagram</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2026 FleetGuard. All rights reserved.</p>
            <div className="footer-social">
              <a href="mailto:fleetguardinfo@gmail.com" aria-label="Email">✉️</a>
              <a href="https://www.instagram.com/fleetgaurd/" target="_blank" rel="noopener noreferrer" aria-label="Instagram">📷</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
