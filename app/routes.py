import hashlib
import json
import random

from flask import Blueprint, jsonify, make_response, render_template, request

from .config import Config
from .db import execute_db, query_db
from . import limiter

bp = Blueprint('main', __name__)

COOKIE_NAME = 'bingo_player'
COOKIE_MAX_AGE = 12 * 60 * 60  # 12 hours


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_fingerprint() -> str:
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    raw = ip + (request.headers.get('User-Agent', '')) + (request.headers.get('Accept-Language', ''))
    return hashlib.sha256(raw.encode()).hexdigest()


def get_fingerprint() -> str:
    cookie_fp = request.cookies.get(COOKIE_NAME)
    if cookie_fp:
        player = _player_by_fingerprint(cookie_fp)
        if player:
            return cookie_fp
    return _compute_fingerprint()


def _set_player_cookie(response, fingerprint: str):
    response.set_cookie(COOKIE_NAME, fingerprint, max_age=COOKIE_MAX_AGE, httponly=True, samesite='Lax')


def _player_by_fingerprint(fp: str):
    return query_db(
        'SELECT id, name, fingerprint, created_at FROM players WHERE fingerprint = %s',
        (fp,), one=True,
    )


def _serialize_player(p: dict) -> dict:
    return {
        'id': p['id'],
        'name': p['name'],
        'fingerprint': p['fingerprint'],
        'created_at': p['created_at'].isoformat(),
    }


def _check_bingo(marks: set) -> str | None:
    """Check if the given set of marked positions (0-24) forms a bingo.
    Returns the winning pattern string or None."""
    # Rows
    for r in range(5):
        row_positions = {r * 5 + c for c in range(5)}
        if row_positions.issubset(marks):
            return f'row-{r}'
    # Columns
    for c in range(5):
        col_positions = {r * 5 + c for r in range(5)}
        if col_positions.issubset(marks):
            return f'col-{c}'
    # Diagonals
    diag_main = {0, 6, 12, 18, 24}
    if diag_main.issubset(marks):
        return 'diag-main'
    diag_anti = {4, 8, 12, 16, 20}
    if diag_anti.issubset(marks):
        return 'diag-anti'
    return None


def _get_current_player():
    fp = get_fingerprint()
    return _player_by_fingerprint(fp), fp


def _require_admin():
    if not Config.ADMIN_ENABLED:
        return False
    auth = request.headers.get('X-Admin-Password', '')
    if not auth or auth != Config.ADMIN_PASSWORD:
        return False
    return True


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/admin')
def admin_page():
    if not Config.ADMIN_ENABLED:
        return 'Not found', 404
    return render_template('admin.html')


@bp.route('/board')
def board_page():
    return render_template('board.html')


# ---------------------------------------------------------------------------
# Player API
# ---------------------------------------------------------------------------

@bp.route('/api/player-count')
def player_count():
    result = query_db('SELECT COUNT(*) as count FROM players', one=True)
    return jsonify({'count': result['count']})


@bp.route('/api/register', methods=['POST'])
@limiter.limit("10/minute")
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    fp = get_fingerprint()
    existing = _player_by_fingerprint(fp)
    if existing:
        resp = make_response(jsonify(_serialize_player(existing)), 200)
        _set_player_cookie(resp, fp)
        return resp

    player = execute_db(
        'INSERT INTO players (name, fingerprint) VALUES (%s, %s) '
        'RETURNING id, name, fingerprint, created_at',
        (name, fp),
    )
    resp = make_response(jsonify(_serialize_player(player)), 201)
    _set_player_cookie(resp, fp)
    return resp


@bp.route('/api/me')
def me():
    fp = get_fingerprint()
    player = _player_by_fingerprint(fp)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    resp = make_response(jsonify(_serialize_player(player)))
    _set_player_cookie(resp, fp)
    return resp


# ---------------------------------------------------------------------------
# Card API
# ---------------------------------------------------------------------------

@bp.route('/api/card')
def get_card():
    player, fp = _get_current_player()
    if not player:
        return jsonify({'error': 'Player not registered'}), 401

    # Check for existing card
    card = query_db(
        'SELECT id, card_data FROM player_cards WHERE player_id = %s',
        (player['id'],), one=True,
    )

    if not card:
        # Generate a new card
        squares = query_db('SELECT id, text FROM bingo_squares WHERE active = TRUE')
        if len(squares) < 24:
            return jsonify({'error': 'Not enough bingo squares configured (need at least 24)'}), 500

        selected = random.sample(squares, 24)
        # Build 25-element list: 24 squares + free center at position 12
        card_squares = []
        sq_iter = iter(selected)
        for i in range(25):
            if i == 12:
                card_squares.append({'id': 0, 'text': 'FREE'})
            else:
                sq = next(sq_iter)
                card_squares.append({'id': sq['id'], 'text': sq['text']})

        card = execute_db(
            'INSERT INTO player_cards (player_id, card_data) VALUES (%s, %s) '
            'RETURNING id, card_data',
            (player['id'], json.dumps(card_squares)),
        )

    # Get marks
    marks = query_db(
        'SELECT square_position FROM player_marks WHERE player_card_id = %s',
        (card['id'],),
    )
    marked_positions = [m['square_position'] for m in marks]

    # Check if already won
    winner = query_db(
        'SELECT pattern, won_at FROM bingo_winners WHERE player_card_id = %s',
        (card['id'],), one=True,
    )

    card_data = card['card_data']
    if isinstance(card_data, str):
        card_data = json.loads(card_data)

    return jsonify({
        'card_id': card['id'],
        'squares': card_data,
        'marked': marked_positions,
        'won': winner is not None,
        'win_pattern': winner['pattern'] if winner else None,
    })


# ---------------------------------------------------------------------------
# Mark API
# ---------------------------------------------------------------------------

