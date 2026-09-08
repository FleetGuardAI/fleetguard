import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Search, X, Loader2 } from 'lucide-react';
import { locationApi } from '@/api/locationApi';
import { cn } from '@/utils/cn';

export function LocationAutocomplete({ 
  value, 
  onChange, 
  placeholder = "Search location...",
  icon: Icon = MapPin,
  className
}) {
  const [query, setQuery] = useState(value?.description || '');
  const [predictions, setPredictions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionToken, setSessionToken] = useState(null);
  const wrapperRef = useRef(null);

  // Generate session token on mount or when previous session is consumed
  useEffect(() => {
    if (!sessionToken) {
      setSessionToken(Math.random().toString(36).substring(2) + Date.now().toString(36));
    }
  }, [sessionToken]);

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!query || query.length < 2) {
      setPredictions([]);
      setIsLoading(false);
      return;
    }

    if (value && query === value.description) {
      // Don't search if the query exactly matches the selected value
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const results = await locationApi.autocomplete(query, sessionToken);
        setPredictions(results || []);
        setIsOpen(true);
      } catch (error) {
        console.error("Autocomplete error:", error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, sessionToken, value]);

  const handleSelect = async (prediction) => {
    setQuery(prediction.description);
    setIsOpen(false);
    setIsLoading(true);
    
    try {
      const details = await locationApi.getPlaceDetails(prediction.place_id, sessionToken);
      onChange({
        place_id: prediction.place_id,
        description: prediction.description,
        address: details?.formatted_address || prediction.description,
        lat: details?.lat,
        lng: details?.lng
      });
      // Reset session token after a successful selection
      setSessionToken(null);
    } catch (error) {
      console.error("Place details error:", error);
      onChange({
        place_id: prediction.place_id,
        description: prediction.description
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setPredictions([]);
    onChange(null);
  };

  return (
    <div ref={wrapperRef} className={cn("relative w-full", className)}>
      <div className="relative flex items-center">
        <Icon className="absolute left-3 w-4 h-4 text-content-muted" />
        <input
          type="text"
          className="w-full h-11 pl-10 pr-10 bg-background-elevated border border-border rounded-xl text-content placeholder:text-content-muted focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all text-sm"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (predictions.length > 0) setIsOpen(true);
          }}
        />
        {isLoading ? (
          <Loader2 className="absolute right-3 w-4 h-4 text-content-muted animate-spin" />
        ) : query ? (
          <button 
            type="button" 
            onClick={handleClear}
            className="absolute right-3 p-1 rounded-full hover:bg-background transition-colors text-content-muted hover:text-content"
          >
            <X className="w-4 h-4" />
          </button>
        ) : null}
      </div>

      {isOpen && predictions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-background-elevated border border-border rounded-xl shadow-card overflow-hidden">
          <ul className="max-h-60 overflow-y-auto py-1">
            {predictions.map((p) => (
              <li 
                key={p.place_id}
                onClick={() => handleSelect(p)}
                className="px-4 py-2 hover:bg-background cursor-pointer flex flex-col transition-colors"
              >
                <span className="text-sm font-medium text-content">{p.main_text}</span>
                <span className="text-xs text-content-muted truncate">{p.secondary_text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
