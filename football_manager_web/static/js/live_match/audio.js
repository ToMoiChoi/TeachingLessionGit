/**
 * Live Match Web Audio API Sound Effects Manager
 */
window.LiveMatchAudio = (function () {
    let ctx = null;
    let enabled = true;
    let volume = 0.45;

    function getCtx() {
        if (!ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) ctx = new AudioCtx();
        }
        if (ctx && ctx.state === 'suspended') {
            ctx.resume().catch(() => {});
        }
        return ctx;
    }

    function playTone(freq, duration, type = 'sine', gainMult = 0.25, delay = 0) {
        if (!enabled || volume <= 0.01) return;
        const c = getCtx();
        if (!c) return;
        const now = c.currentTime + delay;
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, now);
        gain.gain.setValueAtTime(0.001, now);
        gain.gain.exponentialRampToValueAtTime(Math.max(0.002, volume * gainMult), now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(now);
        osc.stop(now + duration + 0.02);
    }

    return {
        setVolume(v) {
            volume = Math.max(0, Math.min(1, parseFloat(v) || 0));
        },
        toggle() {
            enabled = !enabled;
            return enabled;
        },
        isEnabled() {
            return enabled;
        },
        whistle(kind = 'foul') {
            if (kind === 'fulltime') {
                playTone(2850, 0.22, 'sine', 0.22, 0);
                playTone(2850, 0.22, 'sine', 0.22, 0.30);
                playTone(2900, 0.55, 'sine', 0.25, 0.62);
            } else if (kind === 'halftime') {
                playTone(2850, 0.20, 'sine', 0.22, 0);
                playTone(2900, 0.45, 'sine', 0.24, 0.28);
            } else {
                playTone(2850, 0.25, 'sine', 0.20, 0);
            }
        },
        kick() {
            playTone(135, 0.10, 'triangle', 0.32, 0);
            playTone(80, 0.08, 'sine', 0.25, 0.02);
        },
        goal() {
            playTone(523.25, 0.16, 'triangle', 0.28, 0);
            playTone(659.25, 0.16, 'triangle', 0.28, 0.14);
            playTone(783.99, 0.22, 'triangle', 0.30, 0.28);
            playTone(1046.5, 0.45, 'triangle', 0.32, 0.48);
        },
        woodwork() {
            playTone(420, 0.22, 'square', 0.18, 0);
            playTone(290, 0.30, 'triangle', 0.22, 0.04);
        },
        beep() {
            playTone(1200, 0.12, 'sine', 0.18, 0);
            playTone(1500, 0.15, 'sine', 0.18, 0.15);
        }
    };
})();
