(function () {
    const clickAudio = new Audio('/sounds/sfx/Click.wav');
    clickAudio.volume = 0.5;
    document.addEventListener('click', (e) => {
        if (e.target.closest('a, button, select, input, .btn, [onclick], .tactic-btn')) {
            clickAudio.currentTime = 0;
            clickAudio.play().catch(() => {});
        }
    });

    const widget = document.getElementById('fifa-player-widget');
    if (window.location.pathname.includes('/live_match')) {
        if (widget) widget.style.display = 'none';
        return;
    }
    if (!widget) return;

    const dragHandle = document.getElementById('fDragHandle');
    let isDragging = false;
    let startX = 0, startY = 0, initialLeft = 0, initialTop = 0;

    const savedPos = JSON.parse(localStorage.getItem('fifa_widget_pos') || 'null');
    if (savedPos) {
        widget.style.left = `${Math.min(window.innerWidth - 80, Math.max(10, savedPos.left))}px`;
        widget.style.top = `${Math.min(window.innerHeight - 50, Math.max(10, savedPos.top))}px`;
        widget.style.right = 'auto';
        widget.style.bottom = 'auto';
    }

    function onDragStart(e) {
        if (e.target.closest('button, select, input')) return;
        isDragging = true;
        widget.classList.add('dragging');
        startX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        startY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        const rect = widget.getBoundingClientRect();
        initialLeft = rect.left;
        initialTop = rect.top;
        widget.style.left = `${initialLeft}px`;
        widget.style.top = `${initialTop}px`;
        widget.style.right = 'auto';
        widget.style.bottom = 'auto';
        document.addEventListener('mousemove', onDragMove);
        document.addEventListener('mouseup', onDragEnd);
        document.addEventListener('touchmove', onDragMove, { passive: false });
        document.addEventListener('touchend', onDragEnd);
    }

    function onDragMove(e) {
        if (!isDragging) return;
        if (e.cancelable) e.preventDefault();
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        const maxLeft = window.innerWidth - widget.offsetWidth - 8;
        const maxTop = window.innerHeight - widget.offsetHeight - 8;
        widget.style.left = `${Math.max(8, Math.min(maxLeft, initialLeft + (clientX - startX)))}px`;
        widget.style.top = `${Math.max(8, Math.min(maxTop, initialTop + (clientY - startY)))}px`;
    }

    function onDragEnd() {
        if (!isDragging) return;
        isDragging = false;
        widget.classList.remove('dragging');
        const rect = widget.getBoundingClientRect();
        localStorage.setItem('fifa_widget_pos', JSON.stringify({ left: rect.left, top: rect.top }));
        document.removeEventListener('mousemove', onDragMove);
        document.removeEventListener('mouseup', onDragEnd);
        document.removeEventListener('touchmove', onDragMove);
        document.removeEventListener('touchend', onDragEnd);
    }

    if (dragHandle) dragHandle.addEventListener('mousedown', onDragStart);
    widget.addEventListener('mousedown', (e) => {
        if (e.target === widget || e.target.classList.contains('f-info') || e.target.classList.contains('f-text')) {
            onDragStart(e);
        }
    });
    widget.addEventListener('touchstart', onDragStart, { passive: true });

    const fifaTracks = [
        { title: "Love Me Again", file: "/sounds/bgm/John Newman - Love Me Again.mp3" },
        { title: "Heat Waves", file: "/sounds/bgm/Glass Animals - Heat Waves (Official Video).mp3" },
        { title: "Feet Don't Fail Me Now", file: "/sounds/bgm/Joy Crookes - Feet Don t Fail Me Now (Official Video).mp3" }
    ];

    const audio = new Audio();
    audio.preload = "auto";
    let currentIdx = parseInt(localStorage.getItem('fifa_track_idx') || '0', 10);
    let isShuffle = localStorage.getItem('fifa_shuffle') === 'true';
    let savedVol = parseFloat(localStorage.getItem('fifa_volume') || '0.35');
    let shouldPlay = localStorage.getItem('fifa_is_playing') !== 'false';

    const disc = document.getElementById('fDisc');
    const titleEl = document.getElementById('fTitle');
    const selectEl = document.getElementById('fSongSelect');
    const playBtn = document.getElementById('fPlayBtn');
    const prevBtn = document.getElementById('fPrevBtn');
    const nextBtn = document.getElementById('fNextBtn');
    const shuffleBtn = document.getElementById('fShuffleBtn');
    const volInput = document.getElementById('fVolume');

    audio.volume = savedVol;
    volInput.value = savedVol;
    if (isShuffle) shuffleBtn.classList.add('active');

    function loadAndPlay(idx, startAtTime = 0, triggerPlay = true) {
        currentIdx = (idx + fifaTracks.length) % fifaTracks.length;
        const track = fifaTracks[currentIdx];
        audio.src = track.file;
        titleEl.textContent = track.title;
        selectEl.value = currentIdx;
        localStorage.setItem('fifa_track_idx', currentIdx);
        audio.currentTime = startAtTime;
        if (triggerPlay && shouldPlay) {
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
                localStorage.setItem('fifa_is_playing', 'true');
            }).catch(() => {
                playBtn.textContent = '▶️';
                disc.classList.remove('playing');
            });
        } else {
            playBtn.textContent = '▶️';
            disc.classList.remove('playing');
        }
    }

    function playNext() {
        let nextIdx = currentIdx + 1;
        if (isShuffle && fifaTracks.length > 1) {
            do { nextIdx = Math.floor(Math.random() * fifaTracks.length); } while (nextIdx === currentIdx);
        }
        loadAndPlay(nextIdx, 0, true);
    }

    audio.addEventListener('timeupdate', () => localStorage.setItem('fifa_track_time', audio.currentTime));
    audio.addEventListener('ended', playNext);

    playBtn.addEventListener('click', () => {
        if (audio.paused) {
            shouldPlay = true;
            localStorage.setItem('fifa_is_playing', 'true');
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
            }).catch(() => {});
        } else {
            shouldPlay = false;
            localStorage.setItem('fifa_is_playing', 'false');
            audio.pause();
            playBtn.textContent = '▶️';
            disc.classList.remove('playing');
        }
    });

    nextBtn.addEventListener('click', playNext);
    prevBtn.addEventListener('click', () => loadAndPlay(currentIdx - 1, 0, true));
    shuffleBtn.addEventListener('click', () => {
        isShuffle = !isShuffle;
        shuffleBtn.classList.toggle('active', isShuffle);
        localStorage.setItem('fifa_shuffle', isShuffle);
    });
    selectEl.addEventListener('change', (e) => loadAndPlay(parseInt(e.target.value, 10), 0, true));
    volInput.addEventListener('input', (e) => {
        audio.volume = parseFloat(e.target.value);
        localStorage.setItem('fifa_volume', audio.volume);
    });

    loadAndPlay(currentIdx, parseFloat(localStorage.getItem('fifa_track_time') || '0'), shouldPlay);
    document.addEventListener('click', () => {
        if (audio.paused && shouldPlay) {
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
            }).catch(() => {});
        }
    }, { once: true });
})();
