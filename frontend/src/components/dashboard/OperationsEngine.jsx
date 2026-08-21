import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';
import { Loader } from '@/components/ui/Loader';
import { 
  AlertTriangle, 
  ChevronRight, 
  ChevronLeft, 
  Banknote,
  TrendingUp,
  Activity,
  Zap,
  Wrench,
  CreditCard,
  Info
} from 'lucide-react';
import api from '@/api/client';

const INSIGHT_ICONS = {
  revenue: Banknote,
  cashflow: TrendingUp,
  efficiency: Zap,
  performance: Activity,
  maintenance: Wrench,
  payment: CreditCard,
  default: Info
};

export function OperationsEngine() {
  const { t } = useLanguage();
  
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  
  const scrollContainerRef = useRef(null);

  const checkScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(Math.ceil(scrollLeft + clientWidth) < scrollWidth);
    }
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [insights]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Create a clean backend-ready interface
      let data;
      try {
        data = await api.operationsEngine.getInsights();
      } catch (backendErr) {
        // Fallback explicitly during development if endpoint doesn't exist (404)
        if (import.meta.env.DEV && backendErr.message && backendErr.message.includes('404')) {
          console.warn('Operations API not found (404). Using development fallback mock data.');
          data = {
            insights: [
              {
                id: '1',
                type: 'revenue',
                title: 'Revenue & Profit',
                primaryValue: '₹12.4L',
                secondaryValue: 'Net margin 18.2%',
                trend: '+8.4% this month',
                status: 'Healthy',
                description: ''
              },
              {
                id: '2',
                type: 'payment',
                title: 'Payment Risk',
                primaryValue: '₹4.8L',
                secondaryValue: '12 invoices overdue',
                trend: '',
                status: 'Needs attention',
                description: 'Outstanding receivables'
              },
              {
                id: '3',
                type: 'maintenance',
                title: 'Maintenance Risk',
                primaryValue: '3 Vehicles',
                secondaryValue: 'Requires immediate service',
                trend: '',
                status: 'Critical',
                description: 'Estimated ₹1.2L exposure'
              }
            ]
          };
        } else {
          throw backendErr; // Genuine network/CORS or other errors should be thrown
        }
      }
      
      setInsights(data?.insights || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = 350; // approx card width
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (loading) {
    return (
      <div className="w-full h-48 border border-border rounded-2xl bg-white flex flex-col p-6 shadow-sm">
        <div className="mb-4">
          <div className="h-6 bg-surface-secondary rounded w-48 animate-pulse mb-2"></div>
          <div className="h-4 bg-surface-secondary rounded w-64 animate-pulse"></div>
        </div>
        <div className="flex gap-4 overflow-hidden">
          {[1, 2, 3].map(i => (
            <div key={i} className="min-w-[300px] h-28 bg-surface-secondary rounded-xl animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-6 border border-red-200 rounded-2xl bg-red-50 flex flex-col justify-center shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h3 className="text-base font-semibold text-red-900">{t("Operations Engine unavailable")}</h3>
        </div>
        <p className="text-sm text-red-700 mb-4">{t("We couldn't retrieve the latest operational insights.")}</p>
        <div>
          <button 
            onClick={loadData}
            className="px-4 py-2 bg-white text-red-700 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
          >
            {t("Retry Analysis")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white border border-border shadow-sm rounded-2xl p-6 relative">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-semibold text-brand-700 flex items-center gap-2 tracking-tight">
            <Zap className="w-5 h-5 text-brand-500" />
            {t("Operations Engine")}
          </h2>
          <p className="text-sm text-content-secondary mt-0.5 font-light">
            {t("Live operational insights across your fleet.")}
          </p>
        </div>
        
        {insights.length > 1 && (
          <div className="flex items-center gap-2">
            <button 
              onClick={() => scroll('left')} 
              disabled={!canScrollLeft}
              className="p-1.5 rounded-full border border-border bg-surface-base text-content-secondary hover:bg-surface-secondary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button 
              onClick={() => scroll('right')} 
              disabled={!canScrollRight}
              className="p-1.5 rounded-full border border-border bg-surface-base text-content-secondary hover:bg-surface-secondary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {insights.length === 0 ? (
        <div className="w-full py-8 border border-dashed border-border rounded-xl bg-surface-tertiary flex flex-col items-center justify-center text-center">
          <Zap className="h-8 w-8 text-brand-400 mb-3 opacity-60" />
          <h3 className="text-base font-medium text-content">{t("Operations Engine is ready")}</h3>
          <p className="text-sm text-content-secondary mt-1">{t("Add trips, vehicles and financial activity to start generating operational insights.")}</p>
        </div>
      ) : (
        <div 
          ref={scrollContainerRef}
          onScroll={checkScroll}
          className="flex gap-4 overflow-x-auto snap-x snap-mandatory scrollbar-hide pb-2"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {insights.map((insight) => {
            const Icon = INSIGHT_ICONS[insight.type] || INSIGHT_ICONS.default;
            
            const isCritical = insight.status?.toLowerCase() === 'critical';
            const isAttention = insight.status?.toLowerCase().includes('attention');
            const isHealthy = insight.status?.toLowerCase() === 'healthy';
            
            return (
              <div 
                key={insight.id} 
                className="flex-none w-[280px] md:w-[320px] p-5 rounded-xl border border-border bg-surface-base hover:shadow-md transition-shadow snap-start flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-3 text-content-secondary">
                    <Icon className="w-4 h-4" />
                    <span className="text-xs font-semibold uppercase tracking-widest">{t(insight.title)}</span>
                  </div>
                  
                  <div className="mb-2">
                    <h4 className="text-2xl font-bold text-content tracking-tight">{insight.primaryValue}</h4>
                    {insight.description && (
                      <p className="text-xs text-content-secondary mt-1 uppercase tracking-wider font-medium">{t(insight.description)}</p>
                    )}
                  </div>
                  
                  {insight.secondaryValue && (
                    <p className="text-sm text-content-secondary font-light">{t(insight.secondaryValue)}</p>
                  )}
                </div>
                
                <div className="mt-4 pt-4 border-t border-border/60 flex items-center justify-between">
                  {insight.trend ? (
                    <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">{insight.trend}</span>
                  ) : <span></span>}
                  
                  {insight.status && (
                    <span className={cn(
                      "text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-md",
                      isCritical ? "text-red-700 bg-red-50" : 
                      isAttention ? "text-amber-700 bg-amber-50" : 
                      isHealthy ? "text-emerald-700 bg-emerald-50" : "text-brand-700 bg-brand-50"
                    )}>
                      {t(insight.status)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
