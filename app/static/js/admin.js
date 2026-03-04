(function () {
  'use strict';

  var adminPassword = '';
  var loginSection = document.getElementById('admin-login');
  var contentSection = document.getElementById('admin-content');
  var passwordInput = document.getElementById('admin-password');
  var loginBtn = document.getElementById('admin-login-btn');
  var squareList = document.getElementById('square-list');
  var newSquareInput = document.getElementById('new-square-text');
  var addSquareBtn = document.getElementById('add-square-btn');
  var resetBtn = document.getElementById('reset-btn');

  var statPlayers = document.getElementById('stat-players');
  var statCards = document.getElementById('stat-cards');
  var statWinners = document.getElementById('stat-winners');
  var statSquares = document.getElementById('stat-squares');

  function headers() {
    return { 'Content-Type': 'application/json', 'X-Admin-Password': adminPassword };
  }

  loginBtn.addEventListener('click', tryLogin);
  passwordInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') tryLogin(); });

  async function tryLogin() {
    adminPassword = passwordInput.value.trim();
    if (!adminPassword) return;
    try {
      var res = await fetch('/api/admin/stats', { headers: { 'X-Admin-Password': adminPassword } });
      if (res.ok) {
        loginSection.style.display = 'none';
        contentSection.style.display = 'block';
        loadAll();
      } else {
        adminPassword = '';
        alert('Invalid password');
      }
    } catch (e) {
      alert('Connection error');
    }
  }

  async function loadAll() {
    await Promise.all([loadStats(), loadSquares()]);
  }

  async function loadStats() {
    try {
      var res = await fetch('/api/admin/stats', { headers: { 'X-Admin-Password': adminPassword } });
      if (!res.ok) return;
      var data = await res.json();
      statPlayers.textContent = data.players;
      statCards.textContent = data.cards;
      statWinners.textContent = data.winners;
      statSquares.textContent = data.active_squares;
    } catch (e) { /* ignore */ }
  }

  async function loadSquares() {
    try {
      var res = await fetch('/api/admin/squares', { headers: { 'X-Admin-Password': adminPassword } });
      if (!res.ok) return;
      var data = await res.json();
      var squares = data.squares || [];

      if (squares.length === 0) {
        squareList.innerHTML = '<li class="square-item"><span class="square-text" style="color:var(--color-text-secondary)">No squares yet. Add some!</span></li>';
        return;
      }

      squareList.innerHTML = squares.filter(function (s) { return s.active; }).map(function (s) {
        return '<li class="square-item" data-id="' + s.id + '">' +
          '<span class="square-text">' + escapeHtml(s.text) + '</span>' +
          '<div class="square-actions">' +
          '<button class="btn-small btn-danger delete-btn" data-id="' + s.id + '">Remove</button>' +
          '</div></li>';
      }).join('');

      squareList.querySelectorAll('.delete-btn').forEach(function (btn) {
        btn.addEventListener('click', function () { deleteSquare(parseInt(btn.dataset.id, 10)); });
      });
    } catch (e) { /* ignore */ }
  }

  addSquareBtn.addEventListener('click', addSquare);
  newSquareInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') addSquare(); });

  async function addSquare() {
    var text = newSquareInput.value.trim();
    if (!text) return;
    try {
      var res = await fetch('/api/admin/squares', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ text: text })
      });
      if (res.ok || res.status === 201) {
        newSquareInput.value = '';
        await loadAll();
      }
    } catch (e) { /* ignore */ }
  }

  async function deleteSquare(id) {
    try {
      await fetch('/api/admin/squares/' + id, { method: 'DELETE', headers: headers() });
      await loadAll();
    } catch (e) { /* ignore */ }
  }

  resetBtn.addEventListener('click', async function () {
    if (!confirm('This will clear ALL player cards and marks. Players will get new random cards. Are you sure?')) return;
    try {
      var res = await fetch('/api/admin/reset', { method: 'POST', headers: headers() });
      if (res.ok) {
        alert('Game reset successfully!');
        await loadAll();
      }
    } catch (e) { alert('Reset failed'); }
  });

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
})();
