"""
Chess Learning Coach Pro - Ultimate Edition
Complete interactive analysis with AI tutor, variation training, and ELO estimation

Requirements:
pip install streamlit python-chess plotly pandas numpy
System: Stockfish chess engine (installed via packages.txt)
"""

import streamlit as st
import chess
import chess.engine
import chess.pgn
import chess.svg
from io import StringIO
import plotly.graph_objects as go
import pandas as pd
import base64
import math

# Page configuration
st.set_page_config(
    page_title="Chess Coach Pro - Ultimate Edition",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'game_analysis' not in st.session_state:
    st.session_state.game_analysis = []
if 'current_move_index' not in st.session_state:
    st.session_state.current_move_index = 0
if 'position_history' not in st.session_state:
    st.session_state.position_history = []
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'white_stats' not in st.session_state:
    st.session_state.white_stats = {}
if 'black_stats' not in st.session_state:
    st.session_state.black_stats = {}
if 'show_hints' not in st.session_state:
    st.session_state.show_hints = True
if 'tutor_mode' not in st.session_state:
    st.session_state.tutor_mode = True
if 'opening_database' not in st.session_state:
    st.session_state.opening_database = {}
if 'variation_training' not in st.session_state:
    st.session_state.variation_training = False
if 'training_moves' not in st.session_state:
    st.session_state.training_moves = []
if 'phase_ratings' not in st.session_state:
    st.session_state.phase_ratings = {}
if 'estimated_elo' not in st.session_state:
    st.session_state.estimated_elo = {}

# Enhanced CSS
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    .stApp { background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%); }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Move Classifications */
    .move-brilliant { background: rgba(147, 51, 234, 0.2); border: 1px solid rgba(147, 51, 234, 0.5); color: #c084fc; }
    .move-great { background: rgba(16, 185, 129, 0.3); border: 1px solid rgba(16, 185, 129, 0.6); color: #34d399; }
    .move-best { background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.5); color: #10b981; }
    .move-excellent { background: rgba(59, 130, 246, 0.3); border: 1px solid rgba(59, 130, 246, 0.6); color: #60a5fa; }
    .move-good { background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.5); color: #3b82f6; }
    .move-theory { background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.5); color: #a855f7; }
    .move-inaccuracy { background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.5); color: #f59e0b; }
    .move-mistake { background: rgba(249, 115, 22, 0.2); border: 1px solid rgba(249, 115, 22, 0.5); color: #f97316; }
    .move-blunder { background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #ef4444; }
    
    .move-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    /* Tutor Box */
    .tutor-box {
        background: linear-gradient(135deg, rgba(147, 51, 234, 0.15) 0%, rgba(102, 126, 234, 0.15) 100%);
        border: 2px solid rgba(147, 51, 234, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .tutor-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* ELO Badge */
    .elo-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        font-size: 1.5rem;
        font-weight: bold;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Phase Rating Cards */
    .phase-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .phase-opening { border-left-color: #667eea; }
    .phase-middlegame { border-left-color: #f093fb; }
    .phase-endgame { border-left-color: #4facfe; }
    
    /* Variation Training */
    .variation-panel {
        background: rgba(45, 45, 68, 0.6);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .board-container {
        background: rgba(45, 45, 68, 0.6);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        text-align: center;
    }
    
    .eval-bar-container {
        height: 400px;
        width: 40px;
        background: #1a1a2e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
    }
    
    .eval-bar-white {
        background: linear-gradient(180deg, #f0f0f0 0%, #d0d0d0 100%);
        transition: height 0.3s ease;
    }
    
    .player-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        border-left: 5px solid;
    }
    
    .player-card.white { border-left-color: #f0f0f0; }
    .player-card.black { border-left-color: #2d2d44; }
    
    .analysis-panel {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Opening Theory Database
OPENING_DATABASE = {
    'e2e4 e7e5 g1f3 b8c6 f1b5': {'name': 'Ruy Lopez', 'eco': 'C60-C99', 'rating': 9.5},
    'e2e4 c7c5': {'name': 'Sicilian Defense', 'eco': 'B20-B99', 'rating': 9.3},
    'e2e4 e7e5 g1f3 b8c6 f1c4': {'name': 'Italian Game', 'eco': 'C50-C54', 'rating': 9.0},
    'd2d4 d7d5 c2c4': {'name': "Queen's Gambit", 'eco': 'D00-D69', 'rating': 9.4},
    'd2d4 g8f6 c2c4 e7e6': {'name': 'Nimzo-Indian', 'eco': 'E20-E59', 'rating': 9.2},
    'e2e4 e7e6': {'name': 'French Defense', 'eco': 'C00-C19', 'rating': 8.8},
    'e2e4 c7c6': {'name': 'Caro-Kann Defense', 'eco': 'B10-B19', 'rating': 8.9},
    'c2c4': {'name': 'English Opening', 'eco': 'A10-A39', 'rating': 8.7},
}

# Stockfish Engine Setup
@st.cache_resource
def initialize_engine():
    """Initialize Stockfish engine"""
    try:
        possible_paths = [
            '/usr/games/stockfish',
            '/usr/local/bin/stockfish',
            'stockfish',
            '/opt/homebrew/bin/stockfish',
            'C:\\Program Files\\Stockfish\\stockfish.exe'
        ]
        
        for path in possible_paths:
            try:
                engine = chess.engine.SimpleEngine.popen_uci(path)
                return engine
            except:
                continue
        
        st.warning("⚠️ Stockfish not found. Limited analysis mode.")
        return None
    except Exception as e:
        st.error(f"Error initializing engine: {e}")
        return None

if st.session_state.engine is None:
    st.session_state.engine = initialize_engine()

def render_board_svg(board, size=400, highlighted_squares=None, arrows=None, last_move=None):
    """Render chess board"""
    try:
        squares_to_highlight = highlighted_squares or []
        if last_move:
            squares_to_highlight.extend([last_move.from_square, last_move.to_square])
        
        if arrows:
            svg = chess.svg.board(board, size=size, squares=squares_to_highlight, arrows=arrows)
        elif squares_to_highlight:
            svg = chess.svg.board(board, size=size, squares=squares_to_highlight)
        else:
            svg = chess.svg.board(board, size=size)
        
        b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; height: auto;"/>'
    except:
        return "<p>Error rendering board</p>"

def analyze_position(board, depth=18):
    """Analyze position with Stockfish"""
    if st.session_state.engine is None:
        return {'evaluation': 0, 'best_move': None, 'mate_in': None, 'top_moves': []}
    
    try:
        info = st.session_state.engine.analyse(board, chess.engine.Limit(depth=depth), multipv=3)
        
        main_info = info[0] if isinstance(info, list) else info
        score = main_info['score'].relative
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() is not None else 0
        best_move = main_info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        
        top_moves = []
        if isinstance(info, list):
            for line in info[:3]:
                move = line.get('pv', [None])[0]
                if move:
                    move_score = line['score'].relative
                    move_eval = move_score.score(mate_score=10000) / 100.0 if move_score.score() is not None else 0
                    top_moves.append({
                        'move': move.uci(),
                        'san': board.san(move),
                        'eval': move_eval,
                        'pv': [m.uci() for m in line.get('pv', [])[:5]]
                    })
        
        return {
            'evaluation': evaluation,
            'best_move': best_move.uci() if best_move else None,
            'best_move_san': board.san(best_move) if best_move else None,
            'mate_in': mate_in,
            'top_moves': top_moves
        }
    except:
        return {'evaluation': 0, 'best_move': None, 'mate_in': None, 'top_moves': []}

def detect_opening(move_sequence):
    """Detect opening from move sequence"""
    move_string = ' '.join(move_sequence[:10])
    
    for pattern, info in OPENING_DATABASE.items():
        pattern_moves = pattern.split()
        if len(move_sequence) >= len(pattern_moves):
            if all(move_sequence[i] == pattern_moves[i] for i in range(len(pattern_moves))):
                return info
    
    return {'name': 'Unknown Opening', 'eco': 'A00', 'rating': 5.0}

def classify_move_enhanced(eval_before, eval_after, is_best_move, player_color, is_book_move=False):
    """Enhanced move classification with 9 categories"""
    if player_color == chess.BLACK:
        eval_before = -eval_before
        eval_after = -eval_after
    
    centipawn_loss = (eval_before - eval_after) * 100
    
    # Theory/Book move
    if is_book_move:
        return {
            'type': 'theory',
            'symbol': '⚐',
            'cp_loss': 0,
            'feedback': '📚 Theory Move',
            'color': '#a855f7',
            'explanation': 'This is a well-known theoretical move from opening databases.'
        }
    
    # Brilliant move
    if centipawn_loss < -50 and not is_best_move:
        return {
            'type': 'brilliant',
            'symbol': '‼',
            'cp_loss': int(centipawn_loss),
            'feedback': '✨ Brilliant!!',
            'color': '#9333ea',
            'explanation': 'An exceptional move that requires deep calculation! This shows outstanding tactical vision.'
        }
    
    # Great move
    if centipawn_loss < -20 and not is_best_move:
        return {
            'type': 'great',
            'symbol': '⁂',
            'cp_loss': int(centipawn_loss),
            'feedback': '🌟 Great Move!',
            'color': '#34d399',
            'explanation': 'A very strong move that significantly improves your position beyond expectations.'
        }
    
    # Best move
    if is_best_move or centipawn_loss < 5:
        return {
            'type': 'best',
            'symbol': '!',
            'cp_loss': int(centipawn_loss),
            'feedback': '✓ Best Move',
            'color': '#10b981',
            'explanation': 'Perfect! This is the engine\'s top choice. You\'re playing at maximum strength.'
        }
    
    # Excellent move
    if centipawn_loss < 15:
        return {
            'type': 'excellent',
            'symbol': '⁺',
            'cp_loss': int(centipawn_loss),
            'feedback': '⭐ Excellent',
            'color': '#60a5fa',
            'explanation': 'Very strong move! Practically as good as the best move.'
        }
    
    # Good move
    if centipawn_loss < 40:
        return {
            'type': 'good',
            'symbol': '',
            'cp_loss': int(centipawn_loss),
            'feedback': '✔ Good Move',
            'color': '#3b82f6',
            'explanation': 'Solid play. This maintains your position without significant loss.'
        }
    
    # Inaccuracy
    if centipawn_loss < 90:
        return {
            'type': 'inaccuracy',
            'symbol': '?!',
            'cp_loss': int(centipawn_loss),
            'feedback': '⚠ Inaccuracy',
            'color': '#f59e0b',
            'explanation': 'Not the best choice. Look for more active moves or better piece placement.'
        }
    
    # Mistake
    if centipawn_loss < 250:
        return {
            'type': 'mistake',
            'symbol': '?',
            'cp_loss': int(centipawn_loss),
            'feedback': '❌ Mistake',
            'color': '#f97316',
            'explanation': 'This weakens your position significantly. Always check tactics before moving!'
        }
    
    # Blunder
    return {
        'type': 'blunder',
        'symbol': '??',
        'cp_loss': int(centipawn_loss),
        'feedback': '💥 Blunder!!',
        'color': '#ef4444',
        'explanation': 'Critical error! This loses material or a winning position. Review what you missed.'
    }

def generate_tutor_explanation(move_data, position_board):
    """Generate AI tutor explanation for the move"""
    move_type = move_data['classification']['type']
    
    tutor_messages = {
        'brilliant': f"""
        🎓 **Outstanding Play!**
        
        You found {move_data['san']}, a brilliant move! This required exceptional calculation.
        
        **Why it's brilliant:**
        - Improves position evaluation by {abs(move_data['classification']['cp_loss'])} centipawns
        - Shows deep tactical understanding
        - May involve a surprising sacrifice or unexpected maneuver
        
        **Learning:** Study this position! Brilliant moves are rare and showcase mastery.
        """,
        
        'great': f"""
        🎓 **Excellent Discovery!**
        
        {move_data['san']} is a great move that significantly strengthens your position.
        
        **Why it's great:**
        - Better than the obvious moves
        - Shows strong positional understanding
        - Gains {abs(move_data['classification']['cp_loss'])} centipawns advantage
        
        **Learning:** You're thinking beyond the obvious - keep this up!
        """,
        
        'best': f"""
        🎓 **Perfect Execution!**
        
        {move_data['san']} is the engine's top choice. Excellent!
        
        **Why it's best:**
        - Optimal piece placement
        - Maintains or increases advantage
        - No better alternative exists
        
        **Learning:** Playing best moves consistently leads to higher ratings.
        """,
        
        'theory': f"""
        🎓 **Following Theory**
        
        {move_data['san']} is a known theoretical move.
        
        **Opening principles applied:**
        - Control the center
        - Develop pieces efficiently
        - Castle early for king safety
        
        **Learning:** Study the key ideas behind this opening, not just memorize moves.
        """,
        
        'inaccuracy': f"""
        🎓 **Could Be Better**
        
        {move_data['san']} is playable but not optimal. You lose {move_data['classification']['cp_loss']} centipawns.
        
        **Better was:** {move_data.get('best_move_san', 'N/A')}
        
        **Why?**
        - More active piece placement
        - Better control of key squares
        - Maintains more pressure
        
        **Learning:** Take an extra 10 seconds to check if pieces can be more active.
        """,
        
        'mistake': f"""
        🎓 **Needs Improvement**
        
        {move_data['san']} weakens your position by {move_data['classification']['cp_loss']} centipawns.
        
        **Better was:** {move_data.get('best_move_san', 'N/A')}
        
        **What went wrong?**
        - Tactical oversight
        - Weak square created
        - Piece becomes passive or trapped
        
        **Learning:** Before each move, ask:
        1. Are my pieces safe?
        2. Am I creating weaknesses?
        3. What's my opponent's threat?
        """,
        
        'blunder': f"""
        🎓 **Critical Learning Moment**
        
        {move_data['san']} is a serious error, losing {move_data['classification']['cp_loss']} centipawns.
        
        **You should have played:** {move_data.get('best_move_san', 'N/A')}
        
        **What you missed:**
        - Tactical blow (check, capture, or threat)
        - Undefended piece
        - Mating attack or material loss
        
        **Essential Checklist (use EVERY move):**
        1. ✓ Check for opponent's checks
        2. ✓ Check for opponent's captures
        3. ✓ Check for opponent's threats
        4. ✓ Verify all pieces are defended
        
        **Learning:** Slow down! Blunders are almost always preventable with careful checking.
        """,
    }
    
    return tutor_messages.get(move_type, move_data['classification']['explanation'])

def estimate_elo(accuracy, acpl, phase_performance):
    """Estimate player ELO based on performance metrics"""
    # Base calculation
    base_elo = 400  # Starting point
    
    # Accuracy contribution (0-1000 points)
    accuracy_elo = (accuracy / 100) * 1000
    
    # ACPL contribution (lower is better, 0-600 points)
    acpl_elo = max(0, 600 - (acpl * 3))
    
    # Phase performance (0-400 points)
    phase_elo = (
        phase_performance.get('opening', 0) * 1.2 +
        phase_performance.get('middlegame', 0) * 1.5 +
        phase_performance.get('endgame', 0) * 1.3
    ) / 4
    
    estimated = base_elo + accuracy_elo + acpl_elo + phase_elo
    
    # Clamp between 400-3000
    return max(400, min(3000, int(estimated)))

def calculate_phase_ratings(analysis):
    """Calculate performance ratings for each game phase"""
    opening_moves = [m for m in analysis if m['move_number'] <= 12]
    middlegame_moves = [m for m in analysis if 12 < m['move_number'] <= 40]
    endgame_moves = [m for m in analysis if m['move_number'] > 40]
    
    def phase_score(moves):
        if not moves:
            return {'score': 0, 'accuracy': 0, 'rating': 'N/A'}
        
        good_moves = sum(1 for m in moves if m['classification']['type'] in ['brilliant', 'great', 'best', 'excellent', 'good', 'theory'])
        accuracy = (good_moves / len(moves)) * 100
        
        # Rating scale
        if accuracy >= 95:
            rating = 'Masterful'
        elif accuracy >= 85:
            rating = 'Excellent'
        elif accuracy >= 75:
            rating = 'Good'
        elif accuracy >= 60:
            rating = 'Average'
        else:
            rating = 'Needs Work'
        
        return {
            'total_moves': len(moves),
            'good_moves': good_moves,
            'accuracy': accuracy,
            'rating': rating,
            'score': accuracy
        }
    
    return {
        'opening': phase_score(opening_moves),
        'middlegame': phase_score(middlegame_moves),
        'endgame': phase_score(endgame_moves) if endgame_moves else {'score': 0, 'accuracy': 0, 'rating': 'N/A', 'total_moves': 0}
    }

def analyze_game(pgn_string, progress_callback=None):
    """Analyze complete game"""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        return None
    
    board = game.board()
    analysis = []
    position_history = [board.copy()]
    move_sequence = []
    move_number = 1
    
    total_moves = len(list(game.mainline_moves()))
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    
    for idx, move in enumerate(game.mainline_moves()):
        if progress_callback:
            progress_callback((idx + 1) / total_moves)
        
        move_sequence.append(move.uci())
        
        # Detect if it's a theory move
        opening_info = detect_opening(move_sequence)
        is_theory = (idx < 10 and opening_info['name'] != 'Unknown Opening')
        
        # Analyze before move
        eval_before = analyze_position(board, depth=15)
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        player_color = board.turn
        san_move = board.san(move)
        
        # Make move
        board.push(move)
        position_history.append(board.copy())
        
        # Analyze after move
        eval_after = analyze_position(board, depth=15)
        
        # Classify move
        classification = classify_move_enhanced(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color,
            is_theory
        )
        
        analysis.append({
            'move_number': move_number,
            'move': move.uci(),
            'san': san_move,
            'player': 'White' if player_color == chess.WHITE else 'Black',
            'eval_before': eval_before['evaluation'],
            'eval_after': eval_after['evaluation'],
            'best_move': best_move,
            'best_move_san': eval_before.get('best_move_san'),
            'top_moves': eval_before.get('top_moves', []),
            'classification': classification,
            'fen': board.fen(),
            'is_theory': is_theory
        })
        
        move_number += 1
    
    # Detect opening
    opening_info = detect_opening(move_sequence)
    
    return analysis, position_history, opening_info

def calculate_player_stats(analysis, player):
    """Calculate enhanced statistics"""
    player_moves = [m for m in analysis if m['player'] == player]
    
    if not player_moves:
        return {}
    
    move_types = {
        'brilliant': 0, 'great': 0, 'best': 0, 'excellent': 0,
        'good': 0, 'theory': 0, 'inaccuracy': 0, 'mistake': 0, 'blunder': 0
    }
    
    total_cp_loss = 0
    
    for move in player_moves:
        move_type = move['classification']['type']
        move_types[move_type] = move_types.get(move_type, 0) + 1
        if move['classification']['cp_loss'] > 0:
            total_cp_loss += move['classification']['cp_loss']
    
    excellent_moves = move_types['brilliant'] + move_types['great'] + move_types['best'] + move_types['excellent'] + move_types['good'] + move_types['theory']
    accuracy = (excellent_moves / len(player_moves) * 100) if player_moves else 0
    acpl = total_cp_loss / len(player_moves) if player_moves else 0
    
    return {
        'total_moves': len(player_moves),
        'move_types': move_types,
        'accuracy': accuracy,
        'acpl': acpl
    }

def render_evaluation_bar(eval_score, mate_in=None, height=400):
    """Render evaluation bar"""
    if mate_in is not None:
        white_height = 100 if mate_in > 0 else 0
    else:
        clamped = max(-10, min(10, eval_score))
        white_height = 50 + (clamped / 20 * 50)
    
    eval_display = f"M{abs(mate_in)}" if mate_in else f"{eval_score:+.1f}"
    
    return f"""
    <div style="position: relative;">
        <div class="eval-bar-container" style="height: {height}px;">
            <div class="eval-bar-white" style="height: {white_height}%"></div>
        </div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: rgba(0,0,0,0.8); color: white; padding: 0.5rem; 
                    border-radius: 6px; font-weight: bold; font-size: 1rem;">
            {eval_display}
        </div>
    </div>
    """

# Main App
st.markdown('<div class="main-header">♟️ Chess Coach Pro - Ultimate Edition</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; color: #a0a0c0; font-size: 1.1rem; margin-bottom: 2rem;">AI Tutor • Variation Training • ELO Estimation • Phase Analysis</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Controls")
    
    if st.session_state.game_analysis:
        st.success(f"✅ Game Loaded ({len(st.session_state.game_analysis)} moves)")
        
        if st.button("🔄 Load New Game", use_container_width=True):
            st.session_state.game_analysis = []
            st.session_state.current_move_index = 0
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    st.session_state.show_hints = st.checkbox("Show Move Hints", value=True)
    st.session_state.tutor_mode = st.checkbox("AI Tutor Mode", value=True)
    show_alternatives = st.checkbox("Show Variations", value=True)
    
    st.markdown("---")
    
    st.markdown("### 🎓 Training Mode")
    if st.button("📚 Practice Variations", use_container_width=True):
        st.session_state.variation_training = True
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Engine")
    if st.session_state.engine:
        st.success("✅ Stockfish Active")
    else:
        st.warning("⚠️ Limited Mode")

# Main Content
if not st.session_state.game_analysis:
    st.markdown("## 📊 Upload Your Game")
    
    tab1, tab2 = st.tabs(["📝 Paste PGN", "📁 Upload File"])
    
    with tab1:
        pgn_input = st.text_area("Paste PGN", height=200, placeholder="""[Event "Rated Game"]
[White "Player1"]
[Black "Player2"]

1. e4 e5 2. Nf3 Nc6...""")
        
        if st.button("🔍 Analyze", type="primary", use_container_width=True):
            if pgn_input:
                with st.spinner("🧠 Analyzing with Stockfish..."):
                    progress_bar = st.progress(0)
                    
                    def update_progress(p):
                        progress_bar.progress(p)
                    
                    result = analyze_game(pgn_input, progress_callback=update_progress)
                    
                    if result:
                        analysis, position_history, opening_info = result
                        st.session_state.game_analysis = analysis
                        st.session_state.position_history = position_history
                        st.session_state.opening_info = opening_info
                        st.session_state.current_move_index = 0
                        
                        # Calculate stats
                        st.session_state.white_stats = calculate_player_stats(analysis, 'White')
                        st.session_state.black_stats = calculate_player_stats(analysis, 'Black')
                        
                        # Phase ratings
                        st.session_state.phase_ratings = calculate_phase_ratings(analysis)
                        
                        # ELO estimation
                        white_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        black_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        
                        st.session_state.estimated_elo = {
                            'white': estimate_elo(
                                st.session_state.white_stats['accuracy'],
                                st.session_state.white_stats['acpl'],
                                white_phase
                            ),
                            'black': estimate_elo(
                                st.session_state.black_stats['accuracy'],
                                st.session_state.black_stats['acpl'],
                                black_phase
                            )
                        }
                        
                        progress_bar.empty()
                        st.success("✅ Analysis Complete!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid PGN")
    
    with tab2:
        uploaded_file = st.file_uploader("Choose PGN", type=['pgn'])
        if uploaded_file:
            pgn_content = uploaded_file.read().decode('utf-8')
            if st.button("🔍 Analyze Upload", type="primary"):
                with st.spinner("🧠 Analyzing..."):
                    progress_bar = st.progress(0)
                    
                    def update_progress(p):
                        progress_bar.progress(p)
                    
                    result = analyze_game(pgn_content, progress_callback=update_progress)
                    
                    if result:
                        analysis, position_history, opening_info = result
                        st.session_state.game_analysis = analysis
                        st.session_state.position_history = position_history
                        st.session_state.opening_info = opening_info
                        st.session_state.current_move_index = 0
                        
                        st.session_state.white_stats = calculate_player_stats(analysis, 'White')
                        st.session_state.black_stats = calculate_player_stats(analysis, 'Black')
                        st.session_state.phase_ratings = calculate_phase_ratings(analysis)
                        
                        white_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        black_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        
                        st.session_state.estimated_elo = {
                            'white': estimate_elo(st.session_state.white_stats['accuracy'], st.session_state.white_stats['acpl'], white_phase),
                            'black': estimate_elo(st.session_state.black_stats['accuracy'], st.session_state.black_stats['acpl'], black_phase)
                        }
                        
                        progress_bar.empty()
                        st.success("✅ Complete!")
                        st.rerun()

else:
    # Display Analysis
    analysis = st.session_state.game_analysis
    position_history = st.session_state.position_history
    current_idx = st.session_state.current_move_index
    opening_info = st.session_state.opening_info
    
    current_board = position_history[current_idx] if current_idx < len(position_history) else position_history[-1]
    current_move = analysis[current_idx - 1] if current_idx > 0 and current_idx <= len(analysis) else None
    
    # Top Section - ELO & Opening
    st.markdown("## 🏆 Match Overview")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("### ⚪ White")
        st.markdown(f'<div class="elo-badge">{st.session_state.estimated_elo["white"]}</div>', unsafe_allow_html=True)
        st.caption("Estimated ELO")
        st.metric("Accuracy", f"{st.session_state.white_stats['accuracy']:.1f}%")
        st.metric("Avg CP Loss", f"{st.session_state.white_stats['acpl']:.0f}")
    
    with col2:
        st.markdown(f"### 📚 {opening_info['name']}")
        st.markdown(f"**ECO Code:** {opening_info['eco']}")
        
        opening_rating = opening_info.get('rating', 5.0)
        stars = "⭐" * int(opening_rating)
        st.markdown(f"**Opening Strength:** {stars} ({opening_rating}/10)")
        
        # Phase Ratings
        st.markdown("### 📊 Phase Performance")
        col_a, col_b, col_c = st.columns(3)
        
        phase_ratings = st.session_state.phase_ratings
        
        with col_a:
            st.markdown(f"""
            <div class="phase-card phase-opening">
                <h4>🎬 Opening</h4>
                <p><strong>{phase_ratings['opening']['rating']}</strong></p>
                <small>{phase_ratings['opening']['accuracy']:.1f}% accuracy</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f"""
            <div class="phase-card phase-middlegame">
                <h4>⚔️ Middlegame</h4>
                <p><strong>{phase_ratings['middlegame']['rating']}</strong></p>
                <small>{phase_ratings['middlegame']['accuracy']:.1f}% accuracy</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_c:
            if phase_ratings['endgame']['total_moves'] > 0:
                st.markdown(f"""
                <div class="phase-card phase-endgame">
                    <h4>👑 Endgame</h4>
                    <p><strong>{phase_ratings['endgame']['rating']}</strong></p>
                    <small>{phase_ratings['endgame']['accuracy']:.1f}% accuracy</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="phase-card phase-endgame">
                    <h4>👑 Endgame</h4>
                    <p><strong>N/A</strong></p>
                    <small>Game didn't reach endgame</small>
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### ⚫ Black")
        st.markdown(f'<div class="elo-badge">{st.session_state.estimated_elo["black"]}</div>', unsafe_allow_html=True)
        st.caption("Estimated ELO")
        st.metric("Accuracy", f"{st.session_state.black_stats['accuracy']:.1f}%")
        st.metric("Avg CP Loss", f"{st.session_state.black_stats['acpl']:.0f}")
    
    st.markdown("---")
    
    # Move Quality Distribution
    st.markdown("## 🎨 Move Quality Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚪ White's Moves")
        moves = st.session_state.white_stats['move_types']
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("✨ Brilliant", moves.get('brilliant', 0))
        col_b.metric("🌟 Great", moves.get('great', 0))
        col_c.metric("✓ Best", moves.get('best', 0))
        
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("⭐ Excellent", moves.get('excellent', 0))
        col_e.metric("✔ Good", moves.get('good', 0))
        col_f.metric("📚 Theory", moves.get('theory', 0))
        
        col_g, col_h, col_i = st.columns(3)
        col_g.metric("⚠ Inaccuracy", moves.get('inaccuracy', 0))
        col_h.metric("❌ Mistake", moves.get('mistake', 0))
        col_i.metric("💥 Blunder", moves.get('blunder', 0))
    
    with col2:
        st.markdown("### ⚫ Black's Moves")
        moves = st.session_state.black_stats['move_types']
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("✨ Brilliant", moves.get('brilliant', 0))
        col_b.metric("🌟 Great", moves.get('great', 0))
        col_c.metric("✓ Best", moves.get('best', 0))
        
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("⭐ Excellent", moves.get('excellent', 0))
        col_e.metric("✔ Good", moves.get('good', 0))
        col_f.metric("📚 Theory", moves.get('theory', 0))
        
        col_g, col_h, col_i = st.columns(3)
        col_g.metric("⚠ Inaccuracy", moves.get('inaccuracy', 0))
        col_h.metric("❌ Mistake", moves.get('mistake', 0))
        col_i.metric("💥 Blunder", moves.get('blunder', 0))
    
    st.markdown("---")
    
    # Interactive Board
    col_board, col_eval, col_analysis = st.columns([3, 0.5, 2.5])
    
    with col_board:
        st.markdown('<div class="board-container">', unsafe_allow_html=True)
        
        last_move = None
        if current_move:
            try:
                last_move = chess.Move.from_uci(current_move['move'])
            except:
                pass
        
        board_html = render_board_svg(current_board, size=450, last_move=last_move)
        st.markdown(board_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation
        st.markdown("### 🎮 Navigation")
        
        col_n1, col_n2, col_n3, col_n4, col_n5 = st.columns(5)
        
        with col_n1:
            if st.button("⏮️ Start", use_container_width=True):
                st.session_state.current_move_index = 0
                st.rerun()
        
        with col_n2:
            if st.button("◀️ Prev", use_container_width=True):
                if st.session_state.current_move_index > 0:
                    st.session_state.current_move_index -= 1
                    st.rerun()
        
        with col_n3:
            move_slider = st.slider("Move", 0, len(position_history) - 1, current_idx, label_visibility="collapsed")
            if move_slider != current_idx:
                st.session_state.current_move_index = move_slider
                st.rerun()
        
        with col_n4:
            if st.button("▶️ Next", use_container_width=True):
                if st.session_state.current_move_index < len(position_history) - 1:
                    st.session_state.current_move_index += 1
                    st.rerun()
        
        with col_n5:
            if st.button("⏭️ End", use_container_width=True):
                st.session_state.current_move_index = len(position_history) - 1
                st.rerun()
        
        if current_move:
            move_type = current_move['classification']['type']
            st.markdown(f"""
            <div style="text-align: center; margin-top: 1rem;">
                <h3>Move {current_move['move_number']}: {current_move['san']}</h3>
                <span class="move-badge move-{move_type}">
                    {current_move['classification']['feedback']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with col_eval:
        eval_score = current_move['eval_after'] if current_move else 0
        st.markdown(render_evaluation_bar(eval_score, None, height=450), unsafe_allow_html=True)
    
    with col_analysis:
        st.markdown("### 📊 Analysis")
        
        if current_move:
            st.markdown(f"""
            <div class="analysis-panel">
                <h4>{current_move['player']}: {current_move['san']}</h4>
                <p><strong>Eval:</strong> {current_move['eval_after']:+.2f}</p>
                <p><span class="move-badge move-{current_move['classification']['type']}">
                    {current_move['classification']['type'].title()} {current_move['classification']['symbol']}
                </span></p>
                <p><strong>CP Loss:</strong> {abs(current_move['classification']['cp_loss'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # AI Tutor
            if st.session_state.tutor_mode:
                tutor_text = generate_tutor_explanation(current_move, current_board)
                st.markdown(f"""
                <div class="tutor-box">
                    <div class="tutor-icon">🎓</div>
                    {tutor_text}
                </div>
                """, unsafe_allow_html=True)
            
            # Better move
            if current_move['best_move'] and current_move['best_move'] != current_move['move']:
                st.warning(f"**💡 Best:** {current_move['best_move_san']}")
            
            # Next move hints
            if st.session_state.show_hints and current_idx < len(analysis):
                st.markdown("### 🎯 Next Move Hints")
                next_analysis = analyze_position(current_board, depth=12)
                
                if next_analysis['top_moves']:
                    for idx, top_move in enumerate(next_analysis['top_moves'][:3], 1):
                        st.markdown(f"""
                        <div style="background: rgba(45, 45, 68, 0.4); padding: 0.8rem; 
                                    border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid #667eea;">
                            <strong>{idx}. {top_move['san']}</strong> 
                            <span style="color: {'#10b981' if idx == 1 else '#3b82f6'};">
                                ({top_move['eval']:+.2f})
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Variations
            if show_alternatives and current_move['top_moves']:
                with st.expander("🔍 Alternative Lines"):
                    for idx, alt in enumerate(current_move['top_moves'][:3], 1):
                        is_played = (alt['move'] == current_move['move'])
                        st.markdown(f"**{idx}. {alt['san']}** ({'✓ Played' if is_played else alt['eval']})")
                        st.caption(f"Line: {' '.join(alt['pv'][:5])}")
        else:
            st.markdown("""
            <div class="analysis-panel">
                <h4>Starting Position</h4>
                <p>Click Next to begin</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed Review Tabs
    st.markdown("## 📝 Detailed Review")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All", "⚪ White", "⚫ Black", "⚠️ Critical"])
    
    with tab1:
        for idx, m in enumerate(analysis):
            with st.expander(f"Move {m['move_number']}: {m['san']} ({m['player']}) - {m['classification']['type'].title()}"):
                st.markdown(f"**Classification:** <span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Eval:** {m['eval_after']:+.2f} | **CP Loss:** {abs(m['classification']['cp_loss'])}")
                
                if m['best_move'] and m['best_move'] != m['move']:
                    st.info(f"Better: {m['best_move_san']}")
                
                if st.button(f"Jump", key=f"all_{idx}"):
                    st.session_state.current_move_index = idx + 1
                    st.rerun()
    
    with tab2:
        white_moves = [m for m in analysis if m['player'] == 'White']
        for m in white_moves:
            with st.expander(f"Move {m['move_number']}: {m['san']} - {m['classification']['type'].title()}"):
                st.markdown(f"<span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Eval:** {m['eval_after']:+.2f}")
                if m['best_move'] and m['best_move'] != m['move']:
                    st.info(f"Better: {m['best_move_san']}")
    
    with tab3:
        black_moves = [m for m in analysis if m['player'] == 'Black']
        for m in black_moves:
            with st.expander(f"Move {m['move_number']}: {m['san']} - {m['classification']['type'].title()}"):
                st.markdown(f"<span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Eval:** {m['eval_after']:+.2f}")
                if m['best_move'] and m['best_move'] != m['move']:
                    st.info(f"Better: {m['best_move_san']}")
    
    with tab4:
        critical = [m for m in analysis if m['classification']['type'] in ['mistake', 'blunder', 'brilliant']]
        if not critical:
            st.success("🎉 No critical mistakes!")
        else:
            for m in critical:
                emoji = '💥' if m['classification']['type'] == 'blunder' else '❌' if m['classification']['type'] == 'mistake' else '✨'
                with st.expander(f"{emoji} Move {m['move_number']}: {m['san']} ({m['player']})"):
                    st.markdown(f"<span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Played:** {m['san']} | **Best:** {m['best_move_san']}")
                    st.markdown(f"**Eval Change:** {m['eval_before']:+.2f} → {m['eval_after']:+.2f}")
                    st.error(f"Lost {abs(m['classification']['cp_loss'])} centipawns")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0c0; padding: 20px;">
    <p><strong>Chess Coach Pro - Ultimate Edition</strong></p>
    <p>🤖 Stockfish | 🎓 AI Tutor | 📊 9-Level Classification | 🏆 ELO Estimation</p>
</div>
""", unsafe_allow_html=True)
