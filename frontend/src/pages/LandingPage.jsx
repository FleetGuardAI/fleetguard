import React from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ArrowRight,
  Play,
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
} from 'lucide-react';

/**
 * FleetGuard Landing/Marketing Page
 * Closely replicates the provided reference image UI.
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-slate-800">
      {/* ===== NAVBAR ===== */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-b border-slate-100" id="navbar">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-slate-800">Fleet </span>
              <span className="text-emerald-600">Guard</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {['Problem', 'How It Works', 'Features', 'Demo', 'About'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase().replace(/\s+/g, '-')}`}
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                {item}
              </a>
            ))}
          </div>

          <Link
            to="/dashboard"
            className="px-5 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-700
              text-white text-sm font-semibold
              transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
            id="book-demo-btn"
          >
            Book Demo
          </Link>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section className="pt-28 pb-20 px-6 overflow-hidden" id="hero">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          {/* Left — Copy */}
          <div className="animate-slide-up">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold text-emerald-700">WhatsApp-First Verification Platform</span>
            </div>

            <h1 className="text-5xl lg:text-[56px] font-extrabold leading-[1.1] tracking-tight mb-6">
              Verify Every{' '}
              <span className="block">Emergency Truck</span>
              <span className="block">Expense </span>
              <span className="text-emerald-600 italic">Before</span>
              <span className="block text-emerald-600 italic">Payment</span>
            </h1>

            <p className="text-lg text-slate-500 leading-relaxed mb-8 max-w-lg">
              FleetGuard helps fleet owners prevent fake repair, fuel and puncture claims using AI + human verification directly on WhatsApp.
            </p>

            <div className="flex items-center gap-4 mb-12">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                  bg-emerald-600 hover:bg-emerald-700 text-white font-semibold
                  transition-all duration-200 hover:shadow-lg hover:shadow-emerald-500/25"
                id="hero-cta"
              >
                <Mail className="w-4 h-4" />
                Book Demo
              </Link>
              <button className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                bg-white hover:bg-slate-50 border border-slate-200
                text-slate-700 font-semibold transition-all duration-200"
              >
                <Play className="w-4 h-4 fill-slate-700" />
                Watch Demo
              </button>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-10">
              <div>
                <p className="text-3xl font-extrabold text-emerald-600">40%</p>
                <p className="text-xs text-slate-500 mt-1">Fake Claims Blocked</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-emerald-600">500+</p>
                <p className="text-xs text-slate-500 mt-1">Trucks Monitored</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-800">0</p>
                <p className="text-xs text-slate-500 mt-1">App Downloads Needed</p>
              </div>
            </div>
          </div>

          {/* Right — Dashboard Preview */}
          <div className="relative animate-fade-in hidden lg:block">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-slate-900/20 border border-slate-200">
              <div className="bg-gradient-to-br from-surface-850 to-surface-950 p-4 aspect-video flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-16 h-16 text-brand-500 mx-auto mb-4 opacity-60" />
                  <p className="text-sm text-slate-400 font-medium">FleetGuard Dashboard</p>
                  <p className="text-xs text-slate-600 mt-1">Real-time monitoring & fraud detection</p>
                  <Link to="/dashboard" className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-lg bg-brand-500/20 text-brand-400 text-xs font-semibold hover:bg-brand-500/30 transition-colors">
                    Open Dashboard <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Floating cards */}
            <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl border border-slate-100 p-3 animate-slide-up" style={{ animationDelay: '300ms' }}>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-500" />
                <div>
                  <p className="text-xs font-bold text-slate-800">Location Matched</p>
                  <p className="text-[10px] text-slate-500">NH-48, Udaipur</p>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl border border-slate-100 p-3 animate-slide-up" style={{ animationDelay: '500ms' }}>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <div>
                  <p className="text-xs font-bold text-slate-800">Claim Verified</p>
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
              <div className="w-8 h-0.5 bg-emerald-500" />
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-widest">The Problem</span>
            </div>
            <h2 className="text-4xl font-extrabold leading-tight">
              Fleet Owners Lose Lakhs to{' '}
              <span className="text-emerald-600">Unverified Claims</span>
            </h2>
            <p className="text-lg text-slate-500 mt-4 max-w-xl">
              Drivers send emergency payment requests — but there&apos;s no way to know what&apos;s real and what&apos;s fabricated.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: FileWarning, title: 'Fake Puncture Claims', desc: 'Drivers report punctures that never happened to pocket repair money.', color: 'text-red-500', bg: 'bg-red-50' },
              { icon: Fuel, title: 'Inflated Fuel Requests', desc: 'Fuel amounts overstated with no receipts or verifiable proof.', color: 'text-rose-500', bg: 'bg-rose-50' },
              { icon: Eye, title: 'No Proof Before Payment', desc: 'Owners pay blindly over phone calls with zero documentation.', color: 'text-orange-500', bg: 'bg-orange-50' },
              { icon: Phone, title: 'Pressure Calls from Drivers', desc: 'Urgent calls create pressure to send money immediately without checks.', color: 'text-amber-500', bg: 'bg-amber-50' },
            ].map((item, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-white border border-slate-100 hover:border-emerald-200
                  hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300 group"
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
            <h3 className="text-base font-bold text-slate-800 mb-2">Poor Expense Tracking</h3>
            <p className="text-sm text-slate-500 leading-relaxed">
              No centralized records. Expenses scattered across calls, messages and memory.
            </p>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="py-20 px-6" id="how-it-works">
        <div className="max-w-5xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-8 h-0.5 bg-emerald-500" />
            <span className="text-xs font-bold text-emerald-600 uppercase tracking-widest">How It Works</span>
            <div className="w-8 h-0.5 bg-emerald-500" />
          </div>
          <h2 className="text-4xl font-extrabold mb-3">
            Three Steps to <span className="text-emerald-600">Verified Payments</span>
          </h2>
          <p className="text-lg text-slate-500 mb-16">
            Simple, fast, and works entirely on WhatsApp — no apps to install.
          </p>

          {/* Steps */}
          <div className="relative">
            {/* Connection line */}
            <div className="absolute top-12 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-emerald-300 via-emerald-400 to-emerald-300 hidden lg:block" />

            <div className="grid lg:grid-cols-3 gap-10">
              {[
                { num: 1, icon: Upload, title: 'Driver Uploads Proof', desc: 'Driver sends repair video, bill photo, live location and requested amount on WhatsApp.', color: 'from-emerald-500 to-green-600' },
                { num: 2, icon: Bot, title: 'AI + Human Verification', desc: 'Our system checks bill authenticity, duplicate claims, location match and suspicious pricing.', color: 'from-emerald-500 to-teal-600' },
                { num: 3, icon: BadgeCheck, title: 'Owner Gets Verified Report', desc: 'Fleet owner receives a complete verified approval request with all proof before making payment.', color: 'from-emerald-500 to-emerald-700' },
              ].map((step) => (
                <div key={step.num} className="flex flex-col items-center">
                  <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${step.color}
                    flex items-center justify-center text-white text-xl font-bold mb-6
                    shadow-lg shadow-emerald-500/20 relative z-10`}
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

      {/* ===== FEATURES ===== */}
      <section className="py-20 px-6 bg-slate-50/50" id="features">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="w-8 h-0.5 bg-emerald-500" />
              <span className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Features</span>
              <div className="w-8 h-0.5 bg-emerald-500" />
            </div>
            <h2 className="text-4xl font-extrabold">
              Everything You Need to <span className="text-emerald-600">Protect Your Fleet</span>
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: MessageSquare, title: 'WhatsApp Expense Bot', desc: 'Drivers submit receipts and claims via WhatsApp. No app installs, no training needed.' },
              { icon: Eye, title: 'AI Receipt OCR', desc: 'OpenAI Vision extracts vendor, amount, date from receipt photos automatically.' },
              { icon: MapPin, title: 'Live Location Match', desc: 'Verify the driver is actually at the repair location, not fabricating claims.' },
              { icon: BarChart3, title: 'Real-Time BI Dashboard', desc: 'KPIs, fuel charts, expense trends, and driver risk scores — all in one view.' },
              { icon: Fuel, title: 'Fuel Theft Detection', desc: 'EMA-smoothed telemetry detects suspicious fuel drops when the truck is stationary.' },
              { icon: Shield, title: 'Driver Risk Scoring', desc: 'AI scores each driver 0-100 based on rejected claims, price inflation, and theft associations.' },
            ].map((feat, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-white border border-slate-100
                  hover:border-emerald-200 hover:shadow-lg hover:shadow-emerald-500/5
                  transition-all duration-300 group"
              >
                <div className="p-3 rounded-xl bg-emerald-50 w-fit mb-4 group-hover:bg-emerald-100 transition-colors">
                  <feat.icon className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="text-base font-bold text-slate-800 mb-2">{feat.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="py-20 px-6 bg-gradient-to-br from-emerald-700 via-green-700 to-emerald-800" id="demo">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-extrabold text-white mb-4 italic">
            Modernize Emergency <span className="not-italic">Fleet Payments</span>
          </h2>
          <p className="text-lg text-emerald-100/80 mb-8">
            Stop losing money to unverified claims. Start verifying every expense on WhatsApp today.
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full
              bg-white hover:bg-slate-50 text-emerald-700 font-bold
              transition-all duration-200 hover:shadow-xl hover:shadow-emerald-900/30
              text-base"
            id="cta-btn"
          >
            <Mail className="w-5 h-5" />
            Book Free Demo
          </Link>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="bg-slate-900 text-slate-400 py-16 px-6" id="about">
        <div className="max-w-7xl mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold">
                <span className="text-white">Fleet </span>
                <span className="text-emerald-400">Guard</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed">
              AI-powered expense verification for fleet owners. Built on WhatsApp. No apps needed.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">Product</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Live Demo</Link></li>
              <li><a href="#demo" className="hover:text-white transition-colors">Book Demo</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">Company</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="#about" className="hover:text-white transition-colors">About</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Testimonials</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-widest mb-4">Contact</h4>
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
          <p className="text-xs text-slate-600">© 2026 FleetGuard. All rights reserved.</p>
          <div className="flex items-center gap-3">
            <Truck className="w-5 h-5 text-slate-700" />
            <BarChart3 className="w-5 h-5 text-slate-700" />
          </div>
        </div>
      </footer>
    </div>
  );
}
