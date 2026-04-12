(function () {
  'use strict';

  // --- State ---
  var cardId = null;
  var squares = [];
  var markedSet = new Set();
  var hasBingo = false;
  var hasWon = false;
  var playerRegistered = false;

  // --- DOM refs ---
  var board = document.getElementById('bingo-board');
  var modal = document.getElementById('registration-modal');
  var nameInput = document.getElementById('player-name-input');
  var registerBtn = document.getElementById('register-btn');
  var playerNameEl = document.getElementById('player-name');
  var toastContainer = document.getElementById('toast-container');
  var bingoBtn = document.getElementById('bingo-btn');
  var wonMsg = document.getElementById('won-msg');
  var winnersContent = document.getElementById('winners-content');
  var confettiCanvas = document.getElementById('confetti-canvas');

  // --- Init ---
  async function init() {
    try {
      var res = await fetch('/api/me');
      if (res.ok) {
        var data = await res.json();
        playerRegistered = true;
        playerNameEl.textContent = data.name || '';
        await loadCard();
        startWinnersPolling();
      } else {
        showModal();
      }
    } catch (e) {
      showModal();
    }
  }

  // --- Modal ---
  function showModal() {
    modal.style.display = 'flex';
    setTimeout(function () { nameInput.focus(); }, 100);
  }

  function hideModal() { modal.style.display = 'none'; }

  registerBtn.addEventListener('click', handleRegister);
  nameInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') handleRegister();
  });

  async function handleRegister() {
    var name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    try {
      var res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
      });
      if (res.ok || res.status === 201) {
        var data = await res.json();
        playerRegistered = true;
        playerNameEl.textContent = data.name || name;
        hideModal();
        await loadCard();
        startWinnersPolling();
      } else {
        var err = await res.json().catch(function () { return {}; });
        showToast(err.error || 'Registration failed', 3000);
      }
    } catch (e) {
      showToast('Connection error', 3000);
    }
  }

  // --- Card ---
  async function loadCard() {
    try {
      var res = await fetch('/api/card');
      if (!res.ok) {
        var err = await res.json().catch(function () { return {}; });
        showToast(err.error || 'Failed to load card', 3000);
        return;
      }
      var data = await res.json();
      cardId = data.card_id;
      squares = data.squares;
      markedSet = new Set(data.marked);
      markedSet.add(12); // Free center
      hasWon = data.won;
      renderBoard();
      updateBingoButton();
      if (hasWon) {
        wonMsg.textContent = '🎉 You got BINGO!';
        wonMsg.style.display = 'block';
        bingoBtn.style.display = 'none';
      }
    } catch (e) {
      showToast('Failed to load card', 3000);
    }
  }

  function renderBoard() {
    board.innerHTML = '';
    for (var i = 0; i < 25; i++) {
      var cell = document.createElement('div');
      cell.className = 'bingo-cell';
      cell.dataset.position = i;

      if (i === 12) {
        cell.textContent = '⭐ FREE';
        cell.classList.add('free', 'marked');
      } else {
        cell.textContent = squares[i] ? squares[i].text : '';
        if (markedSet.has(i)) cell.classList.add('marked');
        cell.addEventListener('click', handleCellClick);
      }

      board.appendChild(cell);
    }
  }

  async function handleCellClick(e) {
    if (hasWon) return;
    var cell = e.currentTarget;
    var pos = parseInt(cell.dataset.position, 10);
    var isMarked = markedSet.has(pos);
    var action = isMarked ? 'unmark' : 'mark';

    // Optimistic update
    if (isMarked) {
      markedSet.delete(pos);
      cell.classList.remove('marked');
    } else {
      markedSet.add(pos);
      cell.classList.add('marked');
    }

    try {
      var res = await fetch('/api/mark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: pos, action: action })
      });
      if (res.ok) {
        var data = await res.json();
        markedSet = new Set(data.marked);
        markedSet.add(12);
        hasBingo = data.has_bingo;
        updateBingoButton();
        // Re-render to sync
        syncCellStates();
      } else {
        // Revert optimistic update
        if (action === 'mark') {
          markedSet.delete(pos);
          cell.classList.remove('marked');
        } else {
          markedSet.add(pos);
          cell.classList.add('marked');
        }
      }
    } catch (e) {
      showToast('Connection error', 2000);
    }
  }

  function syncCellStates() {
    var cells = board.querySelectorAll('.bingo-cell');
    cells.forEach(function (cell) {
      var pos = parseInt(cell.dataset.position, 10);
      if (pos === 12) return;
      if (markedSet.has(pos)) cell.classList.add('marked');
      else cell.classList.remove('marked');
    });
  }

  function updateBingoButton() {
    if (hasWon) {
      bingoBtn.style.display = 'none';
      return;
    }
    bingoBtn.style.display = 'inline-block';
    bingoBtn.disabled = !hasBingo;
  }

  // --- Bingo claim ---
  bingoBtn.addEventListener('click', async function () {
    if (!hasBingo || hasWon) return;
    try {
      var res = await fetch('/api/bingo', { method: 'POST' });
      if (res.ok) {
        var data = await res.json();
        hasWon = true;
        wonMsg.textContent = '🎉 You got BINGO!';
        wonMsg.style.display = 'block';
        bingoBtn.style.display = 'none';
        launchConfetti();
        showToast('🎉 BINGO! Congratulations!', 5000);
        loadWinners();
      }else {
        var err = await res.json().catch(function () { return {}; });
        showToast(err.error || 'Not a valid bingo', 3000);
      }
    } catch (e) {
      showToast('Connection error', 3000);
    }
  });

  // --- Winners feed ---
  var lastWinnerCount = 0;

  async function loadWinners() {
    try {
      var res = await fetch('/api/winners');
      if (!res.ok) return;
      var data = await res.json();
      var winners = data.winners || [];

      if (winners.length === 0) {
        winnersContent.innerHTML = '<span class="winners-ticker-empty">No winners yet — be the first!</span>';
      } else {
        winnersContent.textContent = winners.map(function (w) {
          return '🎉 ' + w.name;
        }).join('  ·  ');
      }

      // Toast if new winner appeared
      if (winners.length > lastWinnerCount && lastWinnerCount > 0) {
        var newest = winners[winners.length - 1];
        showToast('🎉 ' + newest.name + ' got BINGO!', 4000);
      }
      lastWinnerCount = winners.length;
    } catch (e) { /* ignore */ }
  }

  function startWinnersPolling() {
    loadWinners();
    setInterval(loadWinners, 5000);
  }

  // --- Confetti ---
  function launchConfetti() {
    var canvas = confettiCanvas;
    var ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    canvas.style.display = 'block';

    var particles = [];
    var colors = ['#538d4e', '#b59f3b', '#ff6b6b', '#4ecdc4', '#ffe66d', '#ff8a5c', '#a78bfa', '#f472b6'];
    var gravity = 0.12;
    var drag = 0.98;

    for (var i = 0; i < 200; i++) {
      var angle = Math.random() * Math.PI * 2;
      var speed = 5 + Math.random() * 10;
      particles.push({
        x: canvas.width / 2 + (Math.random() - 0.5) * 300,
        y: canvas.height / 2 - 50,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: 4 + Math.random() * 8,
        rotation: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 12,
        life: 1,
        decay: 0.002 + Math.random() * 0.004,
        shape: Math.random() > 0.5 ? 'rect' : 'circle',
      });
    }

    var startTime = Date.now();
    var maxDuration = 4000;

    function animate() {
      var elapsed = Date.now() - startTime;
      if (elapsed > maxDuration || particles.every(function (p) { return p.life <= 0; })) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        canvas.style.display = 'none';
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(function (p) {
        if (p.life <= 0) return;
        p.vy += gravity;
        p.vx *= drag;
        p.vy *= drag;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotSpeed;
        p.life -= p.decay;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.fillStyle = p.color;

        if (p.shape === 'rect') {
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      });

      requestAnimationFrame(animate);
    }

    animate();
  }

  // --- Toast ---
  function showToast(message, duration) {
    duration = duration || 2000;
    var toast = document.createElement('div');
    toast.classList.add('toast');
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(function () {
      toast.classList.add('fade-out');
      toast.addEventListener('animationend', function () { toast.remove(); });
    }, duration);
  }

  // --- Start ---
  init();
})();
