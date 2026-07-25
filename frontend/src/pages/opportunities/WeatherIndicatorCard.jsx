import { useEffect, useMemo, useState } from 'react';
import { CloudSun, MapPin, Navigation, RefreshCw, Thermometer, Wind } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const HOT_THRESHOLD_C = 35;


export function WeatherIndicatorCard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadWeather(latitude, longitude) {
      try {
        const apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY || 'bff43ba2abb39745eaad7a703ba34259';
        const weatherUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&appid=${apiKey}&units=metric`;
        const forecastUrl = `https://api.openweathermap.org/data/2.5/forecast?lat=${latitude}&lon=${longitude}&appid=${apiKey}&units=metric`;

        let weatherRes, forecastRes;
        try {
          weatherRes = await fetch(weatherUrl);
          forecastRes = await fetch(forecastUrl);
        } catch (e) {
          console.warn('Weather fetch error:', e);
        }

        if (cancelled) return;

        let weatherData, forecastData;
        if (weatherRes && weatherRes.ok) {
          weatherData = await weatherRes.json();
          forecastData = forecastRes && forecastRes.ok ? await forecastRes.json() : null;
        } else {
          setError('Live weather service unavailable.');
          setLoading(false);
          return;
        }

        const city = weatherData.name || 'Current location';
        const currentTemp = weatherData.main?.temp || 0;
        const condition = weatherData.weather?.[0]?.description || 'moderate weather';
        const windSpeed = (weatherData.wind?.speed || 0) * 3.6; // m/s to km/h

        let hotDaysAhead = 0;
        let firstHotDayOffset = 0;

        if (forecastData && forecastData.list) {
          const days = {};
          const today = new Date().toISOString().split('T')[0];

          forecastData.list.forEach(item => {
            const dateStr = item.dt_txt.split(' ')[0];
            if (dateStr !== today) {
              if (!days[dateStr]) days[dateStr] = [];
              days[dateStr].push(item.main.temp);
            }
          });

          const futureDays = Object.keys(days).sort();
          futureDays.forEach((day, index) => {
             const maxTemp = Math.max(...days[day]);
             if (maxTemp >= HOT_THRESHOLD_C) {
                hotDaysAhead++;
                if (firstHotDayOffset === 0) firstHotDayOffset = index + 1;
             }
          });
        }
        
        setWeather({
          city,
          latitude,
          longitude,
          currentTemp,
          condition: condition.charAt(0).toUpperCase() + condition.slice(1),
          windSpeed,
          hotDaysAhead,
          firstHotDayOffset,
        });
        setError('');
      } catch (err) {
        setError(err.message || 'Unable to load weather right now.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (!navigator.geolocation) {
      setError('Geolocation is not supported in this browser.');
      setLoading(false);
      return () => {
        cancelled = true;
      };
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => loadWeather(pos.coords.latitude, pos.coords.longitude),
      () => {
        setError('Location permission is needed to show local weather.');
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      }
    );

    return () => {
      cancelled = true;
    };
  }, []);

  const summary = useMemo(() => {
    if (!weather) return '';

    if (weather.hotDaysAhead > 0) {
      let startText = 'soon';
      if (weather.firstHotDayOffset === 1) startText = 'starting tomorrow';
      else if (weather.firstHotDayOffset > 1) startText = `starting in ${weather.firstHotDayOffset} days`;

      return `Expect ${weather.hotDaysAhead} hot day${weather.hotDaysAhead > 1 ? 's' : ''} ahead, ${startText}.`;
    }

    return `Conditions look ${weather.condition.toLowerCase()} over the next few days.`;
  }, [weather]);

  const forecastLink = weather
    ? `https://www.google.com/search?q=weather+${weather.latitude},${weather.longitude}`
    : '#';

  return (
    <div className="rounded-[26px] border border-blue-200/40 bg-gradient-to-br from-[#4d72bd] via-[#597ec6] to-[#88a7db] p-5 text-white shadow-xl shadow-blue-900/20">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white/95">
          <Navigation className="h-4 w-4" />
          <span>{weather?.city || 'Local Weather'}</span>
        </div>
        <CloudSun className="h-5 w-5 text-white/90" />
      </div>

      {loading && (
        <div className="mt-4 flex items-center gap-2 text-sm text-white/90">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Fetching real-time weather...
        </div>
      )}

      {!loading && error && (
        <div className="mt-4 rounded-xl border border-white/20 bg-white/10 p-3 text-sm text-white/95">
          {error}
        </div>
      )}

      {!loading && !error && weather && (
        <>
          <div className="mt-4 flex items-end gap-3">
            <div className="text-5xl font-semibold leading-none">
              {Math.round(weather.currentTemp)}
              {'\u00B0'}C
            </div>
            <div className="pb-1 text-sm text-white/90">{weather.condition}</div>
          </div>

          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-white/90">
            <div className="flex items-center gap-1.5">
              <Thermometer className="h-3.5 w-3.5" />
              Hot threshold: {HOT_THRESHOLD_C}{'\u00B0'}C
            </div>
            <div className="flex items-center gap-1.5">
              <Wind className="h-3.5 w-3.5" />
              Wind: {Math.round(weather.windSpeed)} km/h
            </div>
            <div className="flex items-center gap-1.5 sm:col-span-2">
              <MapPin className="h-3.5 w-3.5" />
              Based on your current location
            </div>
          </div>

          <p className="mt-3 text-sm leading-snug text-white/95">{summary}</p>

          <div className="mt-4">
            <a href={forecastLink} target="_blank" rel="noreferrer">
              <Button
                type="button"
                size="sm"
                className="rounded-full bg-white/18 hover:bg-white/24 text-white border border-white/30"
              >
                See full forecast
              </Button>
            </a>
          </div>
        </>
      )}
    </div>
  );
}

export default WeatherIndicatorCard;
