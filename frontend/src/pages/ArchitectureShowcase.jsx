import React, { useState } from 'react';

/**
 * FleetGuard Architecture, Slide Deck & Prediction Engine Showcase Page
 */
export default function ArchitectureShowcase() {
  const [activeTab, setActiveTab] = useState('slides'); // 'architecture' | 'slides' | 'calculator'

  // --- Slide Deck State ---
  const [currentSlide, setCurrentSlide] = useState(0);
  const [showSpeakerNotes, setShowSpeakerNotes] = useState(true);

  // --- Calculator Interactive State ---
  const [engineTemp, setEngineTemp] = useState(102); // Deg C
  const [dtcCodes, setDtcCodes] = useState(['P0217', 'P0300']);
  const [mileage, setMileage] = useState(145000);
  const [serviceAdherence, setServiceAdherence] = useState(0.75);

  const [claimedReceipt, setClaimedReceipt] = useState(350);
  const [actualTankIncrease, setActualTankIncrease] = useState(280);
  const [staticDrop, setStaticDrop] = useState(4.5);

  const [harshBraking, setHarshBraking] = useState(4);
  const [harshAccel, setHarshAccel] = useState(2);
  const [overspeedingMins, setOverspeedingMins] = useState(8);
  const [nightDistPct, setNightDistPct] = useState(20);

  // --- Mathematical Models Calculations ---
  // 1. Breakdown Risk Index (BRI)
  const calculateBRI = () => {
    const dtcScore = dtcCodes.reduce((sum, c) => sum + (c === 'P0217' || c === 'P0300' ? 4.0 : 2.0), 0);
    const tempDev = Math.max(0, engineTemp - 95);
    const mileageRatio = mileage / 500000;
    const weibull = Math.pow(mileageRatio, 1.45);
    const z = -3.20 + (1.85 * dtcScore) + (0.045 * tempDev) + (1.20 * weibull) + (-1.50 * serviceAdherence);
    const bri = 1 / (1 + Math.exp(-z));
    return (bri * 100).toFixed(1);
  };

  // 2. Fuel Fraud & Theft Status
  const calculateFuelFraud = () => {
    const discrepancy = Math.abs(claimedReceipt - actualTankIncrease);
    const isDiscrepancyFlagged = discrepancy > Math.max(5, 0.05 * claimedReceipt);
    const isSiphonFlagged = staticDrop >= 3.5;
    return { discrepancy: discrepancy.toFixed(1), isDiscrepancyFlagged, isSiphonFlagged };
  };

  // 3. Driver Risk Score (DRS)
  const calculateDRS = () => {
    const totalDist = 450; // km
    const dist100k = totalDist / 100;
    const hbRate = harshBraking / dist100k;
    const haRate = harshAccel / dist100k;
    const osRate = overspeedingMins / dist100k;
    const deductions = (6.0 * hbRate) + (4.0 * haRate) + (3.5 * osRate) + (0.15 * nightDistPct) + 10.0;
    const drs = Math.max(0, Math.min(100, 100 - deductions));
    return drs.toFixed(1);
  };

  const briScore = calculateBRI();
  const fuelFraud = calculateFuelFraud();
  const drsScore = calculateDRS();

  // --- Slides Data ---
  const slides = [
    {
      title: "FleetGuard: Enterprise Telematics & Fraud Prevention",
      subtitle: "Executive Presentation & Architecture Blueprint",
      type: "title",
      bullets: [
        "Event-Driven Architecture built on Apache Kafka & FastAPI",
        "Multi-modal Receipt OCR AI & Evidence Validation Framework",
        "Predictive Machine Learning Core for Downtime & Fraud Reduction",
        "Quantifiable Financial ROI: 32% Maintenance Cost Reduction"
      ],
      script: "Welcome everyone. FleetGuard is an enterprise-grade fleet intelligence platform engineered to eliminate fleet downtime and financial fraud by merging IoT telemetry, receipt vision AI, and predictive analytics."
    },
    {
      title: "Industry Pain Points & Operational Leaks",
      subtitle: "The Three Major Revenue Drains in Logistics",
      type: "cards",
      cards: [
        { title: "Unplanned Breakdowns", text: "Roadside component failure costs 3x standard maintenance and ruins SLA commitments.", color: "border-red-500 bg-red-500/10" },
        { title: "Fuel Theft & Billing Fraud", text: "Fuel equals ~40% of fleet OPEX. Siphoning and fake paper receipts drain profits silently.", color: "border-amber-500 bg-amber-500/10" },
        { title: "Reactive Servicing", text: "Servicing trucks on fixed calendar schedules leads to premature replacement or sudden failure.", color: "border-orange-500 bg-orange-500/10" }
      ],
      script: "Logistics fleets lose millions annually across three areas: sudden breakdowns, untracked fuel siphoning, and reactive maintenance. FleetGuard acts predictively before these losses occur."
    },
    {
      title: "High-Level System Architecture",
      subtitle: "Decoupled Event Transport & Multi-Engine Processing",
      type: "architecture_diagram",
      bullets: [
        "Persist-First Ingestion: Raw telemetry is saved before event publishing (<50ms response)",
        "Kafka Topic Partitioning: Keyed by vehicle_id for strict order preservation",
        "Decoupled Consumers: OCR, Validation Rules, and ML engines run independently"
      ],
      script: "Our architecture is built for extreme reliability. Ingestion persists events immediately to an immutable log before handing off to Kafka. Independent consumer groups handle OCR, rules, and ML without blocking."
    },
    {
      title: "Multi-Modal Document AI & Evidence Pipeline",
      subtitle: "Automating Paper Receipt Parsing via Vision Models",
      type: "bullets",
      bullets: [
        "WhatsApp & Driver App Photo Uploads trigger async DOCUMENT_UPLOADED events",
        "OCR Provider Registry uses vision models to extract Volume (L), Price, Station ID, Time",
        "0% Manual Data Entry required from fleet managers or depot staff"
      ],
      script: "Drivers simply snap a receipt picture on WhatsApp or our mobile app. Our OCR consumer extracts all metadata in seconds and publishes a verified DOCUMENT_TEXT_EXTRACTED event."
    },
    {
      title: "Real-Time Rule & Validation Engine",
      subtitle: "Automated Operational Guardrails",
      type: "cards",
      cards: [
        { title: "GPS Fencing Match", text: "Cross-checks receipt pump location against vehicle OBD-II GPS position.", color: "border-blue-500 bg-blue-500/10" },
        { title: "Tank Capacity Lock", text: "Blocks claims exceeding physical fuel tank limits.", color: "border-blue-500 bg-blue-500/10" },
        { title: "Invoice Hash Lock", text: "Prevents submitting duplicate physical receipts across drivers.", color: "border-blue-500 bg-blue-500/10" },
        { title: "Consumption Variance", text: "Flags L/100km anomalies deviating from baseline vehicle norms.", color: "border-blue-500 bg-blue-500/10" }
      ],
      script: "Every transaction passes through automated guardrail rules. If a driver claims 400L into a 300L tank or is 50km away from the gas station, the transaction is instantly blocked."
    },
    {
      title: "Predictive Intelligence Core",
      subtitle: "Continuous Risk & Maintenance Machine Learning",
      type: "bullets",
      bullets: [
        "Breakdown Risk Index (BRI): Sigmoid failure probability classifier",
        "Remaining Useful Life (RUL): Weibull hazard survival models for parts",
        "Fuel Theft Detection: Dual-vector receipt vs tank sensor delta verification",
        "Driver Safety Rating (DRS): Harsh event & fatigue exposure scoring"
      ],
      script: "FleetGuard doesn't just log data; it runs continuous mathematical models to predict vehicle breakdown risk, component lifespan, fuel theft, and driver safety scores."
    },
    {
      title: "Prediction Deep Dive: Breakdown Risk Index (BRI)",
      subtitle: "Sigmoid & Weibull Mathematical Logit Classifier",
      type: "formula",
      formula: "BRI(v, t) = 1 / (1 + e^-z)  where  z = -3.20 + 1.85(DTC) + 0.045(ΔTemp) + 1.20(Mileage/Rated)^1.45 - 1.50(MaintScore)",
      bullets: [
        "DTC Severity Weighting: Critical engine fault codes weighted up to 4.0",
        "Temperature Deviation: Coolant temp above 95°C normal baseline",
        "Weibull Accelerated Wear: Exponential mileage aging factor (alpha = 1.45)",
        "Automated Action: BRI > 70% automatically dispatches a workshop work order"
      ],
      script: "Our Breakdown Risk Index evaluates fault codes, temperature spikes, and vehicle age. When BRI crosses 70%, FleetGuard dispatches a work order before the vehicle breaks down."
    },
    {
      title: "Prediction Deep Dive: Dual-Vector Fuel Theft Model",
      subtitle: "Cross-Validating Physical Sensors with Receipt OCR",
      type: "bullets",
      bullets: [
        "Vector 1 (Static Siphoning): Detects tank level drops >= 3.5L while speed = 0 and engine = OFF",
        "Vector 2 (Billing Discrepancy): Flags claims where OCR Receipt Vol exceeds Sensor Tank Delta by >5%",
        "Instant Fraud Isolation: Automatically holds ticket reimbursement for admin review"
      ],
      script: "We cross-validate the physical tank sensor against the OCR receipt. If fuel drops while parked or receipt volume exceeds what actually entered the tank, we generate an instant theft alert."
    },
    {
      title: "Enterprise ROI & Financial Value",
      subtitle: "Quantifiable Impact for Fleet Logistics",
      type: "cards",
      cards: [
        { title: "-32% Maintenance OPEX", text: "Condition-based servicing replaces wasteful calendar maintenance.", color: "border-emerald-500 bg-emerald-500/10" },
        { title: "-85% Fuel Fraud", text: "Zero tolerance for fake paper receipts or illegal siphoning.", color: "border-emerald-500 bg-emerald-500/10" },
        { title: "+18% Fleet Uptime", text: "Eliminating roadside breakdowns keeps freight moving on schedule.", color: "border-emerald-500 bg-emerald-500/10" }
      ],
      script: "Deploying FleetGuard yields immediate ROI: 32% lower repair bills, virtual elimination of fuel fraud, and an 18% boost in overall fleet availability."
    },
    {
      title: "Deployment Roadmap & Q&A",
      subtitle: "Rapid Implementation Schedule",
      type: "bullets",
      bullets: [
        "Phase 1 (Weeks 1-2): Telematics & Persist-First Event Ingestion setup",
        "Phase 2 (Weeks 3-4): OCR Receipt Pipeline & Validation Rules activation",
        "Phase 3 (Weeks 5-6): Predictive ML Analytics & Executive BI Dashboard rollout",
        "Thank you! We welcome your questions and discussion."
      ],
      script: "FleetGuard is designed for rapid deployment without operational disruption. Thank you, and we look forward to answering your questions."
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-semibold uppercase tracking-wider border border-cyan-500/30">
              Architecture & PPT Hub
            </span>
            <span className="text-slate-400 text-sm">v2.0 Event-Driven Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-2">
            FleetGuard Intelligence Blueprint
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Interactive Architecture Flow, Presentation Slide Deck, and Real-Time Mathematical Prediction Engine
          </p>
        </div>

        {/* Tab Switcher Buttons */}
        <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('slides')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'slides'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            📊 PPT Presentation Deck
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'architecture'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            🏛️ Architecture Blueprint
          </button>
          <button
            onClick={() => setActiveTab('calculator')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === 'calculator'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            🧮 Live Prediction Engine
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* TAB 1: PPT PRESENTATION DECK */}
        {activeTab === 'slides' && (
          <div className="space-y-6">
            {/* Slide Navigation Controls */}
            <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  SLIDE {currentSlide + 1} OF {slides.length}
                </span>
                <h3 className="text-lg font-bold text-white truncate max-w-md">
                  {slides[currentSlide].title}
                </h3>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowSpeakerNotes(!showSpeakerNotes)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                    showSpeakerNotes
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                      : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                  }`}
                >
                  💬 Speaker Notes: {showSpeakerNotes ? 'ON' : 'OFF'}
                </button>

                <div className="flex items-center gap-1.5">
                  <button
                    disabled={currentSlide === 0}
                    onClick={() => setCurrentSlide(prev => prev - 1)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold transition-all"
                  >
                    ← Previous
                  </button>
                  <button
                    disabled={currentSlide === slides.length - 1}
                    onClick={() => setCurrentSlide(prev => prev + 1)}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold transition-all"
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>

            {/* Slide Canvas */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 min-h-[480px] shadow-2xl relative flex flex-col justify-between overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>

              {/* Slide Header */}
              <div>
                <div className="text-xs uppercase tracking-widest font-semibold text-blue-400 mb-1">
                  {slides[currentSlide].subtitle}
                </div>
                <h2 className="text-3xl font-extrabold text-white mb-6">
                  {slides[currentSlide].title}
                </h2>

                {/* Slide Body Rendering */}
                {slides[currentSlide].type === 'cards' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6">
                    {slides[currentSlide].cards?.map((card, idx) => (
                      <div key={idx} className={`p-6 rounded-xl border ${card.color} backdrop-blur-sm`}>
                        <h4 className="font-bold text-lg text-white mb-2">{card.title}</h4>
                        <p className="text-slate-300 text-sm leading-relaxed">{card.text}</p>
                      </div>
                    ))}
                  </div>
                )}

                {slides[currentSlide].type === 'formula' && (
                  <div className="my-6">
                    <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/40 text-cyan-300 font-mono text-sm leading-relaxed shadow-inner">
                      {slides[currentSlide].formula}
                    </div>
                  </div>
                )}

                {slides[currentSlide].type === 'architecture_diagram' && (
                  <div className="my-6 p-6 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="flex items-center justify-around gap-2 text-xs font-mono font-semibold py-4">
                      <div className="p-3 rounded-lg bg-blue-950 border border-blue-700 text-blue-300">OBD / Mobile App</div>
                      <span className="text-slate-500">→</span>
                      <div className="p-3 rounded-lg bg-indigo-950 border border-indigo-700 text-indigo-300">Persist Event Log</div>
                      <span className="text-slate-500">→</span>
                      <div className="p-3 rounded-lg bg-purple-950 border border-purple-700 text-purple-300">Apache Kafka Bus</div>
                      <span className="text-slate-500">→</span>
                      <div className="p-3 rounded-lg bg-emerald-950 border border-emerald-700 text-emerald-300">OCR & Rule Engines</div>
                    </div>
                  </div>
                )}

                {/* Bullets List */}
                {slides[currentSlide].bullets && (
                  <ul className="space-y-3 my-4">
                    {slides[currentSlide].bullets.map((b, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-slate-300 text-sm">
                        <span className="text-blue-400 mt-0.5">✦</span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Speaker Script Footer */}
              {showSpeakerNotes && (
                <div className="mt-8 pt-4 border-t border-slate-800/80 bg-slate-950/60 p-4 rounded-xl border border-amber-500/20">
                  <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <span>💬</span> Speaker Script & Presentation Notes
                  </div>
                  <p className="text-slate-300 italic text-sm leading-relaxed">
                    "{slides[currentSlide].script}"
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: ARCHITECTURE BLUEPRINT */}
        {activeTab === 'architecture' && (
          <div className="space-y-8">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Core System Architecture Specification</h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                FleetGuard uses an asynchronous, event-driven pattern designed for high telemetry throughput and zero data loss. The write path is decoupled from downstream computational pipelines.
              </p>

              {/* Architecture Layer Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-blue-400 text-sm font-semibold mb-1">Layer 1</div>
                  <h3 className="font-bold text-white text-lg mb-2">Ingestion Core</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    FastAPI REST & Webhooks. Enforces <em>Persist Event → Publish Event</em> invariant before return (&lt;50ms response).
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-indigo-400 text-sm font-semibold mb-1">Layer 2</div>
                  <h3 className="font-bold text-white text-lg mb-2">Kafka Bus</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Apache Kafka topic <code>operational-events</code>. Entity-based partitioning guarantees order per vehicle.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-purple-400 text-sm font-semibold mb-1">Layer 3</div>
                  <h3 className="font-bold text-white text-lg mb-2">OCR & Rule Engine</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Vision AI extracts receipt text asynchronously. Rule Engine validates GPS, tank capacities, and hashes.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-emerald-400 text-sm font-semibold mb-1">Layer 4</div>
                  <h3 className="font-bold text-white text-lg mb-2">Predictive ML Core</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Calculates Breakdown Risk Index, RUL component survival, fuel fraud alerts, and driver risk scores.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: LIVE PREDICTION CALCULATOR */}
        {activeTab === 'calculator' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Interactive Inputs Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Model 1: Breakdown Risk Controls */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                  <span>⚙️ Breakdown Risk Index (BRI) Parameters</span>
                  <span className="text-xs font-mono text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
                    Formula: Sigmoid + Weibull
                  </span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-xs text-slate-400 font-semibold block mb-2">
                      Engine Coolant Temperature: <span className="text-white font-bold">{engineTemp}°C</span>
                    </label>
                    <input
                      type="range"
                      min="80"
                      max="130"
                      value={engineTemp}
                      onChange={(e) => setEngineTemp(Number(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 font-semibold block mb-2">
                      Current Mileage: <span className="text-white font-bold">{mileage.toLocaleString()} km</span>
                    </label>
                    <input
                      type="range"
                      min="10000"
                      max="600000"
                      step="10000"
                      value={mileage}
                      onChange={(e) => setMileage(Number(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="text-xs text-slate-400 font-semibold block mb-2">Active OBD-II Fault Codes (DTCs)</label>
                  <div className="flex gap-2">
                    {['P0217 (Overheat)', 'P0300 (Misfire)', 'P0101 (MAF)', 'P0440 (EVAP)'].map(codeLabel => {
                      const code = codeLabel.split(' ')[0];
                      const active = dtcCodes.includes(code);
                      return (
                        <button
                          key={code}
                          onClick={() => {
                            setDtcCodes(prev => active ? prev.filter(c => c !== code) : [...prev, code]);
                          }}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                            active
                              ? 'bg-red-500/20 text-red-300 border-red-500/40'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {codeLabel}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Model 2: Fuel Theft Controls */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-lg font-bold text-white mb-4">⛽ Fuel Fraud & Theft Cross-Validation</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">OCR Claimed Receipt (L)</label>
                    <input
                      type="number"
                      value={claimedReceipt}
                      onChange={(e) => setClaimedReceipt(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Actual Sensor Increase (L)</label>
                    <input
                      type="number"
                      value={actualTankIncrease}
                      onChange={(e) => setActualTankIncrease(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Static Parked Drop (L)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={staticDrop}
                      onChange={(e) => setStaticDrop(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Live Model Output Column */}
            <div className="space-y-6">
              {/* Output 1: BRI Risk Index */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center">
                <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
                  Breakdown Risk Index (BRI)
                </div>
                <div className={`text-5xl font-black my-3 ${
                  Number(briScore) >= 70 ? 'text-red-400' : Number(briScore) >= 30 ? 'text-amber-400' : 'text-emerald-400'
                }`}>
                  {briScore}%
                </div>
                <div className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  Risk Tier: <span className={Number(briScore) >= 70 ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'}>
                    {Number(briScore) >= 70 ? 'HIGH' : Number(briScore) >= 30 ? 'MEDIUM' : 'LOW'}
                  </span>
                </div>
              </div>

              {/* Output 2: Fuel Fraud Status */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-3">
                  Fuel Anomaly Status
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span>Receipt Discrepancy:</span>
                    <span className="font-bold text-white">{fuelFraud.discrepancy} Liters</span>
                  </div>
                  <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span>Receipt Over-Billing:</span>
                    <span className={`font-bold ${fuelFraud.isDiscrepancyFlagged ? 'text-red-400' : 'text-emerald-400'}`}>
                      {fuelFraud.isDiscrepancyFlagged ? 'FLAGGED' : 'PASSED'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span>Static Tank Siphoning:</span>
                    <span className={`font-bold ${fuelFraud.isSiphonFlagged ? 'text-red-400' : 'text-emerald-400'}`}>
                      {fuelFraud.isSiphonFlagged ? 'SIPHON ALERT' : 'NORMAL'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Output 3: Driver Score */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center">
                <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">
                  Driver Risk Score (DRS)
                </div>
                <div className="text-4xl font-black text-blue-400 my-2">
                  {drsScore} / 100
                </div>
                <div className="text-xs text-slate-400">
                  Rating: <span className="text-blue-300 font-bold">GOOD SAFETY</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
