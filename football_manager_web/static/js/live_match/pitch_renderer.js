/**
 * Synchronized 2D Tactical Pitch Renderer
 * Đồng bộ trực tiếp với ball_zone (0..100), đội hình thực tế và animation sự kiện từng giây.
 */
window.LivePitchRenderer = (function () {
    const W = 900;
    const H = 520;
    const PAD = 34;

    const FORMATION_COORDS = {
        '4-3-3': [
            [0.06, 0.50], [0.22, 0.14], [0.20, 0.38], [0.20, 0.62], [0.22, 0.86],
            [0.44, 0.24], [0.42, 0.50], [0.44, 0.76], [0.68, 0.16], [0.68, 0.84], [0.72, 0.50]
        ],
        '4-2-3-1': [
            [0.06, 0.50], [0.22, 0.14], [0.20, 0.38], [0.20, 0.62], [0.22, 0.86],
            [0.37, 0.36], [0.37, 0.64], [0.56, 0.18], [0.58, 0.50], [0.56, 0.82], [0.74, 0.50]
        ],
        '4-4-2': [
            [0.06, 0.50], [0.22, 0.14], [0.20, 0.38], [0.20, 0.62], [0.22, 0.86],
            [0.46, 0.14], [0.44, 0.38], [0.44, 0.62], [0.46, 0.86], [0.70, 0.36], [0.70, 0.64]
        ],
        '5-3-2': [
            [0.06, 0.50], [0.28, 0.12], [0.19, 0.30], [0.18, 0.50], [0.19, 0.70],
            [0.28, 0.88], [0.46, 0.28], [0.44, 0.50], [0.46, 0.72], [0.70, 0.36], [0.70, 0.64]
        ],
        '3-5-2': [
            [0.06, 0.50], [0.20, 0.26], [0.18, 0.50], [0.20, 0.74],
            [0.42, 0.12], [0.38, 0.36], [0.46, 0.50], [0.38, 0.64], [0.42, 0.88], [0.70, 0.36], [0.70, 0.64]
        ],
        '3-4-3': [
            [0.06, 0.50], [0.20, 0.26], [0.18, 0.50], [0.20, 0.74],
            [0.44, 0.15], [0.42, 0.40], [0.42, 0.60], [0.44, 0.85], [0.68, 0.18], [0.68, 0.82], [0.73, 0.50]
        ],
        '4-3-2-1': [
            [0.06, 0.50], [0.22, 0.14], [0.20, 0.38], [0.20, 0.62], [0.22, 0.86],
            [0.39, 0.26], [0.37, 0.50], [0.39, 0.74], [0.58, 0.34], [0.58, 0.66], [0.74, 0.50]
        ],
        '5-4-1': [
            [0.06, 0.50], [0.26, 0.12], [0.19, 0.30], [0.18, 0.50], [0.19, 0.70],
            [0.26, 0.88], [0.46, 0.18], [0.44, 0.40], [0.44, 0.60], [0.46, 0.82], [0.70, 0.50]
        ]
    };

    let canvas = null;
    let ctx = null;
    let homePlayers = [];
    let awayPlayers = [];
    let homeFormation = '4-3-3';
    let awayFormation = '4-3-3';
    let targetBallZone = 50; // 0..100
    let ball = { x: W / 2, y: H / 2, tx: W / 2, ty: H / 2, trail: [] };
    let particles = [];
    let animPhase = 0;
    let bannerTimer = null;

    function init(canvasId, matchState) {
        canvas = document.getElementById(canvasId);
        if (!canvas) return;
        ctx = canvas.getContext('2d');
        canvas.width = W;
        canvas.height = H;
        homeFormation = matchState.home_formation || '4-3-3';
        awayFormation = matchState.away_formation || '4-3-3';
        syncPlayers(matchState.home_players || [], matchState.away_players || []);
        requestAnimationFrame(loop);
    }

    function shortName(full) {
        if (!full) return '';
        const parts = full.trim().split(' ');
        return parts[parts.length - 1].slice(0, 9);
    }

    function syncPlayers(hList, aList) {
        const hCoords = FORMATION_COORDS[homeFormation] || FORMATION_COORDS['4-3-3'];
        const aCoords = FORMATION_COORDS[awayFormation] || FORMATION_COORDS['4-3-3'];

        homePlayers = hList.slice(0, 11).map((p, i) => {
            const [nx, ny] = hCoords[i] || [0.4, 0.5];
            const prev = homePlayers[i];
            const bx = PAD + nx * (W - PAD * 2);
            const by = PAD + ny * (H - PAD * 2);
            return {
                ...p,
                label: shortName(p.name),
                baseX: bx, baseY: by,
                x: prev ? prev.x : bx,
                y: prev ? prev.y : by,
                isHome: true
            };
        });

        awayPlayers = aList.slice(0, 11).map((p, i) => {
            const [nx, ny] = aCoords[i] || [0.4, 0.5];
            const prev = awayPlayers[i];
            const bx = PAD + (1 - nx) * (W - PAD * 2);
            const by = PAD + (1 - ny) * (H - PAD * 2);
            return {
                ...p,
                label: shortName(p.name),
                baseX: bx, baseY: by,
                x: prev ? prev.x : bx,
                y: prev ? prev.y : by,
                isHome: false
            };
        });
    }

    function setFormation(fmt) {
        homeFormation = fmt || '4-3-3';
        syncPlayers(homePlayers, awayPlayers);
    }

    function setBallZone(zone) {
        targetBallZone = Math.max(6, Math.min(94, zone));
        ball.tx = PAD + (targetBallZone / 100) * (W - PAD * 2);
        ball.ty = PAD + (0.20 + Math.random() * 0.60) * (H - PAD * 2);
    }

    function spawnBurst(x, y, color, count = 24) {
        for (let i = 0; i < count; i++) {
            const angle = (Math.PI * 2 * i) / count + Math.random() * 0.3;
            const speed = 1.5 + Math.random() * 4.5;
            particles.push({
                x, y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 1.0,
                color
            });
        }
    }

    function showBanner(title, sub, borderColor = '#facc15', durationMs = 2400) {
        const box = document.getElementById('pitchBanner');
        const tEl = document.getElementById('pitchBannerTitle');
        const sEl = document.getElementById('pitchBannerSub');
        if (!box || !tEl || !sEl) return;
        tEl.textContent = title;
        tEl.style.color = borderColor;
        sEl.textContent = sub;
        box.style.borderColor = borderColor;
        box.classList.add('show');
        if (bannerTimer) clearTimeout(bannerTimer);
        bannerTimer = setTimeout(() => box.classList.remove('show'), durationMs);
    }

    function triggerEventAnimation(ev) {
        const type = ev.event_type || ev.type || '';
        const d = ev.data || {};
        const isHome = d.is_home !== undefined ? d.is_home : true;

        if (type === 'goal') {
            const gx = isHome ? W - PAD + 4 : PAD - 4;
            const gy = H / 2 + (Math.random() - 0.5) * 44;
            ball.tx = gx;
            ball.ty = gy;
            spawnBurst(gx, gy, '#facc15', 36);
            spawnBurst(gx, gy, isHome ? '#10b981' : '#f43f5e', 24);
            showBanner(`⚽ VÀOOO! (${ev.minute_label})`, `${d.shooter || 'Cầu thủ'} lập công! Tỉ số ${d.score || ''}`, '#10b981', 3200);
        } else if (type === 'shot_miss') {
            const gx = isHome ? W - PAD - 8 : PAD + 8;
            const gy = H / 2 + (Math.random() - 0.5) * 90;
            ball.tx = gx;
            ball.ty = gy;
            if (d.woodwork) {
                spawnBurst(gx, gy, '#fb923c', 18);
                showBanner(`💥 DỘI KHUNG GỖ! (${ev.minute_label})`, `${d.shooter || 'Cầu thủ'} dứt điểm đập xà/cột!`, '#fb923c', 2200);
            } else if (d.target) {
                spawnBurst(gx, gy, '#38bdf8', 14);
                showBanner(`🧤 CỨU THUA XUẤT SẮC!`, `Thủ môn cản phá cú sút của ${d.shooter || 'đối phương'}`, '#38bdf8', 1900);
            }
        } else if (type === 'penalty_kick') {
            const gx = isHome ? W - PAD : PAD;
            ball.tx = gx;
            ball.ty = H / 2;
            if (d.is_goal) {
                spawnBurst(gx, H / 2, '#facc15', 32);
                showBanner(`🎯 PENALTY THÀNH CÔNG!`, `${d.taker} đánh bại ${d.gk}!`, '#10b981', 2800);
            } else {
                spawnBurst(gx, H / 2, '#38bdf8', 20);
                showBanner(`🧤 CẢN PHÁ PENALTY!`, `${d.gk} đẩy cú sút 11m của ${d.taker}!`, '#38bdf8', 2500);
            }
        } else if (type === 'corner_kick') {
            ball.tx = isHome ? W - PAD - 4 : PAD + 4;
            ball.ty = d.side === 'top' ? PAD + 6 : H - PAD - 6;
        } else if (type === 'red_card') {
            showBanner(`🟥 THẺ ĐỎ! (${ev.minute_label})`, `${d.player} (${d.team}) bị truất quyền thi đấu!`, '#ef4444', 2800);
        } else if (type === 'yellow_card') {
            showBanner(`🟨 THẺ VÀNG (${ev.minute_label})`, `Cảnh cáo ${d.player} (${d.team})`, '#eab308', 1800);
        } else if (type === 'var_check') {
            const ok = d.decision === 'confirmed';
            showBanner(`🖥️ VAR: ${ok ? 'XÁC NHẬN' : 'TỪ CHỐI'}!`, `${d.player || ''} — ${ok ? 'Quyết định hợp lệ' : 'Lỗi việt vị'}`, ok ? '#10b981' : '#ef4444', 2600);
        } else if (type === 'injury_time') {
            showBanner(`⏱️ BÙ GIỜ +${d.extra_minutes} PHÚT`, `Trọng tài bàn giơ bảng điện tử Hiệp ${d.half}`, '#4ade80', 2200);
        }
    }

    function drawPitch() {
        const stripes = 10;
        const sw = W / stripes;
        for (let i = 0; i < stripes; i++) {
            ctx.fillStyle = i % 2 === 0 ? '#166534' : '#15803d';
            ctx.fillRect(i * sw, 0, sw + 1, H);
        }

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.72)';
        ctx.lineWidth = 2;

        // Outer boundary
        ctx.strokeRect(PAD, PAD, W - PAD * 2, H - PAD * 2);
        // Halfway line & center circle
        ctx.beginPath();
        ctx.moveTo(W / 2, PAD);
        ctx.lineTo(W / 2, H - PAD);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(W / 2, H / 2, 62, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(W / 2, H / 2, 3.5, 0, Math.PI * 2);
        ctx.fill();

        // Penalty boxes
        const boxW = 122, boxH = 230;
        const sixW = 44, sixH = 112;
        ctx.strokeRect(PAD, (H - boxH) / 2, boxW, boxH);
        ctx.strokeRect(W - PAD - boxW, (H - boxH) / 2, boxW, boxH);
        ctx.strokeRect(PAD, (H - sixH) / 2, sixW, sixH);
        ctx.strokeRect(W - PAD - sixW, (H - sixH) / 2, sixW, sixH);

        // Goals
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.lineWidth = 3;
        ctx.strokeRect(PAD - 14, H / 2 - 36, 14, 72);
        ctx.strokeRect(W - PAD, H / 2 - 36, 14, 72);
    }

    function updateAndDrawPlayers() {
        const shift = ((targetBallZone - 50) / 50) * 85;
        const drawList = (list, color, border) => {
            list.forEach((p, idx) => {
                const isGK = (p.position === 'GK' || idx === 0);
                const driftX = isGK ? shift * 0.12 : shift * 0.85;
                const swayX = Math.sin(animPhase * 0.03 + idx * 1.4) * (isGK ? 2 : 7);
                const swayY = Math.cos(animPhase * 0.025 + idx * 1.1) * (isGK ? 5 : 8);

                const tx = Math.max(PAD + 14, Math.min(W - PAD - 14, p.baseX + driftX + swayX));
                const ty = Math.max(PAD + 14, Math.min(H - PAD - 14, p.baseY + swayY));
                p.x += (tx - p.x) * 0.06;
                p.y += (ty - p.y) * 0.06;

                ctx.save();
                if (p.red_cards > 0) ctx.globalAlpha = 0.25;

                // Shadow
                ctx.fillStyle = 'rgba(0,0,0,0.35)';
                ctx.beginPath();
                ctx.ellipse(p.x, p.y + 11, 10, 4, 0, 0, Math.PI * 2);
                ctx.fill();

                // Token
                ctx.fillStyle = isGK ? '#f59e0b' : color;
                ctx.strokeStyle = border;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(p.x, p.y, 11, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();

                // Position code inside circle
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 8px Segoe UI';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText((p.position || '').slice(0, 3), p.x, p.y);

                // Name below
                ctx.fillStyle = 'rgba(2, 6, 23, 0.72)';
                ctx.fillRect(p.x - 24, p.y + 13, 48, 12);
                ctx.fillStyle = '#f8fafc';
                ctx.font = '600 9px Segoe UI';
                ctx.fillText(p.label, p.x, p.y + 19);

                // Card badge
                if (p.red_cards > 0 || p.yellow_cards > 0) {
                    ctx.fillStyle = p.red_cards > 0 ? '#ef4444' : '#facc15';
                    ctx.fillRect(p.x + 8, p.y - 12, 6, 8);
                }
                ctx.restore();
            });
        };

        drawList(homePlayers, '#10b981', '#ecfdf5');
        drawList(awayPlayers, '#f43f5e', '#fff1f2');
    }

    function updateAndDrawBall() {
        ball.x += (ball.tx - ball.x) * 0.09;
        ball.y += (ball.ty - ball.y) * 0.09;
        ball.trail.push({ x: ball.x, y: ball.y });
        if (ball.trail.length > 10) ball.trail.shift();

        // Trail
        for (let i = 0; i < ball.trail.length; i++) {
            const pt = ball.trail[i];
            ctx.fillStyle = `rgba(255, 255, 255, ${(i / ball.trail.length) * 0.35})`;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 3 + (i / ball.trail.length) * 3, 0, Math.PI * 2);
            ctx.fill();
        }

        // Ball
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.arc(ball.x, ball.y, 6.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
    }

    function updateAndDrawParticles() {
        for (let i = particles.length - 1; i >= 0; i--) {
            const pt = particles[i];
            pt.x += pt.vx;
            pt.y += pt.vy;
            pt.life -= 0.025;
            if (pt.life <= 0) {
                particles.splice(i, 1);
                continue;
            }
            ctx.globalAlpha = pt.life;
            ctx.fillStyle = pt.color;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 3.2, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
        }
    }

    function loop() {
        if (!ctx) return;
        animPhase++;
        drawPitch();
        updateAndDrawPlayers();
        updateAndDrawBall();
        updateAndDrawParticles();
        requestAnimationFrame(loop);
    }

    return {
        init,
        syncPlayers,
        setFormation,
        setBallZone,
        triggerEventAnimation,
        showBanner
    };
})();
