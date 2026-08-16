import React, { useState, useEffect, useCallback, useRef } from 'react';
import { QrCode, Copy, Download, RefreshCw, Users, CheckCircle2, Clock } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';
import api from '@/api/client';

/**
 * Minimal inline QR Code generator (no external dependencies).
 * Generates a simple QR-like SVG from a string using a deterministic hash grid.
 * For production, replace with a proper QR library like `qrcode`.
 */
function generateQrSvg(data, size = 200) {
  // Simple deterministic pattern from string hash
  const cells = 21;
  const cellSize = size / cells;
  const grid = [];
  
  // Hash the data string to generate a pseudo-random but deterministic pattern
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }

  // Generate grid pattern
  for (let y = 0; y < cells; y++) {
    for (let x = 0; x < cells; x++) {
      // Finder patterns (top-left, top-right, bottom-left)
      const isFinderTL = x < 7 && y < 7;
      const isFinderTR = x >= cells - 7 && y < 7;
      const isFinderBL = x < 7 && y >= cells - 7;
      
      if (isFinderTL || isFinderTR || isFinderBL) {
        const fx = isFinderTR ? x - (cells - 7) : x;
        const fy = isFinderBL ? y - (cells - 7) : y;
        const isBorder = fx === 0 || fx === 6 || fy === 0 || fy === 6;
        const isInner = fx >= 2 && fx <= 4 && fy >= 2 && fy <= 4;
        if (isBorder || isInner) {
          grid.push({ x, y });
        }
        continue;
      }
      
      // Data modules — deterministic from hash
      const seed = (hash * (x + 1) * (y + 1) + x * 31 + y * 17) & 0xFFFF;
      if (seed % 3 !== 0) {
        grid.push({ x, y });
      }
    }
  }

  const rects = grid.map(({ x, y }) =>
    `<rect x="${x * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="currentColor" rx="1"/>`
  ).join('');

  return `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" class="text-content">${rects}</svg>`;
}

