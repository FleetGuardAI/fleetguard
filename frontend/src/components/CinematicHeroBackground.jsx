import React, { useEffect, useRef, useCallback } from 'react';

/**
 * CinematicHeroBackground
 * 
 * A premium animated hero background that brings the static hero image
 * to life using canvas overlays and CSS animations. Designed to replicate
 * the feel of a cinematic 4K video background without requiring actual video.
 * 
 * Effects:
 * 1. Slow Ken Burns zoom (subtle 5% scale over 20s)
 * 2. Animated volumetric god rays from the sun position
 * 3. Drifting cloud shadows
 * 4. Floating atmospheric mist/fog particles
 * 5. Gentle light shimmer on the "water" area
 * 6. Subtle golden-hour color temperature shift
 */
export default function CinematicHeroBackground() {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const startTimeRef = useRef(null);

  const draw = useCallback((ctx, width, height, elapsed) => {
    ctx.clearRect(0, 0, width, height);

    // ——— 1. VOLUMETRIC GOD RAYS ———
    // Sun position (upper-left area of the image based on reference)
    const sunX = width * 0.28;
    const sunY = height * 0.18;

    // Pulsing ray intensity
    const rayPulse = 0.5 + Math.sin(elapsed * 0.0003) * 0.15;
    const rayRotation = elapsed * 0.00003; // Very slow rotation

    ctx.save();
    ctx.translate(sunX, sunY);
    ctx.rotate(rayRotation);

    const rayCount = 12;
    for (let i = 0; i < rayCount; i++) {
      const angle = (i / rayCount) * Math.PI * 2;
      const rayLength = height * (0.6 + Math.sin(elapsed * 0.0005 + i * 0.8) * 0.15);
      const rayWidth = Math.PI * 0.015 + Math.sin(elapsed * 0.0004 + i) * 0.005;

      const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, rayLength);
      const alpha = (0.04 + Math.sin(elapsed * 0.0006 + i * 1.2) * 0.02) * rayPulse;
      gradient.addColorStop(0, `rgba(255, 230, 160, ${alpha * 2})`);
      gradient.addColorStop(0.3, `rgba(255, 210, 120, ${alpha * 1.2})`);
      gradient.addColorStop(0.7, `rgba(255, 200, 100, ${alpha * 0.5})`);
      gradient.addColorStop(1, 'rgba(255, 200, 100, 0)');

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, rayLength, angle - rayWidth, angle + rayWidth);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();
    }
    ctx.restore();

    // ——— 2. SOFT SUN GLOW ———
    const sunGlow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, width * 0.25);
    const glowAlpha = 0.09 + Math.sin(elapsed * 0.0004) * 0.03;
    sunGlow.addColorStop(0, `rgba(255, 240, 200, ${glowAlpha * 2.5})`);
    sunGlow.addColorStop(0.4, `rgba(255, 220, 150, ${glowAlpha * 1.2})`);
    sunGlow.addColorStop(1, 'rgba(255, 220, 150, 0)');
    ctx.fillStyle = sunGlow;
    ctx.fillRect(0, 0, width, height);

    // ——— 3. DRIFTING CLOUD SHADOWS ———
    const cloudShadowCount = 4;
    for (let i = 0; i < cloudShadowCount; i++) {
      const speed = 0.008 + i * 0.003;
      const cloudX = ((elapsed * speed + i * width * 0.3) % (width * 1.6)) - width * 0.3;
      const cloudY = height * (0.15 + i * 0.12);
      const cloudW = width * (0.25 + i * 0.06);
      const cloudH = height * (0.06 + i * 0.02);

      const shadowGradient = ctx.createRadialGradient(
        cloudX + cloudW / 2, cloudY + cloudH / 2, 0,
        cloudX + cloudW / 2, cloudY + cloudH / 2, cloudW / 2
      );
      const shadowAlpha = 0.03 + Math.sin(elapsed * 0.0002 + i) * 0.015;
      shadowGradient.addColorStop(0, `rgba(0, 0, 0, ${shadowAlpha})`);
      shadowGradient.addColorStop(0.6, `rgba(0, 0, 0, ${shadowAlpha * 0.3})`);
      shadowGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.fillStyle = shadowGradient;
      ctx.fillRect(cloudX, cloudY, cloudW, cloudH);
    }

    // ——— 4. ATMOSPHERIC MIST PARTICLES ———
    const mistParticleCount = 18;
    for (let i = 0; i < mistParticleCount; i++) {
      const seed = i * 137.508; // golden angle for distribution
      const x = ((Math.sin(seed) * 0.5 + 0.5) * width * 1.2 + elapsed * (0.005 + i * 0.002)) % (width * 1.2) - width * 0.1;
      const baseY = height * (0.35 + (Math.cos(seed * 2) * 0.5 + 0.5) * 0.45);
      const y = baseY + Math.sin(elapsed * 0.0003 + seed) * 15;
      const size = 60 + Math.sin(seed * 3) * 40;
      const alpha = 0.025 + Math.sin(elapsed * 0.0004 + seed) * 0.015;

      const mistGradient = ctx.createRadialGradient(x, y, 0, x, y, size);
      mistGradient.addColorStop(0, `rgba(220, 230, 240, ${alpha})`);
      mistGradient.addColorStop(0.5, `rgba(200, 215, 230, ${alpha * 0.5})`);
      mistGradient.addColorStop(1, 'rgba(200, 215, 230, 0)');

      ctx.fillStyle = mistGradient;
      ctx.beginPath();
      ctx.ellipse(x, y, size * 1.5, size * 0.6, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // ——— 5. LAKE WATER SHIMMER ———
    // Water is in the center-left area of the reference image
    const waterCenterX = width * 0.35;
    const waterCenterY = height * 0.55;
    const shimmerCount = 25;

    for (let i = 0; i < shimmerCount; i++) {
      const seed = i * 97.3;
      const x = waterCenterX + (Math.sin(seed) * width * 0.2);
      const y = waterCenterY + (Math.cos(seed * 1.3) * height * 0.08);
      const sparklePhase = elapsed * 0.002 + seed;
      const sparkleAlpha = Math.max(0, Math.sin(sparklePhase) * 0.08 + 0.02);
      const sparkleSize = 2 + Math.sin(sparklePhase * 1.5) * 1.5;

      ctx.fillStyle = `rgba(255, 250, 230, ${sparkleAlpha})`;
      ctx.beginPath();
      ctx.arc(x, y, sparkleSize, 0, Math.PI * 2);
      ctx.fill();
    }

    // ——— 6. FLOATING DUST/POLLEN PARTICLES (near camera) ———
    const dustCount = 12;
    for (let i = 0; i < dustCount; i++) {
      const seed = i * 213.7;
      const progress = ((elapsed * 0.00008 + seed / 1000) % 1);
      const x = (Math.sin(seed * 2.3) * 0.5 + 0.5) * width;
      const y = height * (0.2 + progress * 0.6) + Math.sin(elapsed * 0.001 + seed) * 20;
      const alpha = Math.sin(progress * Math.PI) * 0.08;
      const size = 1 + Math.sin(seed) * 0.5;

      ctx.fillStyle = `rgba(255, 240, 200, ${alpha})`;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }

    // ——— 7. SUBTLE GOLDEN HOUR VIGNETTE SHIFT ———
    const vignetteShift = Math.sin(elapsed * 0.00015) * 0.01;
    const vignette = ctx.createRadialGradient(
      width * 0.4, height * 0.4, width * 0.2,
      width * 0.5, height * 0.5, width * 0.8
    );
    vignette.addColorStop(0, 'rgba(0, 0, 0, 0)');
    vignette.addColorStop(1, `rgba(0, 0, 0, ${0.12 + vignetteShift})`);
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, width, height);

  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2); // Cap at 2x for perf
      width = canvas.parentElement.offsetWidth;
      height = canvas.parentElement.offsetHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener('resize', resize);

    startTimeRef.current = performance.now();

    const animate = (now) => {
      const elapsed = now - startTimeRef.current;
      ctx.setTransform(1, 0, 0, 1, 0, 0); // Reset transform
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      ctx.scale(dpr, dpr);
      draw(ctx, width, height, elapsed);
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 5, mixBlendMode: 'screen' }}
    />
  );
}