@bp.route('/api/mark', methods=['POST'])
def mark_square():
    player, fp = _get_current_player()
    if not player:
        return jsonify({'error': 'Player not registered'}), 401

    card = query_db(
        'SELECT id FROM player_cards WHERE player_id = %s',
        (player['id'],), one=True,
    )
    if not card:
        return jsonify({'error': 'No card found'}), 404

    data = request.get_json(silent=True) or {}
    position = data.get('position')
    if position is None or not (0 <= position <= 24):
        return jsonify({'error': 'Invalid position (0-24)'}), 400
    if position == 12:
        return jsonify({'error': 'Free square is always marked'}), 400

    action = data.get('action', 'mark')

    if action == 'unmark':
        execute_db(
            'DELETE FROM player_marks WHERE player_card_id = %s AND square_position = %s RETURNING id',
            (card['id'], position),
        )
    else:
        execute_db(
            'INSERT INTO player_marks (player_card_id, square_position) VALUES (%s, %s) '
            'ON CONFLICT (player_card_id, square_position) DO NOTHING RETURNING id',
            (card['id'], position),
        )

    # Return updated marks
    marks = query_db(
        'SELECT square_position FROM player_marks WHERE player_card_id = %s',
        (card['id'],),
    )
    marked_positions = {m['square_position'] for m in marks}
    marked_positions.add(12)  # Free center always marked

    has_bingo = _check_bingo(marked_positions)

    return jsonify({
        'marked': list(marked_positions - {12}),
        'has_bingo': has_bingo is not None,
        'bingo_pattern': has_bingo,
    })


# ---------------------------------------------------------------------------
# Bingo claim API
# ---------------------------------------------------------------------------

@bp.route('/api/bingo', methods=['POST'])
@limiter.limit("5/minute")
def claim_bingo():
    player, fp = _get_current_player()
    if not player:
        return jsonify({'error': 'Player not registered'}), 401

    card = query_db(
        'SELECT id FROM player_cards WHERE player_id = %s',
        (player['id'],), one=True,
    )
    if not card:
        return jsonify({'error': 'No card found'}), 404

    # Check if already won
    existing_win = query_db(
        'SELECT id FROM bingo_winners WHERE player_card_id = %s',
        (card['id'],), one=True,
    )
    if existing_win:
        return jsonify({'error': 'Already claimed bingo'}), 409

    # Verify bingo
    marks = query_db(
        'SELECT square_position FROM player_marks WHERE player_card_id = %s',
        (card['id'],),
    )
    marked_positions = {m['square_position'] for m in marks}
    marked_positions.add(12)

    pattern = _check_bingo(marked_positions)
    if not pattern:
        return jsonify({'error': 'No bingo detected'}), 400

    winner = execute_db(
        'INSERT INTO bingo_winners (player_id, player_card_id, pattern) VALUES (%s, %s, %s) '
        'RETURNING id, won_at',
        (player['id'], card['id'], pattern),
    )

    return jsonify({
        'success': True,
        'pattern': pattern,
        'won_at': winner['won_at'].isoformat(),
        'player_name': player['name'],
    })


# ---------------------------------------------------------------------------
# Winners feed
# ---------------------------------------------------------------------------

@bp.route('/api/winners')
def winners():
    rows = query_db(
        'SELECT bw.pattern, bw.won_at, p.name '
        'FROM bingo_winners bw '
        'JOIN players p ON p.id = bw.player_id '
        'ORDER BY bw.won_at ASC '
        'LIMIT 50',
    )
    return jsonify({
        'winners': [
            {
                'name': r['name'],
                'pattern': r['pattern'],
                'won_at': r['won_at'].isoformat(),
            }
            for r in rows
        ],
        'count': len(rows),
    })


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------

@bp.route('/api/admin/squares')
@limiter.limit("5/minute")
def list_squares():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    squares = query_db('SELECT id, text, active FROM bingo_squares ORDER BY id')
    return jsonify({'squares': [{'id': s['id'], 'text': s['text'], 'active': s['active']} for s in squares]})


@bp.route('/api/admin/squares', methods=['POST'])
@limiter.limit("5/minute")
def add_square():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    sq = execute_db(
        'INSERT INTO bingo_squares (text) VALUES (%s) '
        'ON CONFLICT (text) DO UPDATE SET active = TRUE '
        'RETURNING id, text, active',
        (text,),
    )
    return jsonify(sq), 201


@bp.route('/api/admin/squares/<int:square_id>', methods=['DELETE'])
@limiter.limit("5/minute")
def delete_square(square_id):
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    execute_db('UPDATE bingo_squares SET active = FALSE WHERE id = %s RETURNING id', (square_id,))
    return jsonify({'success': True})


@bp.route('/api/admin/stats')
@limiter.limit("5/minute")
def admin_stats():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    players = query_db('SELECT COUNT(*) as count FROM players', one=True)
    cards = query_db('SELECT COUNT(*) as count FROM player_cards', one=True)
    winners_count = query_db('SELECT COUNT(*) as count FROM bingo_winners', one=True)
    squares = query_db('SELECT COUNT(*) as count FROM bingo_squares WHERE active = TRUE', one=True)
    return jsonify({
        'players': players['count'],
        'cards': cards['count'],
        'winners': winners_count['count'],
        'active_squares': squares['count'],
    })


@bp.route('/api/admin/reset', methods=['POST'])
@limiter.limit("2/minute")
def reset_game():
    if not _require_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    execute_db('DELETE FROM bingo_winners RETURNING id')
    execute_db('DELETE FROM player_marks RETURNING id')
    execute_db('DELETE FROM player_cards RETURNING id')

    return jsonify({'success': True, 'message': 'Game reset. All cards and marks cleared.'})
