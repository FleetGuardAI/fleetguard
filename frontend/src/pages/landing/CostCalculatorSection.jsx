import React, { useState } from 'react';
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
  const totalHoursPerMonth = peopleManaging * hoursPerDay * workingDaysPerMonth;
  const totalCostPerMonth = totalHoursPerMonth * avgHourlyCost;

  return (
    <section className="py-24 bg-[#EAF5F0] text-content relative border-y border-fg-green/20">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 lg:gap-8 items-stretch">
          
          {/* Left Column: Text Content */}
          <div className="flex flex-col justify-center space-y-6 lg:pr-8">
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

          {/* Middle Column: Calculator Inputs */}
          <div className="flex flex-col justify-center bg-white/50 backdrop-blur-sm border border-fg-green/20 rounded-2xl p-8 shadow-sm">
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

          {/* Right Column: Output Card */}
          <div className="bg-fg-dark text-white rounded-2xl p-8 flex flex-col justify-between shadow-xl relative overflow-hidden">
            {/* Subtle background element */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-fg-green/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4 pointer-events-none"></div>

            <div className="relative z-10">
              <div className="text-xs font-semibold text-white/70 uppercase tracking-widest mb-6">
                Estimated manual cost
              </div>
              
              <div className="mb-4">
                <div className="text-3xl font-medium tracking-tight mb-2">
                  ~{totalHoursPerMonth.toLocaleString('en-IN')} hours/month
                </div>
                <div className="flex items-center gap-2 text-fg-green font-bold text-3xl">
                  = ₹ {totalCostPerMonth.toLocaleString('en-IN')} / month
                  <div className="group relative">
                    <Info className="w-5 h-5 text-fg-green/50 hover:text-fg-green cursor-pointer" />
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-white text-content text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                      Calculated using an illustrative estimate of ₹{avgHourlyCost}/hour for administrative staff.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative z-10 mt-12 text-sm text-white/70 font-light leading-relaxed">
              That's time your team could spend on decisions instead of spreadsheets.
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}

function SliderInput({ label, value, min, max, onChange, suffix }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <label className="text-sm font-medium text-content-secondary">{label}</label>
        <span className="text-sm font-bold text-content flex gap-1">
          {value.toLocaleString('en-IN')} <span className="font-normal text-content-muted">{suffix}</span>
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-fg-green/20 rounded-lg appearance-none cursor-pointer accent-fg-green focus:outline-none focus:ring-2 focus:ring-fg-green/50"
      />
    </div>
  );
}
