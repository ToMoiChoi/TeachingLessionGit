/**
 * Live Match Controller
 * - Đồng hồ MM:SS chạy mượt từng giây (hỗ trợ tốc độ trực tiếp từ 10s/phút -> 1s/phút và 0.5s/phút)
 * - Kích hoạt sự kiện theo đúng mốc giây trong từng phút (Sub-minute timeline)
 * - Hỗ trợ bù giờ thật (45+1', 45+2', 90+1'...), bảng diễn biến lọc được, Momentum, Stats & KQ cùng vòng live
 */
window.LiveMatchController = (function () {
    let state = null;
    let msPerMinute = 3000; // Mặc định 3s/phút (chỉnh được từ 10s -> 1s -> 0.5s)
    let isPaused = false;
    let isFetching = false;
    let currentFilter = 'all';

    // Trạng thái đồng hồ nội suy theo giây trong phút đang phát
    let activeMinute = 0;
    let activeInjury = 0;
    let minuteElapsedMs = 0;
    let lastFrameTs = null;
    let pendingEvents = [];
    let pendingPayload = null;
    let allDisplayedEvents = [];

    function init(initialState) {
        state = initialState;
        activeMinute = state.current_minute || 0;
        activeInjury = state.injury_minute || 0;

        LivePitchRenderer.init('pitchCanvas', state);
        renderInitialEvents(state.events || []);
        updateScoreboardFromState(state);
        updateStats({
            possession_home: state.possession_home ?? 50,
            possession_away: state.possession_away ?? 50,
            xg_home: state.xg_home ?? 0,
            xg_away: state.xg_away ?? 0,
            shots_home: state.shots_home ?? 0,
            shots_away: state.shots_away ?? 0,
            target_home: state.target_home ?? 0,
            target_away: state.target_away ?? 0,
            saves_home: state.saves_home ?? 0,
            saves_away: state.saves_away ?? 0,
            corners_home: state.corners_home ?? 0,
            corners_away: state.corners_away ?? 0,
            passes_home: state.passes_home ?? 0,
            passes_away: state.passes_away ?? 0,
            fouls_home: state.fouls_home ?? 0,
            fouls_away: state.fouls_away ?? 0,
            yellow_home: state.yellow_home ?? 0,
            yellow_away: state.yellow_away ?? 0,
            red_home: state.red_home ?? 0,
            red_away: state.red_away ?? 0
        });
        renderMomentum(state.momentum || []);
        renderOtherMatches(state.other_matches || []);
        syncPhaseUI(state);

        if (!state.finished && state.phase !== 'halftime') {
            fetchNextMinute();
        }
        requestAnimationFrame(clockLoop);
    }

    function formatClock(min, inj, sec) {
        const s = Math.max(0, Math.min(59, Math.floor(sec)));
        const ss = s < 10 ? `0${s}` : `${s}`;
        if (inj > 0) {
            return `${min}+${inj}:${ss}`;
        }
        const mm = min < 10 ? `0${min}` : `${min}`;
        return `${mm}:${ss}`;
    }

    function updateClockUI(min, inj, sec) {
        const el = document.getElementById('matchClock');
        if (el) el.textContent = formatClock(min, inj, sec);
    }

    function clockLoop(ts) {
        if (lastFrameTs === null) lastFrameTs = ts;
        const dt = Math.min(250, ts - lastFrameTs);
        lastFrameTs = ts;

        if (!isPaused && state && !state.finished && state.phase !== 'halftime' && pendingPayload) {
            minuteElapsedMs += dt;
            const progress = Math.min(1, minuteElapsedMs / msPerMinute);
            const displaySec = Math.floor(progress * 60);
            updateClockUI(activeMinute, activeInjury, Math.min(59, displaySec));

            // Kích hoạt các sự kiện đúng mốc giây
            while (pendingEvents.length > 0 && displaySec >= (pendingEvents[0].second || 0)) {
                const ev = pendingEvents.shift();
                fireEvent(ev);
            }

            // Kết thúc 60 giây của phút hiện tại -> đồng bộ số liệu & gọi phút kế tiếp
            if (minuteElapsedMs >= msPerMinute) {
                while (pendingEvents.length > 0) {
                    fireEvent(pendingEvents.shift());
                }
                const payload = pendingPayload;
                pendingPayload = null;
                applyEndOfMinutePayload(payload);

                if (!state.finished && state.phase !== 'halftime') {
                    fetchNextMinute();
                }
            }
        }
        requestAnimationFrame(clockLoop);
    }

    function fetchNextMinute() {
        if (isFetching || !state || state.finished || state.phase === 'halftime') return;
        isFetching = true;
        fetch('/api/tick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(res => res.json())
            .then(data => {
                isFetching = false;
                if (data.error) return;
                pendingPayload = data;
                activeMinute = data.current_minute;
                activeInjury = data.injury_minute || 0;
                minuteElapsedMs = 0;
                pendingEvents = (data.new_events || []).slice().sort((a, b) => (a.second || 0) - (b.second || 0));

                // Di chuyển bóng ngay theo ball_zone của phút này
                if (data.ball_zone !== undefined) {
                    LivePitchRenderer.setBallZone(data.ball_zone);
                }
                updateInjuryBadge(data);
            })
            .catch(err => {
                isFetching = false;
                console.error('Tick error:', err);
            });
    }

    function fireEvent(ev) {
        addEventToTimeline(ev);
        const tickerClock = document.getElementById('tickerClock');
        const tickerMsg = document.getElementById('tickerMsg');
        if (tickerClock) tickerClock.textContent = ev.clock || ev.minute_label || "00:00";
        if (tickerMsg) tickerMsg.textContent = ev.description || '';

        const t = ev.event_type || ev.type || '';
        if (t === 'goal' || (t === 'penalty_kick' && ev.data && ev.data.is_goal)) {
            LiveMatchAudio.goal();
            if (pendingPayload) {
                updateScoreNumbers(pendingPayload.home_goals, pendingPayload.away_goals, true);
                renderScorers(pendingPayload);
            }
        } else if (t === 'shot_miss') {
            if (ev.data && ev.data.woodwork) LiveMatchAudio.woodwork();
            else LiveMatchAudio.kick();
        } else if (t === 'yellow_card' || t === 'red_card' || t === 'foul' || t === 'penalty_call') {
            LiveMatchAudio.whistle('foul');
        } else if (t === 'var_check' || t === 'injury_time') {
            LiveMatchAudio.beep();
        } else if (t === 'halftime') {
            LiveMatchAudio.whistle('halftime');
        } else if (t === 'fulltime') {
            LiveMatchAudio.whistle('fulltime');
        }

        LivePitchRenderer.triggerEventAnimation(ev);
    }

    function applyEndOfMinutePayload(data) {
        state.home_goals = data.home_goals;
        state.away_goals = data.away_goals;
        state.current_minute = data.current_minute;
        state.injury_minute = data.injury_minute || 0;
        state.injury_time_h1 = data.injury_time_h1 || 0;
        state.injury_time_h2 = data.injury_time_h2 || 0;
        state.half = data.half;
        state.phase = data.phase;
        state.finished = data.finished;
        state.home_players = data.home_players || state.home_players;
        state.away_players = data.away_players || state.away_players;
        state.scorers_home = data.scorers_home || [];
        state.scorers_away = data.scorers_away || [];
        state.red_cards_home = data.red_cards_home || [];
        state.red_cards_away = data.red_cards_away || [];
        state.other_matches = data.other_matches || [];

        updateScoreNumbers(data.home_goals, data.away_goals, false);
        renderScorers(data);
        updateStats(data.stats);
        renderMomentum(data.momentum || []);
        renderOtherMatches(data.other_matches || []);
        LivePitchRenderer.syncPlayers(state.home_players, state.away_players);
        syncPhaseUI(data);
    }

    function updateInjuryBadge(data) {
        const badge = document.getElementById('injuryBadge');
        if (!badge) return;
        const inj1 = data.injury_time_h1 || 0;
        const inj2 = data.injury_time_h2 || 0;
        if (data.half === 1 && data.current_minute >= 45 && inj1 > 0) {
            badge.textContent = `+${inj1}'`;
            badge.style.display = 'inline-block';
        } else if (data.half === 2 && data.current_minute >= 90 && inj2 > 0) {
            badge.textContent = `+${inj2}'`;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }

    function updateScoreNumbers(hg, ag, flash = false) {
        const hEl = document.getElementById('scoreHome');
        const aEl = document.getElementById('scoreAway');
        if (hEl) {
            if (flash && parseInt(hEl.textContent, 10) !== hg) {
                hEl.classList.add('flash');
                setTimeout(() => hEl.classList.remove('flash'), 700);
            }
            hEl.textContent = hg;
        }
        if (aEl) {
            if (flash && parseInt(aEl.textContent, 10) !== ag) {
                aEl.classList.add('flash');
                setTimeout(() => aEl.classList.remove('flash'), 700);
            }
            aEl.textContent = ag;
        }
    }

    function updateScoreboardFromState(s) {
        updateScoreNumbers(s.home_goals || 0, s.away_goals || 0, false);
        updateClockUI(s.current_minute || 0, s.injury_minute || 0, 0);
        renderScorers(s);
    }

    function renderScorers(data) {
        const renderSide = (elId, scorers, reds) => {
            const el = document.getElementById(elId);
            if (!el) return;
            const pills = [];
            (scorers || []).forEach(s => {
                pills.push(`<span class="sb-scorer-pill">⚽ ${s.name} ${s.minute}</span>`);
            });
            (reds || []).forEach(r => {
                pills.push(`<span class="sb-scorer-pill red">🟥 ${r.name} ${r.minute}</span>`);
            });
            el.innerHTML = pills.join('');
        };
        renderSide('scorersHome', data.scorers_home, data.red_cards_home);
        renderSide('scorersAway', data.scorers_away, data.red_cards_away);
    }

    function syncPhaseUI(data) {
        const dot = document.getElementById('liveDot');
        const pill = document.getElementById('phasePill');
        const htBanner = document.getElementById('halftimeBanner');
        const ftBanner = document.getElementById('fulltimeBanner');
        const htScore = document.getElementById('htScoreText');
        const ftScore = document.getElementById('ftScoreText');

        if (data.finished || data.phase === 'finished') {
            if (dot) dot.className = 'sb-live-dot finished';
            if (pill) pill.textContent = 'KẾT THÚC (FT)';
            if (htBanner) htBanner.classList.remove('visible');
            if (ftBanner) ftBanner.classList.add('visible');
            if (ftScore) ftScore.textContent = `${data.home_goals} - ${data.away_goals}`;
            updateClockUI(90, data.injury_time_h2 || 0, 0);
        } else if (data.phase === 'halftime' || data.halftime) {
            if (dot) dot.className = 'sb-live-dot paused';
            if (pill) pill.textContent = 'NGHỈ GIỮA HIỆP (HT)';
            if (htBanner) htBanner.classList.add('visible');
            if (htScore) htScore.textContent = `${data.home_goals} - ${data.away_goals}`;
            updateClockUI(45, data.injury_time_h1 || 0, 0);
        } else {
            if (dot) dot.className = isPaused ? 'sb-live-dot paused' : 'sb-live-dot';
            if (pill) pill.textContent = isPaused ? 'TẠM DỪNG' : (data.half === 2 ? 'HIỆP 2 • LIVE' : 'HIỆP 1 • LIVE');
            if (htBanner) htBanner.classList.remove('visible');
            if (ftBanner) ftBanner.classList.remove('visible');
        }
    }

    function updateStats(st) {
        if (!st) return;
        const setBar = (idH, idA, barId, valH, valA, suffix = '') => {
            const hEl = document.getElementById(idH);
            const aEl = document.getElementById(idA);
            const bEl = document.getElementById(barId);
            if (hEl) hEl.textContent = `${valH}${suffix}`;
            if (aEl) aEl.textContent = `${valA}${suffix}`;
            if (bEl) {
                const nH = parseFloat(valH) || 0;
                const nA = parseFloat(valA) || 0;
                const pct = (nH + nA) > 0 ? Math.round((nH / (nH + nA)) * 100) : 50;
                bEl.style.width = `${pct}%`;
            }
        };

        setBar('stPosH', 'stPosA', 'barPos', st.possession_home ?? 50, st.possession_away ?? 50, '%');
        setBar('stXgH', 'stXgA', 'barXg', (st.xg_home ?? 0).toFixed(2), (st.xg_away ?? 0).toFixed(2));
        setBar('stShotsH', 'stShotsA', 'barShots', st.shots_home ?? 0, st.shots_away ?? 0);
        setBar('stTargetH', 'stTargetA', 'barTarget', st.target_home ?? 0, st.target_away ?? 0);
        setBar('stSavesH', 'stSavesA', 'barSaves', st.saves_home ?? 0, st.saves_away ?? 0);
        setBar('stCornersH', 'stCornersA', 'barCorners', st.corners_home ?? 0, st.corners_away ?? 0);
        setBar('stPassesH', 'stPassesA', 'barPasses', st.passes_home ?? 0, st.passes_away ?? 0);

        const cardStr = (f, y, r) => `${f}${y ? ` (🟨${y})` : ''}${r ? ` (🟥${r})` : ''}`;
        const fH = document.getElementById('stFoulsH');
        const fA = document.getElementById('stFoulsA');
        if (fH) fH.textContent = cardStr(st.fouls_home ?? 0, st.yellow_home ?? 0, st.red_home ?? 0);
        if (fA) fA.textContent = cardStr(st.fouls_away ?? 0, st.yellow_away ?? 0, st.red_away ?? 0);
    }

    function renderMomentum(list) {
        const wrap = document.getElementById('momentumBars');
        if (!wrap) return;
        const html = (list || []).map(item => {
            const v = item.v || 0;
            const hPct = v > 0 ? Math.min(100, Math.abs(v)) : 0;
            const aPct = v < 0 ? Math.min(100, Math.abs(v)) : 0;
            return `<div class="mom-col" title="${item.m}: ${v >= 0 ? 'Đội nhà ép sân' : 'Đối thủ ép sân'}">
                <div class="mom-top">${hPct ? `<div class="mom-fill-home" style="height:${hPct}%"></div>` : ''}</div>
                <div class="mom-bot">${aPct ? `<div class="mom-fill-away" style="height:${aPct}%"></div>` : ''}</div>
            </div>`;
        }).join('');
        wrap.innerHTML = html || '<div style="width:100%;text-align:center;font-size:0.72rem;color:#64748b;">Đang chờ nhịp độ trận đấu...</div>';
    }

    function renderOtherMatches(list) {
        const el = document.getElementById('otherMatchesList');
        if (!el) return;
        if (!list || list.length === 0) {
            el.innerHTML = '<p style="color:#94a3b8;font-size:0.84rem;">Không có trận đấu nào khác cùng giờ.</p>';
            return;
        }
        el.innerHTML = list.map(m => `
            <div class="other-match-row">
                <div>
                    <strong>${m.home}</strong> vs <strong>${m.away}</strong>
                    ${m.last_scorer ? `<div style="font-size:0.72rem;color:#34d399;margin-top:2px;">⚽ Gần nhất: ${m.last_scorer}</div>` : ''}
                </div>
                <span class="om-score">${m.home_goals} - ${m.away_goals}</span>
            </div>
        `).join('');
    }

    function matchesFilter(ev) {
        if (currentFilter === 'all') return true;
        const t = ev.event_type || ev.type || '';
        if (currentFilter === 'key') return !!ev.is_key || ['goal', 'shot_miss', 'penalty_call', 'penalty_kick', 'var_check', 'yellow_card', 'red_card', 'substitution', 'halftime', 'fulltime'].includes(t);
        if (currentFilter === 'goals_cards') return ['goal', 'penalty_kick', 'yellow_card', 'red_card', 'var_check'].includes(t);
        return true;
    }

    function createTimelineNode(ev) {
        const div = document.createElement('div');
        const t = ev.event_type || ev.type || 'general';
        div.className = `tl-item ev-${t}`;
        const clockText = ev.clock || ev.minute_label || "00:00";
        div.innerHTML = `<span class="tl-clock">${clockText}</span><span class="tl-desc">${ev.description || ''}</span>`;
        return div;
    }

    function addEventToTimeline(ev) {
        allDisplayedEvents.unshift(ev);
        if (!matchesFilter(ev)) return;
        const feed = document.getElementById('timelineFeed');
        if (!feed) return;
        feed.prepend(createTimelineNode(ev));
    }

    function renderInitialEvents(events) {
        allDisplayedEvents = (events || []).slice().reverse();
        rebuildTimeline();
    }

    function rebuildTimeline() {
        const feed = document.getElementById('timelineFeed');
        if (!feed) return;
        feed.innerHTML = '';
        allDisplayedEvents.filter(matchesFilter).forEach(ev => {
            feed.appendChild(createTimelineNode(ev));
        });
    }

    function setFilter(filterName, btn) {
        currentFilter = filterName;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        if (btn) btn.classList.add('active');
        rebuildTimeline();
    }

    // ---------- ĐIỀU KHIỂN TỐC ĐỘ 10s -> 1s (và 0.5s) ----------
    function setSpeedSeconds(secPerMin, btn) {
        const clamped = Math.max(0.5, Math.min(10, parseFloat(secPerMin) || 3));
        msPerMinute = Math.round(clamped * 1000);
        const slider = document.getElementById('speedSlider');
        const readout = document.getElementById('speedReadout');
        if (slider && clamped >= 1) slider.value = clamped;
        if (readout) readout.textContent = `${clamped}s / phút`;
        document.querySelectorAll('.btn-speed-preset').forEach(b => b.classList.remove('active'));
        if (btn) btn.classList.add('active');
    }

    function onSliderSpeed(val) {
        const sec = parseFloat(val) || 3;
        msPerMinute = Math.round(sec * 1000);
        const readout = document.getElementById('speedReadout');
        if (readout) readout.textContent = `${sec}s / phút`;
        document.querySelectorAll('.btn-speed-preset').forEach(b => b.classList.remove('active'));
    }

    function togglePause() {
        isPaused = !isPaused;
        const btn = document.getElementById('pauseBtn');
        if (btn) {
            btn.textContent = isPaused ? '▶️ Tiếp tục' : '⏸️ Tạm dừng';
            btn.classList.toggle('btn-warning', isPaused);
        }
        syncPhaseUI(state);
    }

    function skipCurrentHalf() {
        if (isFetching || !state || state.finished || state.phase === 'halftime') return;
        isFetching = true;
        pendingPayload = null;
        pendingEvents = [];
        fetch('/api/skip_half', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
            .then(r => r.json())
            .then(data => {
                isFetching = false;
                if (data.error) return;
                (data.new_events || []).forEach(ev => addEventToTimeline(ev));
                applyEndOfMinutePayload(data);
                if (data.finished) LiveMatchAudio.whistle('fulltime');
                else if (data.halftime) LiveMatchAudio.whistle('halftime');
            })
            .catch(() => { isFetching = false; });
    }

    function startSecondHalf() {
        fetch('/start_second_half', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                state.phase = 'second_half';
                state.half = 2;
                state.current_minute = 45;
                state.injury_minute = 0;
                if (data.event) addEventToTimeline(data.event);
                isPaused = false;
                syncPhaseUI(state);
                fetchNextMinute();
            });
    }

    function setTactic(tactic, btn) {
        fetch('/api/change_tactic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tactic })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.querySelectorAll('.btn-tactic').forEach(b => b.classList.remove('active'));
                    if (btn) btn.classList.add('active');
                    if (data.event) addEventToTimeline(data.event);
                    LivePitchRenderer.showBanner(`📋 CHIẾN THUẬT: ${tactic.toUpperCase()}`, 'Đội hình lập tức điều chỉnh nhịp độ thi đấu!', '#38bdf8', 1800);
                }
            });
    }

    function changeFormation(formation) {
        fetch('/api/change_live_formation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formation })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    state.home_formation = formation;
                    LivePitchRenderer.setFormation(formation);
                    if (data.event) addEventToTimeline(data.event);
                    LivePitchRenderer.showBanner(`📐 ĐỔI SƠ ĐỒ: ${formation}`, 'Các tuyến đã di chuyển theo sơ đồ mới!', '#38bdf8', 1800);
                }
            });
    }

    // ---------- MODALS ----------
    function openModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add('open');
    }
    function closeModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove('open');
    }

    function openSubModal() {
        fetch('/get_players')
            .then(r => r.json())
            .then(data => {
                const outSel = document.getElementById('playerOutSelect');
                const inSel = document.getElementById('playerInSelect');
                outSel.innerHTML = (data.starting || []).map(p =>
                    `<option value="${p.id}">[${p.position}] ${p.name} — Thể lực ${Math.round(p.stamina)}%</option>`
                ).join('');
                inSel.innerHTML = (data.subs || []).map(p =>
                    `<option value="${p.id}">[${p.position}] ${p.name} — Thể lực ${Math.round(p.stamina)}%</option>`
                ).join('');
                openModal('subModal');
            });
    }

    function confirmSub() {
        const outId = parseInt(document.getElementById('playerOutSelect').value, 10);
        const inId = parseInt(document.getElementById('playerInSelect').value, 10);
        fetch('/substitute_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_out: outId, player_in: inId })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const cnt = document.getElementById('subsUsedCount');
                    if (cnt) cnt.textContent = data.subs_used;
                    if (data.event) addEventToTimeline(data.event);
                    const idx = state.home_players.findIndex(p => p.id === data.player_out.id);
                    if (idx !== -1) {
                        state.home_players[idx] = {
                            ...state.home_players[idx],
                            id: data.player_in.id,
                            name: data.player_in.name,
                            position: data.player_in.position || state.home_players[idx].position,
                            stamina: data.player_in.stamina || 100,
                            yellow_cards: 0,
                            red_cards: 0
                        };
                        LivePitchRenderer.syncPlayers(state.home_players, state.away_players);
                    }
                    closeModal('subModal');
                    LivePitchRenderer.showBanner('🔄 THAY NGƯỜI', `${data.player_out.name} ⬇️ • ${data.player_in.name} ⬆️`, '#a855f7', 2200);
                } else {
                    alert(data.error || 'Không thể thay người!');
                }
            });
    }

    function openLineupsModal() {
        const renderList = (players) => (players || []).map(p => {
            const st = Math.round(p.stamina ?? 100);
            const col = st > 65 ? '#10b981' : (st > 40 ? '#eab308' : '#ef4444');
            const cards = `${p.yellow_cards ? ' 🟨' : ''}${p.red_cards ? ' 🟥' : ''}`;
            const goals = p.goals ? ` ⚽x${p.goals}` : '';
            return `<div class="lineup-row ${p.red_cards ? 'sent-off' : ''}">
                <span><strong>[${p.position}]</strong> ${p.name}${goals}${cards}</span>
                <span>${st}% <span class="stamina-pill"><span class="stamina-fill" style="width:${st}%;background:${col}"></span></span></span>
            </div>`;
        }).join('');
        const hEl = document.getElementById('lineupHomeList');
        const aEl = document.getElementById('lineupAwayList');
        if (hEl) hEl.innerHTML = renderList(state.home_players);
        if (aEl) aEl.innerHTML = renderList(state.away_players);
        openModal('lineupsModal');
    }

    function toggleAudio(btn) {
        const on = LiveMatchAudio.toggle();
        if (btn) btn.textContent = on ? '🔊 Âm thanh: Bật' : '🔇 Âm thanh: Tắt';
    }

    return {
        init, setFilter, setSpeedSeconds, onSliderSpeed, togglePause, skipCurrentHalf,
        startSecondHalf, setTactic, changeFormation, openModal, closeModal,
        openSubModal, confirmSub, openLineupsModal, toggleAudio
    };
})();
