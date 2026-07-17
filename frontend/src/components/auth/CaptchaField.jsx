import { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

function ensureRecaptchaScript(siteKey) {
  const src = `https://www.google.com/recaptcha/enterprise.js?render=${siteKey}`;
  const existing = document.querySelector(`script[src="${src}"]`);
  if (existing) return;

  const script = document.createElement('script');
  script.src = src;
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
}

export function CaptchaField({ value, onChange, error, label = 'Captcha', action = 'login' }) {
  const siteKey = import.meta.env.VITE_RECAPTCHA_ENTERPRISE_SITE_KEY || import.meta.env.VITE_TURNSTILE_SITE_KEY;
  const [sdkReady, setSdkReady] = useState(false);
  const [tokenLoading, setTokenLoading] = useState(false);

  useEffect(() => {
    if (!siteKey) return;

    ensureRecaptchaScript(siteKey);

    const timer = window.setInterval(() => {
      if (window.grecaptcha?.enterprise) {
        setSdkReady(true);
        window.clearInterval(timer);
      }
    }, 100);

    return () => window.clearInterval(timer);
  }, [siteKey]);

  const generateToken = async () => {
    if (!siteKey || !window.grecaptcha?.enterprise) return;

    setTokenLoading(true);
    try {
      const token = await new Promise((resolve, reject) => {
        window.grecaptcha.enterprise.ready(async () => {
          try {
            const generated = await window.grecaptcha.enterprise.execute(siteKey, { action });
            resolve(generated);
          } catch (err) {
            reject(err);
          }
        });
      });
      onChange(token);
    } catch {
      onChange('');
    } finally {
      setTokenLoading(false);
    }
  };

  if (!siteKey) {
    return (
      <Input
        label={label}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        error={error}
        placeholder="For local dev, enter: dev-captcha-pass"
        helperText="Set VITE_RECAPTCHA_ENTERPRISE_SITE_KEY for live token generation"
        required
      />
    );
  }

  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-content-secondary">{label}</label>
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={generateToken}
          disabled={!sdkReady}
          loading={tokenLoading}
          icon={<ShieldCheck className="h-4 w-4" />}
        >
          {value ? 'Refresh Captcha Token' : 'Generate Captcha Token'}
        </Button>
        {value && <p className="text-xs text-emerald-600">Token ready</p>}
      </div>
      {!sdkReady && (
        <p className="text-xs text-content-muted">Loading reCAPTCHA Enterprise SDK...</p>
      )}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