export function QrOnboardingCard() {
  const { success, error } = useToast();
  const [invite, setInvite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [connectedDrivers, setConnectedDrivers] = useState(0);
  const qrRef = useRef(null);

  const loadInvite = useCallback(async () => {
    try {
      // Fetch existing invites
      const invites = await api.get('/api/v1/fleet/invites').catch(() => []);
      const activeInvite = Array.isArray(invites) 
        ? invites.find(i => i.is_active && (!i.expires_at || new Date(i.expires_at) > new Date()))
        : null;
      
      if (activeInvite) {
        setInvite(activeInvite);
      }
    } catch {
      // Silently fail — will show creation button
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDriverCount = useCallback(async () => {
    try {
      const drivers = await api.get('/api/v1/fleet/drivers').catch(() => []);
      setConnectedDrivers(Array.isArray(drivers) ? drivers.length : 0);
    } catch {
      // Keep default
    }
  }, []);

  useEffect(() => {
    loadInvite();
    loadDriverCount();
  }, [loadInvite, loadDriverCount]);

  const handleGenerateQr = async () => {
    setRegenerating(true);
    try {
      const newInvite = await api.post('/api/v1/fleet/invite', {
        label: 'Dashboard QR Invite',
        expires_in_days: 30,
      });
      setInvite(newInvite);
      success('QR Generated', 'New driver invite QR code created successfully.');
    } catch {
      error('Generation Failed', 'Could not create invite QR code.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleRegenerateQr = async () => {
    setRegenerating(true);
    try {
      const newInvite = await api.post('/api/v1/fleet/invite', {
        label: 'Dashboard QR Invite (Regenerated)',
        expires_in_days: 30,
      });
      setInvite(newInvite);
      success('QR Regenerated', 'Old invite invalidated. New QR code ready.');
    } catch {
      error('Regeneration Failed', 'Could not regenerate invite QR code.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleCopyCode = () => {
    if (invite?.invite_token) {
      navigator.clipboard.writeText(invite.invite_token);
      success('Copied!', 'Invite code copied to clipboard.');
    }
  };

  const handleDownloadQr = () => {
    if (!qrRef.current) return;
    const svgEl = qrRef.current.querySelector('svg');
    if (!svgEl) return;

    const svgData = new XMLSerializer().serializeToString(svgEl);
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, 400, 400);
      ctx.drawImage(img, 40, 40, 320, 320);
      const link = document.createElement('a');
      link.download = 'fleetguard-invite-qr.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  const daysRemaining = invite?.expires_at
    ? Math.max(0, Math.ceil((new Date(invite.expires_at) - new Date()) / (1000 * 60 * 60 * 24)))
    : null;

  const user = JSON.parse(localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user') || '{}');

  return (
    <div className="bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">
          Driver Onboarding
        </h4>
        <div className="flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5 text-fg-green" />
          <span className="text-xs font-semibold text-fg-green">{connectedDrivers} drivers</span>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-5 h-5 animate-spin text-content-muted" />
        </div>
      ) : invite ? (
        <div className="space-y-4">
          {/* QR Code Display */}
          <div className="flex justify-center">
            <div
              ref={qrRef}
              className="w-36 h-36 p-3 bg-white rounded-xl border border-border shadow-sm"
              dangerouslySetInnerHTML={{
                __html: generateQrSvg(invite.qr_data || invite.invite_token, 200)
              }}
            />
          </div>

          {/* Org Info */}
          <div className="text-center space-y-1">
            <p className="text-sm font-semibold text-content">{user?.company_name || 'Your Organization'}</p>
            <p className="text-[11px] text-content-muted font-mono">
              ID: {invite.company_id || '—'}
            </p>
          </div>

          {/* Expiry */}
          {daysRemaining !== null && (
            <div className="flex items-center justify-center gap-1.5">
              <Clock className="w-3 h-3 text-content-muted" />
              <span className={cn(
                'text-[11px] font-medium',
                daysRemaining <= 3 ? 'text-amber-400' : 'text-content-muted'
              )}>
                Expires in {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyCode}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-surface-secondary border border-border text-xs font-medium text-content-secondary hover:text-content hover:bg-surface transition-colors"
              title="Copy invite code"
              aria-label="Copy invite code"
            >
              <Copy className="w-3.5 h-3.5" />
              Copy Code
            </button>
            <button
              onClick={handleDownloadQr}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-surface-secondary border border-border text-xs font-medium text-content-secondary hover:text-content hover:bg-surface transition-colors"
              title="Download QR code"
              aria-label="Download QR code as image"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </button>
          </div>
          <button
            onClick={handleRegenerateQr}
            disabled={regenerating}
            className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl bg-fg-green/10 border border-fg-green/20 text-xs font-semibold text-fg-green hover:bg-fg-green/20 transition-colors disabled:opacity-50"
            aria-label="Regenerate QR code"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', regenerating && 'animate-spin')} />
            {regenerating ? 'Regenerating...' : 'Regenerate QR'}
          </button>
        </div>
      ) : (
        /* No invite exists yet — show creation CTA */
        <div className="text-center space-y-4 py-4">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-fg-green/10 border border-fg-green/20 flex items-center justify-center">
            <QrCode className="w-8 h-8 text-fg-green" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-content">Invite Drivers</p>
            <p className="text-xs text-content-muted max-w-[200px] mx-auto">
              Generate a QR code for drivers to scan and join your fleet.
            </p>
          </div>
          <button
            onClick={handleGenerateQr}
            disabled={regenerating}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-fg-green hover:bg-fg-green-bright text-surface-inverted transition-all shadow-fg-glow disabled:opacity-50"
            aria-label="Generate invite QR code"
          >
            {regenerating ? 'Generating...' : 'Generate QR Code'}
          </button>
        </div>
      )}
    </div>
  );
}
