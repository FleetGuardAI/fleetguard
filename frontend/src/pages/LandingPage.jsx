import React from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ArrowRight,
  CheckCircle,
  MapPin,
  FileWarning,
  Fuel,
  Phone,
  ClipboardList,
  Upload,
  Bot,
  BadgeCheck,
  Truck,
  Eye,
  BarChart3,
  MessageSquare,
  Mail,
  Instagram,
  LayoutDashboard,
  Sparkles,
} from 'lucide-react';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * FleetGuard Landing/Marketing Page
 * All user-visible strings are translated via the t() function from LanguageContext.
 */
export default function LandingPage() {
  const { t } = useLanguage();

  const navItems = [
    { label: t('nav.problem'), href: '#problem' },
    { label: t('nav.howItWorks'), href: '#how-it-works' },
    { label: t('nav.features'), href: '#features' },
    { label: t('nav.demo'), href: '#demo' },
    { label: t('nav.about'), href: '#about' },
  ];

  return (
    <div className="min-h-screen bg-white font-sans text-slate-800">
      {/* ===== NAVBAR ===== */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-md border-b border-slate-100" id="navbar">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00e676] to-[#00c853] flex items-center justify-center shadow-md shadow-green-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-slate-800">Fleet </span>
              <span className="text-[#00c853]">Guard</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                {item.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <LanguageSelector variant="dark" />
            <Link
              to="/login"
              className="px-5 py-2.5 rounded-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-sm font-semibold transition-all duration-200 hidden sm:inline-flex items-center gap-2"
              id="dashboard-login-btn"
            >
              <LayoutDashboard className="w-4 h-4" />
              {t('nav.dashboard')}
            </Link>
            <a
              href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
              className="px-5 py-2.5 rounded-full bg-[#00c853] hover:bg-[#00b848]
                text-white text-sm font-semibold
                transition-all duration-200 hover:shadow-lg hover:shadow-green-500/30
                inline-flex items-center gap-2"
              id="book-demo-btn"
            >
              <Sparkles className="w-4 h-4" />
              {t('nav.bookDemo')}
            </a>
          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section className="pt-28 pb-20 px-6 overflow-hidden" id="hero">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          {/* Left — Copy */}
          <div className="animate-slide-up">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-50 border border-green-200 mb-6">
              <span className="w-2 h-2 rounded-full bg-[#00c853] animate-pulse" />
              <span className="text-xs font-semibold text-green-700">{t('hero.badge')}</span>
            </div>

            <h1 className="text-5xl lg:text-[56px] font-extrabold leading-[1.1] tracking-tight mb-6">
              {t('hero.title1')}{' '}
              <span className="block">{t('hero.title2')}</span>
              <span className="block">{t('hero.title3')} </span>
              <span className="text-[#00c853] italic">{t('hero.title4')}</span>
              <span className="block text-[#00c853] italic">{t('hero.title5')}</span>
            </h1>

            <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-lg">
              {t('hero.desc')}
            </p>

            <div className="flex items-center gap-4 mb-12">
              <a
                href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                  bg-[#00c853] hover:bg-[#00b848] text-white font-semibold
                  transition-all duration-200 hover:shadow-lg hover:shadow-green-500/30"
                id="hero-cta"
              >
                <Sparkles className="w-4 h-4" />
                {t('nav.bookDemo')}
              </a>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                  bg-white hover:bg-slate-50 border border-slate-200
                  text-slate-700 font-semibold transition-all duration-200"
              >
                <LayoutDashboard className="w-4 h-4 text-[#00c853]" />
                {t('nav.dashboardLogin')}
              </Link>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-10">
              <div>
                <p className="text-3xl font-extrabold text-[#00c853]">40%</p>
                <p className="text-xs text-slate-500 mt-1">{t('hero.stat1Label')}</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-[#00c853]">500+</p>
                <p className="text-xs text-slate-500 mt-1">{t('hero.stat2Label')}</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-800">0</p>
                <p className="text-xs text-slate-500 mt-1">{t('hero.stat3Label')}</p>
              </div>
            </div>
          </div>

          {/* Right — Dashboard Preview */}
          <div className="relative animate-fade-in hidden md:block">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-slate-900/20 border border-slate-200">
              <div className="bg-gradient-to-br from-surface-850 to-surface-950 p-4 aspect-video flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-16 h-16 text-brand-500 mx-auto mb-4 opacity-60" />
                  <p className="text-sm text-slate-400 font-medium">{t('hero.dashboardTitle')}</p>
                  <p className="text-xs text-slate-600 mt-1">{t('hero.dashboardSubtitle')}</p>
                  <Link to="/login" className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg bg-brand-500/20 text-brand-400 text-xs font-semibold hover:bg-brand-500/30 transition-colors">
                    {t('hero.openDashboard')} <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Floating cards */}
            <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl border border-slate-100 p-3 animate-slide-up" style={{ animationDelay: '300ms' }}>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-500" />
                <div>
                  <p className="text-xs font-bold text-slate-800">{t('hero.locationMatched')}</p>
                  <p className="text-[10px] text-slate-500">NH-48, Udaipur</p>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl border border-slate-100 p-3 animate-slide-up" style={{ animationDelay: '500ms' }}>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-[#00c853]" />
                <div>
                  <p className="text-xs font-bold text-slate-800">{t('hero.claimVerified')}</p>
                  <p className="text-[10px] text-slate-500">Truck RJ14 XX 1234</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== THE PROBLEM ===== */}
      <section className="py-20 px-6 bg-slate-50/50" id="problem">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00a844] uppercase tracking-widest">{t('problem.label')}</span>
            </div>
            <h2 className="text-4xl font-extrabold leading-tight">
              {t('problem.title1')}{' '}
              <span className="text-[#00c853]">{t('problem.title2')}</span>
            </h2>
            <p className="text-lg text-slate-500 mt-4 max-w-xl">
              {t('problem.desc')}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: FileWarning, title: t('problem.fake.title'), desc: t('problem.fake.desc'), color: 'text-red-500', bg: 'bg-red-50' },
              { icon: Fuel, title: t('problem.fuel.title'), desc: t('problem.fuel.desc'), color: 'text-rose-500', bg: 'bg-rose-50' },
              { icon: Eye, title: t('problem.proof.title'), desc: t('problem.proof.desc'), color: 'text-orange-500', bg: 'bg-orange-50' },
              { icon: Phone, title: t('problem.pressure.title'), desc: t('problem.pressure.desc'), color: 'text-amber-500', bg: 'bg-amber-50' },
            ].map((item, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-white border border-slate-100 hover:border-green-200
                  hover:shadow-lg hover:shadow-green-500/5 transition-all duration-300 group"
              >
                <div className={`p-3 rounded-xl ${item.bg} w-fit mb-4`}>
                  <item.icon className={`w-6 h-6 ${item.color}`} />
                </div>
                <h3 className="text-base font-bold text-slate-800 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* Extra card */}
          <div className="mt-5 p-6 rounded-2xl bg-white border border-slate-100 max-w-sm">
            <div className="p-3 rounded-xl bg-blue-50 w-fit mb-4">
              <ClipboardList className="w-6 h-6 text-blue-500" />
            </div>
            <h3 className="text-base font-bold text-slate-800 mb-2">{t('problem.tracking.title')}</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              {t('problem.tracking.desc')}
            </p>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="py-20 px-6" id="how-it-works">
        <div className="max-w-5xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-8 h-0.5 bg-[#00c853]" />
            <span className="text-xs font-bold text-[#00a844] uppercase tracking-widest">{t('how.label')}</span>
            <div className="w-8 h-0.5 bg-[#00c853]" />
          </div>
          <h2 className="text-4xl font-extrabold mb-3">
            {t('how.title1')} <span className="text-[#00c853]">{t('how.title2')}</span>
          </h2>
          <p className="text-lg text-slate-500 mb-16">
            {t('how.desc')}
          </p>

          {/* Steps */}
          <div className="relative">
            {/* Connection line */}
            <div className="absolute top-12 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-green-300 via-[#00c853] to-green-300 hidden md:block" />

            <div className="grid lg:grid-cols-3 gap-10">
              {[
                { num: 1, title: t('how.step1.title'), desc: t('how.step1.desc'), color: 'from-[#00e676] to-[#00c853]' },
                { num: 2, title: t('how.step2.title'), desc: t('how.step2.desc'), color: 'from-[#00c853] to-[#00a844]' },
                { num: 3, title: t('how.step3.title'), desc: t('how.step3.desc'), color: 'from-[#00a844] to-[#008837]' },
              ].map((step) => (
                <div key={step.num} className="flex flex-col items-center">
                  <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${step.color}
                    flex items-center justify-center text-white text-xl font-bold mb-6
                    shadow-lg shadow-green-500/25 relative z-10`}
                  >
                    {step.num}
                  </div>
                  <h3 className="text-lg font-bold text-slate-800 mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-500 leading-relaxed max-w-xs">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== WHATSAPP LIVE DEMO ===== */}
      <section className="py-20 px-6 bg-white border-y border-slate-100" id="demo">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00a844] uppercase tracking-widest">{t('demo.label')}</span>
            </div>
            <h2 className="text-4xl font-extrabold mb-4">
              {t('demo.title1')} <span className="text-[#00c853]">{t('demo.title2')}</span>
            </h2>
            <p className="text-lg text-slate-500 mb-8">
              {t('demo.desc')}
            </p>
            <div className="space-y-4">
              {[
                { num: '1️⃣', title: t('demo.step1.title'), desc: t('demo.step1.desc') },
                { num: '2️⃣', title: t('demo.step2.title'), desc: t('demo.step2.desc') },
                { num: '3️⃣', title: t('demo.step3.title'), desc: t('demo.step3.desc') },
              ].map((w) => (
                <div key={w.num} className="flex gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-xl">{w.num}</div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-base">{w.title}</h3>
                    <p className="text-sm text-slate-500 mt-0.5">{w.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — WhatsApp Window Mockup */}
          <div className="relative">
            <div className="rounded-2xl border border-slate-200 overflow-hidden shadow-2xl bg-[#efeae2]">
              {/* Header */}
              <div className="bg-[#005c4b] text-white p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#00c853] text-white flex items-center justify-center font-bold">
                  FG
                </div>
                <div>
                  <h4 className="font-bold text-sm">FleetGuard Bot</h4>
                  <p className="text-[10px] text-emerald-200">online</p>
                </div>
              </div>

              {/* Chat Body */}
              <div className="p-4 space-y-4 max-h-[420px] overflow-y-auto font-sans text-xs">
                {/* Driver message */}
                <div className="flex justify-end">
                  <div className="bg-[#d9fdd3] text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm relative">
                    {t('chat.driverMsg')}
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:14 AM</span>
                  </div>
                </div>

                {/* Bot message */}
                <div className="flex justify-start">
                  <div className="bg-white text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm">
                    {t('chat.botMsg')}
                    <br/><br/>
                    📹 {t('chat.repairVideo')}<br/>
                    🧾 {t('chat.billPhoto')}<br/>
                    📍 {t('chat.liveLocation')}<br/>
                    💰 {t('chat.requestedAmount')}
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:14 AM</span>
                  </div>
                </div>

                {/* Driver uploads video */}
                <div className="flex justify-end">
                  <div className="bg-[#d9fdd3] text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm">
                    📹 <em>video_repair.mp4</em>
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:16 AM</span>
                  </div>
                </div>

                {/* Driver uploads bill and location */}
                <div className="flex justify-end">
                  <div className="bg-[#d9fdd3] text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm">
                    🧾 <em>bill_photo.jpg</em><br/>
                    📍 NH-48, Udaipur<br/>
                    💰 ₹450
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:17 AM</span>
                  </div>
                </div>

                {/* Bot verifies */}
                <div className="flex justify-start">
                  <div className="bg-white text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm">
                    ✅ <strong>{t('chat.verificationComplete')}</strong><br/><br/>
                    🚛 Truck: RJ14 XX 1234<br/>
                    🔧 Issue: Tyre Puncture<br/>
                    💰 Amount: ₹450<br/>
                    📍 Location: Verified ✓<br/>
                    🧾 Bill: Authentic ✓<br/>
                    ⚠️ Fraud Risk: Low<br/><br/>
                    {t('chat.forwardingOwner')}
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:19 AM</span>
                  </div>
                </div>

                {/* Owner alert */}
                <div className="flex justify-start">
                  <div className="bg-[#e1f5fe] border border-blue-200 text-slate-800 p-2.5 rounded-lg max-w-[80%] shadow-sm">
                    👤 <strong>{t('chat.ownerAlert')}</strong><br/><br/>
                    {t('chat.verifiedExpense')}<br/>
                    Truck RJ14 XX 1234<br/>
                    Issue: Puncture — ₹450<br/><br/>
                    ✅ {t('chat.allChecksPassed')}<br/>
                    📎 {t('chat.viewProof')}
                    <span className="text-[9px] text-slate-400 block text-right mt-1">10:19 AM</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section className="py-20 px-6 bg-slate-50/50" id="features">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-8 h-0.5 bg-[#00c853]" />
              <span className="text-xs font-bold text-[#00a844] uppercase tracking-widest">{t('features.label')}</span>
              <div className="w-8 h-0.5 bg-[#00c853]" />
            </div>
            <h2 className="text-4xl font-extrabold">
              {t('features.title1')} <span className="text-[#00c853]">{t('features.title2')}</span>
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: MessageSquare, title: t('features.whatsapp.title'), desc: t('features.whatsapp.desc') },
              { icon: Eye, title: t('features.ocr.title'), desc: t('features.ocr.desc') },
              { icon: MapPin, title: t('features.location.title'), desc: t('features.location.desc') },
              { icon: BarChart3, title: t('features.dashboard.title'), desc: t('features.dashboard.desc') },
              { icon: Fuel, title: t('features.fuel.title'), desc: t('features.fuel.desc') },
              { icon: Shield, title: t('features.risk.title'), desc: t('features.risk.desc') },
            ].map((feat, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-white border border-slate-100
                  hover:border-green-200 hover:shadow-lg hover:shadow-green-500/5
                  transition-all duration-300 group"
              >
                <div className="p-3 rounded-xl bg-green-50 w-fit mb-4 group-hover:bg-green-100 transition-colors">
                  <feat.icon className="w-6 h-6 text-[#00a844]" />
                </div>
                <h3 className="text-base font-bold text-slate-800 mb-2">{feat.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="py-20 px-6 bg-gradient-to-br from-[#00a844] via-[#00c853] to-[#00e676]" id="cta">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-extrabold text-white mb-4 italic">
            {t('cta.title1')} <span className="not-italic">{t('cta.title2')}</span>
          </h2>
          <p className="text-lg text-white/80 mb-8">
            {t('cta.desc')}
          </p>
          <a
            href="mailto:fleetgaurdinfo@gmail.com?subject=Book%20Demo"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full
              bg-white hover:bg-slate-50 text-[#00a844] font-bold
              transition-all duration-200 hover:shadow-xl hover:shadow-green-900/30
              text-base"
            id="cta-btn"
          >
            <Sparkles className="w-5 h-5" />
            {t('nav.bookDemo')}
          </a>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="bg-slate-900 text-slate-400 py-16 px-6" id="about">
        <div className="max-w-7xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00e676] to-[#00c853] flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold">
                <span className="text-white">Fleet </span>
                <span className="text-[#00e676]">Guard</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed">
              {t('footer.tagline')}
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">{t('footer.product')}</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="#features" className="hover:text-white transition-colors">{t('nav.features')}</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">{t('nav.howItWorks')}</a></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">{t('footer.liveDemo')}</Link></li>
              <li><a href="#demo" className="hover:text-white transition-colors">{t('nav.bookDemo')}</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">{t('footer.company')}</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="#about" className="hover:text-white transition-colors">{t('nav.about')}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t('footer.testimonials')}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t('footer.careers')}</a></li>
              <li><a href="#" className="hover:text-white transition-colors">{t('footer.blog')}</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">{t('footer.contact')}</h4>
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-center gap-2">
                <Mail className="w-3.5 h-3.5" />
                <a href="mailto:fleetguardinfo@gmail.com" className="hover:text-white transition-colors">
                  fleetguardinfo@gmail.com
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Instagram className="w-3.5 h-3.5" />
                <a href="#" className="hover:text-white transition-colors">Instagram</a>
              </li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-slate-800 flex items-center justify-between">
          <p className="text-xs text-slate-600">{t('footer.copyright')}</p>
          <div className="flex items-center gap-3">
            <Truck className="w-5 h-5 text-slate-700" />
            <BarChart3 className="w-5 h-5 text-slate-700" />
          </div>
        </div>
      </footer>
    </div>
  );
}
