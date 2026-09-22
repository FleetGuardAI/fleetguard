import React, { useState, useRef, useEffect } from 'react';
import { ArrowRight, Info } from 'lucide-react';

export function CostCalculatorSection() {
  const [fleetSize, setFleetSize] = useState(50);
  const [tripsPerMonth, setTripsPerMonth] = useState(400);
  const [peopleManaging, setPeopleManaging] = useState(3);
  const [hoursPerDay, setHoursPerDay] = useState(6);

  // Constants
  const workingDaysPerMonth = 26;
  const avgHourlyCost = 300; // Estimated ₹ per hour for admin staff

  // Calculations
  // Base staff hours from their manual input
  const baseStaffHours = peopleManaging * hoursPerDay * workingDaysPerMonth;
  
  // A scaling multiplier that demonstrates how overhead grows with fleet size and trip volume
  // For a small fleet (10 trucks, 50 trips), multiplier is small.
  // For a large fleet (500 trucks, 2000 trips), multiplier scales up significantly to show hidden costs.
  const scaleMultiplier = 1 + (fleetSize / 200) + (tripsPerMonth / 1000);
  
  const totalHoursPerMonth = Math.round(baseStaffHours * scaleMultiplier);
  const totalCostPerMonth = totalHoursPerMonth * avgHourlyCost;

  return (
    <section className="py-24 bg-[#EAF5F0] text-content relative border-y border-fg-green/20">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-start">
          
          {/* Left Column: Text Content (spans 3 cols) */}
          <div className="lg:col-span-3 flex flex-col justify-center space-y-6 lg:pr-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-[2px] bg-fg-green"></div>
              <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">The Hidden Cost</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-medium tracking-tight leading-[1.1]">
              Manual fleet management is expensive.
            </h2>
            
            <p className="text-lg text-content-secondary font-light leading-relaxed">
              Your team spends hours collecting, checking and connecting information. While they do that, issues go unnoticed and money leaks.
            </p>

            <div className="pt-2 flex items-center text-sm font-medium text-fg-green hover:text-fg-green-deep transition-colors cursor-pointer group w-max">
              See how costs add up
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Middle Column: Calculator Inputs (spans 5 cols) */}
          <div className="lg:col-span-5 flex flex-col justify-center bg-white/50 backdrop-blur-sm border border-fg-green/20 rounded-2xl p-8 shadow-sm">
            <h3 className="text-sm font-semibold text-content mb-8">Calculate your manual operations cost</h3>
            
            <div className="space-y-6">
              <SliderInput 
                label="Fleet size" 
                value={fleetSize} 
                min={10} max={500} 
                onChange={setFleetSize} 
                suffix="trucks" 
              />
              <SliderInput 
                label="Trips per month" 
                value={tripsPerMonth} 
                min={50} max={2000} 
                onChange={setTripsPerMonth} 
                suffix="trips" 
              />
              <SliderInput 
                label="People managing" 
                value={peopleManaging} 
                min={1} max={20} 
                onChange={setPeopleManaging} 
                suffix="people" 
              />
              <SliderInput 
                label="Hours per day" 
                value={hoursPerDay} 
                min={1} max={12} 
                onChange={setHoursPerDay} 
                suffix="hours" 
              />
            </div>
          </div>

          {/* Right Column: Redesigned Output Card (spans 4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-5">
            {/* Main cost card — smaller, tighter */}
            <div className="bg-fg-dark text-white rounded-2xl p-6 shadow-xl relative overflow-hidden">
              {/* Subtle background glow */}
              <div className="absolute top-0 right-0 w-40 h-40 bg-fg-green/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4 pointer-events-none"></div>

              <div className="relative z-10">
                <div className="text-[10px] font-semibold text-white/60 uppercase tracking-widest mb-4">
                  Estimated manual cost
                </div>
                
                <div className="mb-3">
                  <div className="text-2xl font-medium tracking-tight mb-1.5">
                    ~{totalHoursPerMonth.toLocaleString('en-IN')} hours/month
                  </div>
                  <div className="flex items-center gap-2 text-fg-green font-bold text-2xl">
                    = ₹ {totalCostPerMonth.toLocaleString('en-IN')} / month
                    <div className="group relative">
                      <Info className="w-4 h-4 text-fg-green/50 hover:text-fg-green cursor-pointer" />
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-white text-content text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                        Calculated using an illustrative estimate of ₹{avgHourlyCost}/hour for administrative staff.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-[13px] text-white/50 font-light leading-relaxed border-t border-white/10 pt-3">
                  Time spent coordinating trips, checking documents, following up with drivers and fixing avoidable issues.
                </div>
              </div>
            </div>

            {/* Green insight card */}
            <div className="bg-[#E8F5EE] border border-fg-green/15 rounded-xl p-4">
              <p className="text-[14px] font-medium text-fg-green leading-snug">
                That is {totalHoursPerMonth.toLocaleString('en-IN')} hours that could be spent running the business.
              </p>
            </div>

            {/* Supporting context */}
            <p className="text-[13px] text-content-secondary font-light leading-relaxed px-1">
              Every manual handoff adds another opportunity for information to get missed.
            </p>
          </div>

        </div>
      </div>
    </section>
  );
}

function SliderInput({ label, value, min, max, onChange, suffix }) {
  const sliderRef = useRef(null);

  // Update the CSS gradient to show green fill on the active portion (WebKit)
  useEffect(() => {
    if (sliderRef.current) {
      const pct = ((value - min) / (max - min)) * 100;
      sliderRef.current.style.background = `linear-gradient(to right, #1F5C42 0%, #1F5C42 ${pct}%, #E5EDE7 ${pct}%, #E5EDE7 100%)`;
    }
  }, [value, min, max]);

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <label className="text-sm font-medium text-content-secondary">{label}</label>
        <span className="text-sm font-bold text-content flex gap-1">
          {value.toLocaleString('en-IN')} <span className="font-normal text-content-muted">{suffix}</span>
        </span>
      </div>
      <input
        ref={sliderRef}
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full green-range focus:outline-none"
      />
    </div>
  );
}
