"""
Chess Coach Pro - Complete Edition
Ultimate chess analysis combining 9-level classification, tactics, and AI coaching

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
from plotly.subplots import make_subplots
import pandas as pd
import base64
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Chess Coach Pro - Complete",
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
if 'opening_info' not in st.session_state:
    st.session_state.opening_info = {}
if 'tactical_motifs' not in st.session_state:
    st.session_state.tactical_motifs = []
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
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #a0a0c0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 9-Level Move Classifications */
    .move-brilliant {
        background: rgba(147, 51, 234, 0.25);
        border: 2px solid rgba(147, 51, 234, 0.6);
        color: #c084fc;
        box-shadow: 0 0 15px rgba(147, 51, 234, 0.4);
    }
    
    .move-great {
        background: rgba(16, 185, 129, 0.25);
        border: 2px solid rgba(16, 185, 129, 0.6);
        color: #34d399;
    }
    
    .move-best {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.5);
        color: #10b981;
    }
    
    .move-excellent {
        background: rgba(59, 130, 246, 0.25);
        border: 2px solid rgba(59, 130, 246, 0.5);
        color: #60a5fa;
    }
    
    .move-good {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #3b82f6;
    }
    
    .move-theory {
        background: rgba(168, 85, 247, 0.2);
        border: 1px solid rgba(168, 85, 247, 0.5);
        color: #a855f7;
    }
    
    .move-inaccuracy {
        background: rgba(245, 158, 11, 0.2);
        border: 1px solid rgba(245, 158, 11, 0.5);
        color: #f59e0b;
    }
    
    .move-mistake {
        background: rgba(249, 115, 22, 0.25);
        border: 2px solid rgba(249, 115, 22, 0.5);
        color: #f97316;
    }
    
    .move-blunder {
        background: rgba(239, 68, 68, 0.3);
        border: 2px solid rgba(239, 68, 68, 0.6);
        color: #ef4444;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
    }
    
    .move-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
        margin: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    /* ELO Badge */
    .elo-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 30px;
        font-size: 1.8rem;
        font-weight: bold;
        display: inline-block;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Phase Rating Cards */
    .phase-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid;
        text-align: center;
    }
    
    .phase-opening { border-left-color: #667eea; }
    .phase-middlegame { border-left-color: #f093fb; }
    .phase-endgame { border-left-color: #4facfe; }
    
    .board-container {
        background: rgba(45, 45, 68, 0.6);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        text-align: center;
    }
    
    .eval-bar-container {
        height: 450px;
        width: 45px;
        background: #1a1a2e;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
    }
    
    .eval-bar-white {
        background: linear-gradient(180deg, #f0f0f0 0%, #d0d0d0 100%);
        transition: height 0.3s ease;
    }
    
    .analysis-panel {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .tactic-tag {
        display: inline-block;
        background: rgba(147, 51, 234, 0.2);
        border: 1px solid rgba(147, 51, 234, 0.5);
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: #c084fc;
    }
    
    .strength-item {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .weakness-item {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Opening Database
OPENING_DATABASE = {
    'e2e4 e7e5 g1f3 b8c6 f1b5': {
        'name': 'Ruy Lopez',
        'eco': 'C60-C99',
        'key_ideas': ['Control center', 'Pressure on e5', 'Prepare d4', 'Castle kingside'],
        'rating': 9.5
    },
    'e2e4 c7c5': {
        'name': 'Sicilian Defense',
        'eco': 'B20-B99',
        'key_ideas': ['Asymmetrical structure', 'Queenside counterplay', 'Open c-file'],
        'rating': 9.3
    },
    'e2e4 e7e5 g1f3 b8c6 f1c4': {
        'name': 'Italian Game',
        'eco': 'C50-C54',
        'key_ideas': ['Quick development', 'Pressure f7', 'Central control'],
        'rating': 9.0
    },
    'd2d4 d7d5 c2c4': {
        'name': "Queen's Gambit",
        'eco': 'D00-D69',
        'key_ideas': ['Control center', 'Develop behind pawns', 'Pressure d5'],
        'rating': 9.4
    },
    'd2d4 g8f6 c2c4 e7e6': {
        'name': 'Nimzo-Indian',
        'eco': 'E20-E59',
        'key_ideas': ['Hypermodern control', 'Pin knight', 'Damage structure'],
        'rating': 9.2
    },
    'e2e4 e7e6': {
        'name': 'French Defense',
        'eco': 'C00-C19',
        'key_ideas': ['Solid pawn chain', 'Challenge with c5', 'Queenside play'],
        'rating': 8.8
    },
    'e2e4 c7c6': {
        'name': 'Caro-Kann Defense',
        'eco': 'B10-B19',
        'key_ideas': ['Solid structure', 'Active bishop', 'Safe king'],
        'rating': 8.9
    },
    'c2c4': {
        'name': 'English Opening',
        'eco': 'A10-A39',
        'key_ideas': ['Control d5', 'Flexible structure', 'Fianchetto'],
        'rating': 8.7
    },
}

# Tactical Patterns
TACTICAL_PATTERNS = {
    'fork': {'name': 'Fork', 'icon': '⚔️', 'description': 'One piece attacks two or more pieces'},
    'pin': {'name': 'Pin', 'icon': '📌', 'description': 'Piece cannot move without exposing more valuable piece'},
    'skewer': {'name': 'Skewer', 'icon': '🔪', 'description': 'Valuable piece must move, exposing piece behind'},
    'discovered_attack': {'name': 'Discovered Attack', 'icon': '💥', 'description': 'Moving piece reveals attack from another'},
    'discovered_check': {'name': 'Discovered Check', 'icon': '⚡', 'description': 'Moving piece reveals check from another'},
    'double_attack': {'name': 'Double Attack', 'icon': '🎯', 'description': 'Creating two threats simultaneously'},
    'removing_defender': {'name': 'Removing Defender', 'icon': '🛡️', 'description': 'Eliminate piece defending key square'},
    'back_rank': {'name': 'Back Rank Mate', 'icon': '👑', 'description': 'Checkmate on back rank with trapped king'},
    'deflection': {'name': 'Deflection', 'icon': '🔄', 'description': 'Force piece away from defensive duty'},
    'capture': {'name': 'Capture', 'icon': '✖️', 'description': 'Capturing opponent piece'},
    'check': {'name': 'Check', 'icon': '♔', 'description': 'Attacking enemy king'},
    'checkmate': {'name': 'Checkmate', 'icon': '♚', 'description': 'King in check with no escape'},
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
    """Analyze position with Stockfish - Always returns evaluation from White's perspective"""
    if st.session_state.engine is None:
        return {'evaluation': 0, 'best_move': None, 'mate_in': None, 'top_moves': []}
    
    try:
        info = st.session_state.engine.analyse(board, chess.engine.Limit(depth=depth), multipv=3)
        
        main_info = info[0] if isinstance(info, list) else info
        score = main_info['score'].white()  # Always from White's perspective
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() is not None else 0
        best_move = main_info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        
        top_moves = []
        if isinstance(info, list):
            for line in info[:3]:
                move = line.get('pv', [None])[0]
                if move:
                    move_score = line['score'].white()  # Always from White's perspective
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
    
    return {'name': 'Unknown Opening', 'eco': 'A00', 'key_ideas': [], 'rating': 5.0}

def detect_tactical_motifs(board, move, previous_board):
    """Enhanced tactical pattern detection"""
    motifs = []
    from_piece = previous_board.piece_at(move.from_square)
    
    if not from_piece:
        return motifs
    
    # Captures
    if board.is_capture(move):
        motifs.append('capture')
        to_piece = previous_board.piece_at(move.to_square)
        if to_piece and from_piece.piece_type < to_piece.piece_type:
            motifs.append('winning_capture')
    
    # Checks and checkmate
    if board.is_check():
        motifs.append('check')
        if board.is_checkmate():
            motifs.append('checkmate')
            return motifs
    
    # Fork detection
    attacks = list(board.attacks(move.to_square))
    valuable_attacks = [sq for sq in attacks if board.piece_at(sq) and 
                       board.piece_at(sq).color != from_piece.color and
                       board.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK, chess.KING]]
    
    if len(valuable_attacks) >= 2:
        motifs.append('fork')
    
    # Pin detection
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color != from_piece.color:
            attackers = board.attackers(from_piece.color, square)
            if move.to_square in attackers:
                # Check if there's a more valuable piece behind
                for behind_sq in chess.SQUARES:
                    behind_piece = board.piece_at(behind_sq)
                    if (behind_piece and behind_piece.color == piece.color and
                        behind_piece.piece_type > piece.piece_type):
                        if chess.square_file(behind_sq) == chess.square_file(square) or \
                           chess.square_rank(behind_sq) == chess.square_rank(square):
                            motifs.append('pin')
                            break
    
    # Discovered attack
    if is_discovered_attack(previous_board, move):
        motifs.append('discovered_attack')
        if board.is_check():
            motifs.append('discovered_check')
    
    # Skewer
    if from_piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
        attacks = board.attacks(move.to_square)
        for square in attacks:
            target = board.piece_at(square)
            if target and target.color != from_piece.color:
                if target.piece_type in [chess.QUEEN, chess.KING]:
                    motifs.append('skewer')
                    break
    
    # Back rank threats
    if board.is_check():
        king_square = board.king(not board.turn)
        if king_square is not None:
            rank = chess.square_rank(king_square)
            if (rank == 0 and not board.turn) or (rank == 7 and board.turn):
                motifs.append('back_rank')
    
    # Double attack
    if len(valuable_attacks) >= 2 or (board.is_check() and valuable_attacks):
        motifs.append('double_attack')
    
    return motifs

def is_discovered_attack(board, move):
    """Check for discovered attack"""
    moving_piece = board.piece_at(move.from_square)
    if not moving_piece:
        return False
    
    for piece_square in board.piece_map():
        piece = board.piece_at(piece_square)
        if piece and piece.color == moving_piece.color:
            if piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                attacks_before = list(board.attacks(piece_square))
                temp_board = board.copy()
                temp_board.remove_piece_at(move.from_square)
                attacks_after = list(temp_board.attacks(piece_square))
                if len(attacks_after) > len(attacks_before):
                    return True
    return False

def classify_move_9_levels(eval_before, eval_after, is_best_move, player_color, is_book_move=False, best_move_eval=None):
    """
    Realistic 9-level move classification based on Chess.com/Lichess standards:
    
    Centipawn Loss (CPL) = How much worse the position became after the move
    - CPL is ALWAYS POSITIVE when position worsens
    - Lower CPL = Better move
    
    Thresholds (based on real chess platforms):
    - Best: 0-10 CP loss (engine's top choice)
    - Excellent: 10-25 CP loss
    - Good: 25-50 CP loss
    - Inaccuracy: 50-100 CP loss
    - Mistake: 100-200 CP loss
    - Blunder: 200+ CP loss
    - Brilliant: Special case - NOT best move but gains unexpected advantage
    - Great: Better than engine's 2nd best by 20+ CP
    """
    
    # Normalize evaluation for player color
    if player_color == chess.BLACK:
        eval_before = -eval_before
        eval_after = -eval_after
    
    # Calculate centipawn loss - POSITIVE means position got worse
    # eval_before = 2.0, eval_after = 1.8 → loss = 20 centipawns (position worsened)
    centipawn_loss = (eval_before - eval_after) * 100
    
    # Ensure non-negative (handle floating point errors)
    if abs(centipawn_loss) < 1:
        centipawn_loss = 0
    
    # Theory/Book move (only in opening phase)
    if is_book_move:
        return {
            'type': 'theory',
            'symbol': '⚐',
            'cp_loss': 0,
            'feedback': '📚 Theory',
            'color': '#a855f7',
            'explanation': 'Standard opening theory.',
            'teaching': 'Following book moves is good in the opening.'
        }
    
    # BRILLIANT - Very special case
    # Requirements:
    # 1. NOT the engine's best move
    # 2. Still only loses 0-15 CP (so it's objectively strong)
    # 3. Involves a sacrifice or very non-obvious play (we approximate this)
    # 4. The position must be complex (eval swings matter)
    
    # For now, we mark brilliant conservatively:
    # Only if it's not best move, loses less than 15 CP, AND position improved significantly
    if (not is_best_move and 
        centipawn_loss <= 15 and 
        centipawn_loss >= 0 and
        eval_after > eval_before + 0.2):  # Position actually improved by 20+ CP
        
        return {
            'type': 'brilliant',
            'symbol': '‼',
            'cp_loss': int(centipawn_loss),
            'feedback': '✨ Brilliant!!',
            'color': '#9333ea',
            'explanation': 'Exceptional move! Likely involves a sacrifice or counter-intuitive play.',
            'teaching': 'This is a brilliant find - study this position!'
        }
    
    # GREAT - Strong alternative move
    # Not best, but only loses 5-15 CP and is clearly better than other alternatives
    if (not is_best_move and 
        0 <= centipawn_loss <= 15):
        
        return {
            'type': 'great',
            'symbol': '⁂',
            'cp_loss': int(centipawn_loss),
            'feedback': '🌟 Great!',
            'color': '#34d399',
            'explanation': 'Very strong alternative to the best move.',
            'teaching': 'Almost as good as the engine\'s choice!'
        }
    
    # BEST - Engine's top choice or nearly perfect
    if is_best_move or centipawn_loss <= 10:
        return {
            'type': 'best',
            'symbol': '!',
            'cp_loss': int(centipawn_loss),
            'feedback': '✓ Best',
            'color': '#10b981',
            'explanation': 'Optimal or near-optimal move.',
            'teaching': 'Perfect play! This is what the engine recommends.'
        }
    
    # EXCELLENT - Very good move (10-25 CP loss)
    if centipawn_loss <= 25:
        return {
            'type': 'excellent',
            'symbol': '⁺',
            'cp_loss': int(centipawn_loss),
            'feedback': '⭐ Excellent',
            'color': '#60a5fa',
            'explanation': 'Very strong move with minimal loss.',
            'teaching': f'Only {int(centipawn_loss)} CP from perfect - great accuracy!'
        }
    
    # GOOD - Acceptable move (25-50 CP loss)
    if centipawn_loss <= 50:
        return {
            'type': 'good',
            'symbol': '',
            'cp_loss': int(centipawn_loss),
            'feedback': '✔ Good',
            'color': '#3b82f6',
            'explanation': 'Reasonable move that maintains position.',
            'teaching': f'Solid play. Lost {int(centipawn_loss)} CP - acceptable in practical play.'
        }
    
    # INACCURACY - Minor error (50-100 CP loss)
    if centipawn_loss <= 100:
        return {
            'type': 'inaccuracy',
            'symbol': '?!',
            'cp_loss': int(centipawn_loss),
            'feedback': '⚠ Inaccuracy',
            'color': '#f59e0b',
            'explanation': 'Suboptimal move - better options existed.',
            'teaching': f'Lost {int(centipawn_loss)} CP. Look for more active moves or better piece placement.'
        }
    
    # MISTAKE - Significant error (100-200 CP loss)
    if centipawn_loss <= 200:
        return {
            'type': 'mistake',
            'symbol': '?',
            'cp_loss': int(centipawn_loss),
            'feedback': '❌ Mistake',
            'color': '#f97316',
            'explanation': 'Clear mistake that weakens your position.',
            'teaching': f'This loses {int(centipawn_loss)} CP! Check: 1) Are pieces safe? 2) What are opponent\'s threats? 3) Better squares?'
        }
    
    # BLUNDER - Critical error (200+ CP loss)
    return {
        'type': 'blunder',
        'symbol': '??',
        'cp_loss': int(centipawn_loss),
        'feedback': '💥 BLUNDER!!',
        'color': '#ef4444',
        'explanation': 'Critical error! Loses material or winning advantage.',
        'teaching': f'Huge blunder losing {int(centipawn_loss)} CP! Use blunder-check: 1) Checks? 2) Captures? 3) Attacks on my pieces? 4) All pieces defended?'
    }

def generate_tutor_explanation(move_data, position_board):
    """Generate detailed AI tutor explanation"""
    move_type = move_data['classification']['type']
    san = move_data['san']
    cp_loss = move_data['classification']['cp_loss']
    best = move_data.get('best_move_san', 'N/A')
    
    explanations = {
        'brilliant': f"""
        🎓 **BRILLIANT PLAY!**
        
        You discovered {san}, a brilliant move worth {abs(cp_loss)} centipawns!
        
        **Why it's brilliant:**
        - Shows exceptional calculation depth
        - May involve a surprising sacrifice or counter-intuitive move
        - Gains significant advantage through creativity
        
        **Master Insight:** Brilliant moves often involve sacrificing material for positional compensation, 
        launching surprising attacks, or finding hidden tactical resources. Study this position!
        """,
        
        'great': f"""
        🎓 **GREAT DISCOVERY!**
        
        {san} is a great move, improving your position by {abs(cp_loss)} centipawns!
        
        **Why it's great:**
        - Significantly better than the obvious alternatives
        - Shows strong understanding of position
        - Finds the most active continuation
        
        **Keep It Up:** You're thinking beyond surface-level moves. This depth of analysis leads to mastery!
        """,
        
        'best': f"""
        🎓 **PERFECT EXECUTION!**
        
        {san} is the engine's top choice. Excellent precision!
        
        **Why it's best:**
        - Optimal piece placement or pawn structure
        - Maintains or increases your advantage
        - No better alternative exists in this position
        
        **Elite Performance:** Consistently finding best moves separates masters from beginners. You're on the right track!
        """,
        
        'excellent': f"""
        🎓 **EXCELLENT CHOICE!**
        
        {san} is an excellent move, only {abs(cp_loss)} centipawns from perfect.
        
        **Why it's excellent:**
        - Practically as strong as the best move
        - Achieves similar strategic goals
        - The difference is negligible in practice
        
        **Strong Play:** At this level of accuracy, you're playing near-perfect chess!
        """,
        
        'good': f"""
        🎓 **SOLID MOVE!**
        
        {san} maintains your position. Good fundamental play.
        
        **Why it's good:**
        - No significant weaknesses created
        - Keeps pieces coordinated
        - Loss of {abs(cp_loss)} centipawns is acceptable
        
        **Steady Progress:** Good moves keep you in the game and avoid complications.
        """,
        
        'theory': f"""
        🎓 **FOLLOWING THEORY!**
        
        {san} is a well-known theoretical move in this opening.
        
        **Opening Principles:**
        - Control the center
        - Develop pieces efficiently
        - Castle for king safety
        - Don't move the same piece twice
        
        **Study Tip:** Learn the IDEAS behind opening moves, not just memorization. Understand why masters play these moves!
        """,
        
        'inaccuracy': f"""
        🎓 **ROOM FOR IMPROVEMENT**
        
        {san} loses {abs(cp_loss)} centipawns. Not optimal here.
        
        **Better was:** {best}
        
        **What to improve:**
        - Look for more active piece placement
        - Check if you can gain tempo (move with threat)
        - Consider controlling key central squares
        
        **Practice Drill:** Before moving, ask: "Can my pieces be MORE active?" Take 10 extra seconds to look deeper!
        """,
        
        'mistake': f"""
        🎓 **LEARNING OPPORTUNITY**
        
        {san} is a mistake, losing {abs(cp_loss)} centipawns.
        
        **You should have played:** {best}
        
        **What went wrong:**
        - Tactical oversight (missed threat or piece safety)
        - Weakened pawn structure or king safety
        - Piece became passive or misplaced
        
        **CRITICAL CHECKLIST (Use Every Move):**
        1. ✓ Are ALL my pieces safe?
        2. ✓ Am I leaving weaknesses (holes, backward pawns)?
        3. ✓ What is my opponent's BEST response?
        4. ✓ Can I improve piece activity first?
        
        **Recovery:** Everyone makes mistakes. The key is learning from them!
        """,
        
        'blunder': f"""
        🎓 **CRITICAL LEARNING MOMENT**
        
        {san} is a serious blunder, losing {abs(cp_loss)} centipawns!
        
        **The correct move was:** {best}
        
        **What you missed:**
        - Hanging piece (undefended)
        - Tactical blow (fork, pin, skewer)
        - Checkmate threat
        - Losing material through forced sequence
        
        **MANDATORY BLUNDER-CHECK ROUTINE:**
        Before EVERY move, verify:
        1. ✓ Does opponent have ANY checks?
        2. ✓ Does opponent have ANY captures?
        3. ✓ Does opponent have ANY attacks on my pieces?
        4. ✓ Are ALL my pieces defended?
        5. ✓ Is my king safe from tactics?
        
        **Training Plan:**
        - Slow down! Take 2x as long on each move
        - Do 20 tactical puzzles daily on Chess.com/Lichess
        - Practice "touch-move" discipline: Think BEFORE touching pieces
        
        **Remember:** 95% of blunders are preventable with careful checking. You can eliminate these!
        """,
    }
    
    return explanations.get(move_type, move_data['classification']['explanation'])

def estimate_elo(accuracy, acpl, phase_performance, move_quality_distribution):
    """
    Enhanced ELO estimation based on multiple factors:
    - Overall accuracy
    - Average centipawn loss (ACPL)
    - Phase performance (opening, middlegame, endgame)
    - Move quality distribution
    """
    base_elo = 600
    
    # Accuracy contribution (0-800 points)
    if accuracy >= 95:
        accuracy_elo = 800
    elif accuracy >= 90:
        accuracy_elo = 700
    elif accuracy >= 85:
        accuracy_elo = 600
    elif accuracy >= 80:
        accuracy_elo = 500
    elif accuracy >= 75:
        accuracy_elo = 400
    elif accuracy >= 70:
        accuracy_elo = 300
    else:
        accuracy_elo = (accuracy / 70) * 300
    
    # ACPL contribution (0-500 points, lower ACPL = higher rating)
    if acpl < 10:
        acpl_elo = 500
    elif acpl < 20:
        acpl_elo = 450
    elif acpl < 30:
        acpl_elo = 400
    elif acpl < 50:
        acpl_elo = 350
    elif acpl < 75:
        acpl_elo = 300
    elif acpl < 100:
        acpl_elo = 250
    else:
        acpl_elo = max(0, 250 - (acpl - 100) * 2)
    
    # Phase performance (0-400 points)
    phase_elo = (
        phase_performance.get('opening', 0) * 1.2 +
        phase_performance.get('middlegame', 0) * 1.5 +
        phase_performance.get('endgame', 0) * 1.3
    ) / 4
    
    # Move quality bonus (0-300 points)
    brilliant_bonus = move_quality_distribution.get('brilliant', 0) * 50
    great_bonus = move_quality_distribution.get('great', 0) * 30
    best_bonus = move_quality_distribution.get('best', 0) * 2
    quality_bonus = min(300, brilliant_bonus + great_bonus + best_bonus)
    
    # Blunder penalty
    blunder_penalty = move_quality_distribution.get('blunder', 0) * 100
    mistake_penalty = move_quality_distribution.get('mistake', 0) * 30
    
    estimated = base_elo + accuracy_elo + acpl_elo + phase_elo + quality_bonus - blunder_penalty - mistake_penalty
    
    # Clamp between 400-3200
    return max(400, min(3200, int(estimated)))

def calculate_phase_ratings(analysis):
    """Calculate performance ratings for each game phase"""
    opening_moves = [m for m in analysis if m['move_number'] <= 12]
    middlegame_moves = [m for m in analysis if 12 < m['move_number'] <= 40]
    endgame_moves = [m for m in analysis if m['move_number'] > 40]
    
    def phase_score(moves):
        if not moves:
            return {'score': 0, 'accuracy': 0, 'rating': 'N/A', 'total_moves': 0, 'good_moves': 0}
        
        good_moves = sum(1 for m in moves if m['classification']['type'] in 
                        ['brilliant', 'great', 'best', 'excellent', 'good', 'theory'])
        accuracy = (good_moves / len(moves)) * 100
        
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
        'endgame': phase_score(endgame_moves)
    }

def calculate_player_stats(analysis, player):
    """Calculate comprehensive statistics for a player"""
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
    
    excellent_moves = (move_types['brilliant'] + move_types['great'] + 
                      move_types['best'] + move_types['excellent'] + 
                      move_types['good'] + move_types['theory'])
    accuracy = (excellent_moves / len(player_moves) * 100) if player_moves else 0
    acpl = total_cp_loss / len(player_moves) if player_moves else 0
    
    return {
        'total_moves': len(player_moves),
        'move_types': move_types,
        'accuracy': accuracy,
        'acpl': acpl
    }

def analyze_game(pgn_string, progress_callback=None):
    """Comprehensive game analysis"""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        return None
    
    board = game.board()
    analysis = []
    position_history = [board.copy()]
    move_sequence = []
    tactical_motifs = []
    move_number = 1
    
    total_moves = len(list(game.mainline_moves()))
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    
    for idx, move in enumerate(game.mainline_moves()):
        if progress_callback:
            progress_callback((idx + 1) / total_moves)
        
        previous_board = board.copy()
        move_sequence.append(move.uci())
        
        # Detect if it's a theory move (first 10 moves)
        opening_info = detect_opening(move_sequence)
        is_theory = (idx < 10 and opening_info['name'] != 'Unknown Opening')
        
        # Analyze before move
        eval_before = analyze_position(board, depth=16)
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        player_color = board.turn
        san_move = board.san(move)
        
        # Make move
        board.push(move)
        position_history.append(board.copy())
        
        # Analyze after move
        eval_after = analyze_position(board, depth=16)
        
        # Detect tactical motifs
        motifs = detect_tactical_motifs(board, move, previous_board)
        if motifs:
            tactical_motifs.append({
                'move_number': move_number,
                'move': san_move,
                'motifs': motifs,
                'player': 'White' if player_color == chess.WHITE else 'Black',
                'fen': board.fen()
            })
        
        # Classify move with 9-level system
        classification = classify_move_9_levels(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color,
            is_theory,
            eval_before.get('evaluation')
        )
        
        analysis.append({
            'move_number': move_number,
            'move': move.uci(),
            'san': san_move,
            'player': 'White' if player_color == chess.WHITE else 'Black',
            'eval_before': eval_before['evaluation'],
            'eval_after': eval_after['evaluation'],
            'mate_before': eval_before.get('mate_in'),
            'mate_after': eval_after.get('mate_in'),
            'best_move': best_move,
            'best_move_san': eval_before.get('best_move_san'),
            'top_moves': eval_before.get('top_moves', []),
            'classification': classification,
            'motifs': motifs,
            'fen': board.fen(),
            'is_theory': is_theory
        })
        
        move_number += 1
    
    # Detect opening
    opening_info = detect_opening(move_sequence)
    
    return analysis, position_history, opening_info, tactical_motifs

def render_evaluation_bar(eval_score, mate_in=None, height=450):
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
                    background: rgba(0,0,0,0.85); color: white; padding: 0.6rem; 
                    border-radius: 8px; font-weight: bold; font-size: 1.1rem; min-width: 60px; text-align: center;">
            {eval_display}
        </div>
    </div>
    """

def create_evaluation_chart(analysis):
    """Create evaluation chart over time"""
    move_numbers = [m['move_number'] for m in analysis]
    evaluations = [m['eval_after'] for m in analysis]
    
    # Color code by move quality
    colors = []
    for m in analysis:
        mtype = m['classification']['type']
        if mtype in ['brilliant', 'great']:
            colors.append('#9333ea')
        elif mtype in ['best', 'excellent']:
            colors.append('#10b981')
        elif mtype == 'good':
            colors.append('#3b82f6')
        elif mtype in ['inaccuracy', 'theory']:
            colors.append('#f59e0b')
        elif mtype == 'mistake':
            colors.append('#f97316')
        else:
            colors.append('#ef4444')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=move_numbers,
        y=evaluations,
        mode='lines+markers',
        name='Evaluation',
        line=dict(color='#667eea', width=2),
        marker=dict(size=8, color=colors, line=dict(width=1, color='white')),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.15)',
        hovertemplate='Move %{x}<br>Eval: %{y:.2f}<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title='Position Evaluation Timeline',
        xaxis_title='Move Number',
        yaxis_title='Evaluation (pawns)',
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    return fig

# Main App
st.markdown('<div class="main-header">♟️ Chess Coach Pro - Complete Edition</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">🎯 9-Level Move Classification | ⚔️ Advanced Tactics | 🎓 AI Tutor | 📊 ELO Estimation | 📚 Opening Theory</div>', unsafe_allow_html=True)

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
    st.session_state.show_hints = st.checkbox("💡 Show Move Hints", value=True)
    st.session_state.tutor_mode = st.checkbox("🎓 AI Tutor Mode", value=True)
    show_alternatives = st.checkbox("🔍 Show Variations", value=True)
    show_tactics = st.checkbox("⚔️ Highlight Tactics", value=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 9-Level System")
    st.markdown("""
    <div style='font-size: 0.85rem; line-height: 1.6;'>
    <strong style='color: #9333ea;'>‼ Brilliant</strong> - Exceptional<br>
    <strong style='color: #34d399;'>⁂ Great</strong> - Very strong<br>
    <strong style='color: #10b981;'>! Best</strong> - Top choice<br>
    <strong style='color: #60a5fa;'>⁺ Excellent</strong> - Near perfect<br>
    <strong style='color: #3b82f6;'>✔ Good</strong> - Solid<br>
    <strong style='color: #a855f7;'>⚐ Theory</strong> - Book move<br>
    <strong style='color: #f59e0b;'>?! Inaccuracy</strong> - Suboptimal<br>
    <strong style='color: #f97316;'>? Mistake</strong> - Error<br>
    <strong style='color: #ef4444;'>?? Blunder</strong> - Critical error
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🤖 Engine")
    if st.session_state.engine:
        st.success("✅ Stockfish Active")
        st.caption("Depth: 16-18 ply")
    else:
        st.warning("⚠️ Limited Mode")

# Main Content
if not st.session_state.game_analysis:
    st.markdown("## 📊 Upload Your Game for Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2.5rem;">🎯</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                <strong>9-Level Classification</strong><br>
                Precise move evaluation from Brilliant to Blunder
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2.5rem;">⚔️</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                <strong>Tactical Detection</strong><br>
                Automatic recognition of 12+ tactical patterns
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2.5rem;">🎓</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                <strong>AI Coaching</strong><br>
                Personalized teaching for every move
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📝 Paste PGN", "📁 Upload File"])
    
    with tab1:
        pgn_input = st.text_area("Paste your game PGN", height=200, placeholder="""[Event "Rated Game"]
[White "Player1"]
[Black "Player2"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6...""")
        
        if st.button("🔍 Analyze Game", type="primary", use_container_width=True):
            if pgn_input:
                with st.spinner("🧠 Deep analysis in progress with Stockfish..."):
                    progress_bar = st.progress(0)
                    
                    def update_progress(p):
                        progress_bar.progress(p)
                    
                    result = analyze_game(pgn_input, progress_callback=update_progress)
                    
                    if result:
                        analysis, position_history, opening_info, tactical_motifs = result
                        st.session_state.game_analysis = analysis
                        st.session_state.position_history = position_history
                        st.session_state.opening_info = opening_info
                        st.session_state.tactical_motifs = tactical_motifs
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
                                white_phase,
                                st.session_state.white_stats['move_types']
                            ),
                            'black': estimate_elo(
                                st.session_state.black_stats['accuracy'],
                                st.session_state.black_stats['acpl'],
                                black_phase,
                                st.session_state.black_stats['move_types']
                            )
                        }
                        
                        progress_bar.empty()
                        st.success("✅ Analysis Complete!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid PGN format")
    
    with tab2:
        uploaded_file = st.file_uploader("Choose PGN file", type=['pgn'])
        if uploaded_file:
            pgn_content = uploaded_file.read().decode('utf-8')
            if st.button("🔍 Analyze Upload", type="primary", use_container_width=True):
                with st.spinner("🧠 Analyzing..."):
                    progress_bar = st.progress(0)
                    
                    def update_progress(p):
                        progress_bar.progress(p)
                    
                    result = analyze_game(pgn_content, progress_callback=update_progress)
                    
                    if result:
                        analysis, position_history, opening_info, tactical_motifs = result
                        st.session_state.game_analysis = analysis
                        st.session_state.position_history = position_history
                        st.session_state.opening_info = opening_info
                        st.session_state.tactical_motifs = tactical_motifs
                        st.session_state.current_move_index = 0
                        
                        st.session_state.white_stats = calculate_player_stats(analysis, 'White')
                        st.session_state.black_stats = calculate_player_stats(analysis, 'Black')
                        st.session_state.phase_ratings = calculate_phase_ratings(analysis)
                        
                        white_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        black_phase = {k: v['score'] for k, v in st.session_state.phase_ratings.items()}
                        
                        st.session_state.estimated_elo = {
                            'white': estimate_elo(st.session_state.white_stats['accuracy'], st.session_state.white_stats['acpl'], white_phase, st.session_state.white_stats['move_types']),
                            'black': estimate_elo(st.session_state.black_stats['accuracy'], st.session_state.black_stats['acpl'], black_phase, st.session_state.black_stats['move_types'])
                        }
                        
                        progress_bar.empty()
                        st.success("✅ Complete!")
                        st.balloons()
                        st.rerun()

else:
    # Display Analysis
    analysis = st.session_state.game_analysis
    position_history = st.session_state.position_history
    current_idx = st.session_state.current_move_index
    opening_info = st.session_state.opening_info
    tactical_motifs = st.session_state.tactical_motifs
    
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
        
        if opening_info.get('key_ideas'):
            st.markdown("**Key Ideas:**")
            for idea in opening_info['key_ideas'][:3]:
                st.caption(f"• {idea}")
        
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
    st.markdown("## 🎨 Move Quality Distribution (9-Level System)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚪ White's Moves")
        moves = st.session_state.white_stats['move_types']
        
        # Top tier
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("✨ Brilliant", moves.get('brilliant', 0))
        col_b.metric("🌟 Great", moves.get('great', 0))
        col_c.metric("✓ Best", moves.get('best', 0))
        
        # Mid tier
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("⭐ Excellent", moves.get('excellent', 0))
        col_e.metric("✔ Good", moves.get('good', 0))
        col_f.metric("📚 Theory", moves.get('theory', 0))
        
        # Low tier
        col_g, col_h, col_i = st.columns(3)
        col_g.metric("⚠ Inaccuracy", moves.get('inaccuracy', 0))
        col_h.metric("❌ Mistake", moves.get('mistake', 0))
        col_i.metric("💥 Blunder", moves.get('blunder', 0))
    
    with col2:
        st.markdown("### ⚫ Black's Moves")
        moves = st.session_state.black_stats['move_types']
        
        # Top tier
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("✨ Brilliant", moves.get('brilliant', 0))
        col_b.metric("🌟 Great", moves.get('great', 0))
        col_c.metric("✓ Best", moves.get('best', 0))
        
        # Mid tier
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("⭐ Excellent", moves.get('excellent', 0))
        col_e.metric("✔ Good", moves.get('good', 0))
        col_f.metric("📚 Theory", moves.get('theory', 0))
        
        # Low tier
        col_g, col_h, col_i = st.columns(3)
        col_g.metric("⚠ Inaccuracy", moves.get('inaccuracy', 0))
        col_h.metric("❌ Mistake", moves.get('mistake', 0))
        col_i.metric("💥 Blunder", moves.get('blunder', 0))
    
    st.markdown("---")
    
    # Evaluation Chart
    st.markdown("## 📈 Position Evaluation Timeline")
    eval_chart = create_evaluation_chart(analysis)
    st.plotly_chart(eval_chart, use_container_width=True)
    
    st.markdown("---")
    
    # Deep Analysis Visualizations
    st.markdown("## 🔬 Deep Performance Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["🕸️ Skill Profiles", "📊 Move Quality Flow", "🎯 Phase Breakdown"])
    
    with analysis_tab1:
        st.markdown("### Spider Charts - Complete Skill Assessment")
        col_spider1, col_spider2 = st.columns(2)
        
        with col_spider1:
            white_spider = create_spider_chart(
                st.session_state.white_phase_ratings, 
                "White", 
                "rgba(220, 220, 255, 1)"
            )
            st.plotly_chart(white_spider, use_container_width=True)
        
        with col_spider2:
            black_spider = create_spider_chart(
                st.session_state.black_phase_ratings, 
                "Black", 
                "rgba(100, 100, 120, 1)"
            )
            st.plotly_chart(black_spider, use_container_width=True)
        
        st.info("📊 **Spider Chart Metrics:**\n"
                "- **Opening/Middlegame/Endgame**: Accuracy in each phase\n"
                "- **Tactics**: Frequency of brilliant/great moves\n"
                "- **Accuracy**: Overall precision\n"
                "- **Calculation**: Consistency (inverse of errors)")
    
    with analysis_tab2:
        st.markdown("### Candlestick View - Position Volatility")
        
        col_candle1, col_candle2 = st.columns(2)
        
        with col_candle1:
            white_candles = create_move_quality_candles(analysis, 'White')
            if white_candles:
                st.plotly_chart(white_candles, use_container_width=True)
            else:
                st.info("No moves to display")
        
        with col_candle2:
            black_candles = create_move_quality_candles(analysis, 'Black')
            if black_candles:
                st.plotly_chart(black_candles, use_container_width=True)
            else:
                st.info("No moves to display")
        
        st.info("📈 **Candlestick Interpretation:**\n"
                "- **Green candles**: Position improved during segment\n"
                "- **Red candles**: Position deteriorated during segment\n"
                "- **Long wicks**: High volatility/complexity\n"
                "- Color intensity shows error count in segment")
    
    with analysis_tab3:
        st.markdown("### 9-Level Classification by Phase")
        
        phase_detail_tab1, phase_detail_tab2 = st.tabs(["⚪ White", "⚫ Black"])
        
        with phase_detail_tab1:
            white_phases = st.session_state.white_phase_ratings
            
            col_pd1, col_pd2, col_pd3 = st.columnsdef analyze_position(board, depth=18):
    """Analyze position with Stockfish - Always returns evaluation from White's perspective"""
    if st.session_state.engine is None:
        return {'evaluation': 0, 'best_move': None, 'mate_in': None, 'top_moves': []}
    
    try:
        info = st.session_state.engine.analyse(board, chess.engine.Limit(depth=depth), multipv=3)
        
        main_info = info[0] if isinstance(info, list) else info
        score = main_info['score'].white()  # Always from White's perspective
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() is not None else 0
        best_move = main_info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        
        top_moves = []
        if isinstance(info, list):
            for line in info[:3]:
                move = line.get('pv', [None])[0]
                if move:
                    move_score = line['score'].white()  # Always from White's perspective
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
    
    # Interactive Board Section
    st.markdown("## 🎮 Interactive Analysis")
    
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
                    {current_move['classification']['symbol']} {current_move['classification']['feedback']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with col_eval:
        eval_score = current_move['eval_after'] if current_move else 0
        mate = current_move.get('mate_after') if current_move else None
        st.markdown(render_evaluation_bar(eval_score, mate, height=450), unsafe_allow_html=True)
    
    with col_analysis:
        st.markdown("### 📊 Move Analysis")
        
        if current_move:
            st.markdown(f"""
            <div class="analysis-panel">
                <h4>{current_move['player']}: {current_move['san']}</h4>
                <p><strong>Evaluation:</strong> {current_move['eval_after']:+.2f}</p>
                <p><span class="move-badge move-{current_move['classification']['type']}">
                    {current_move['classification']['type'].title()} {current_move['classification']['symbol']}
                </span></p>
                <p><strong>Centipawn Loss:</strong> {abs(current_move['classification']['cp_loss'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tactical Motifs
            if show_tactics and current_move['motifs']:
                st.markdown("**⚔️ Tactical Patterns:**")
                for motif in current_move['motifs']:
                    if motif in TACTICAL_PATTERNS:
                        pattern = TACTICAL_PATTERNS[motif]
                        st.markdown(f"""
                        <span class="tactic-tag">{pattern['icon']} {pattern['name']}</span>
                        """, unsafe_allow_html=True)
                st.caption(f"*{TACTICAL_PATTERNS[current_move['motifs'][0]]['description']}*" if current_move['motifs'] else "")
            
            # AI Tutor
            if st.session_state.tutor_mode:
                tutor_text = generate_tutor_explanation(current_move, current_board)
                st.markdown(f"""
                <div class="tutor-box">
                    <div class="tutor-icon">🎓</div>
                    {tutor_text}
                </div>
                """, unsafe_allow_html=True)
            
            # Better move suggestion
            if current_move['best_move'] and current_move['best_move'] != current_move['move']:
                st.warning(f"**💡 Better move:** {current_move['best_move_san']}")
                st.caption(f"Would have saved {abs(current_move['classification']['cp_loss'])} centipawns")
            
            # Next move hints
            if st.session_state.show_hints and current_idx < len(analysis):
                st.markdown("### 🎯 Top Continuations")
                next_analysis = analyze_position(current_board, depth=14)
                
                if next_analysis['top_moves']:
                    for idx, top_move in enumerate(next_analysis['top_moves'][:3], 1):
                        st.markdown(f"""
                        <div style="background: rgba(45, 45, 68, 0.4); padding: 0.8rem; 
                                    border-radius: 8px; margin: 0.5rem 0; 
                                    border-left: 3px solid {'#10b981' if idx == 1 else '#3b82f6'};">
                            <strong>{idx}. {top_move['san']}</strong> 
                            <span style="color: {'#10b981' if idx == 1 else '#3b82f6'};">
                                ({top_move['eval']:+.2f})
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Alternative variations
            if show_alternatives and current_move['top_moves']:
                with st.expander("🔍 Alternative Lines"):
                    for idx, alt in enumerate(current_move['top_moves'][:3], 1):
                        is_played = (alt['move'] == current_move['move'])
                        eval_str = '✓ Played' if is_played else f"{alt['eval']:+.2f}"
                        st.markdown(f"**{idx}. {alt['san']}** ({eval_str})")
                        st.caption(f"Continuation: {' '.join(alt['pv'][:4])}")
        else:
            st.markdown("""
            <div class="analysis-panel">
                <h4>📍 Starting Position</h4>
                <p>Click <strong>Next</strong> to begin analysis</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tactical Motifs Summary
    if tactical_motifs:
        st.markdown("## ⚔️ Tactical Patterns Found")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            for motif_data in tactical_motifs[:10]:
                motifs_str = ' '.join([
                    f'<span class="tactic-tag">{TACTICAL_PATTERNS.get(m, {}).get("icon", "⚔️")} {TACTICAL_PATTERNS.get(m, {}).get("name", m.replace("_", " ").title())}</span>' 
                    for m in motif_data['motifs']
                ])
                
                st.markdown(f"""
                <div style="background: rgba(45, 45, 68, 0.6); padding: 1rem; 
                            border-radius: 8px; margin: 0.5rem 0; 
                            border-left: 3px solid #667eea;">
                    <strong>Move {motif_data['move_number']}: {motif_data['move']}</strong> 
                    ({motif_data['player']})<br>
                    {motifs_str}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.metric("Total Tactics", len(tactical_motifs))
            
            # Count unique patterns
            all_motifs = [m for data in tactical_motifs for m in data['motifs']]
            motif_counts = {}
            for motif in all_motifs:
                motif_counts[motif] = motif_counts.get(motif, 0) + 1
            
            st.markdown("**Pattern Breakdown:**")
            for motif, count in sorted(motif_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                pattern = TACTICAL_PATTERNS.get(motif, {'name': motif.title(), 'icon': '⚔️'})
                st.caption(f"{pattern['icon']} {pattern['name']}: {count}×")
    
    st.markdown("---")
    
    # Detailed Move Review
    st.markdown("## 📝 Detailed Move Review")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 All Moves", "⚪ White", "⚫ Black", "⚠️ Critical Moments", "✨ Best Moments"])
    
    with tab1:
        for idx, m in enumerate(analysis):
            move_type = m['classification']['type']
            with st.expander(f"Move {m['move_number']}: {m['san']} ({m['player']}) - {m['classification']['symbol']} {move_type.title()}"):
                col_a, col_b = st.columns([2, 1])
                
                with col_a:
                    st.markdown(f"**Classification:** <span class='move-badge move-{move_type}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Evaluation:** {m['eval_after']:+.2f} | **CP Loss:** {abs(m['classification']['cp_loss'])}")
                    
                    if m['motifs']:
                        motif_str = ', '.join([TACTICAL_PATTERNS.get(mot, {'name': mot}).get('name', mot) for mot in m['motifs']])
                        st.info(f"⚔️ **Tactics:** {motif_str}")
                    
                    if m['best_move'] and m['best_move'] != m['move']:
                        st.warning(f"💡 Better: {m['best_move_san']}")
                
                with col_b:
                    if st.button(f"🎯 Jump Here", key=f"all_{idx}"):
                        st.session_state.current_move_index = idx + 1
                        st.rerun()
    
    with tab2:
        white_moves = [m for m in analysis if m['player'] == 'White']
        for m in white_moves:
            move_type = m['classification']['type']
            with st.expander(f"Move {m['move_number']}: {m['san']} - {m['classification']['symbol']} {move_type.title()}"):
                st.markdown(f"<span class='move-badge move-{move_type}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Eval:** {m['eval_after']:+.2f} | **CP Loss:** {abs(m['classification']['cp_loss'])}")
                if m['best_move'] and m['best_move'] != m['move']:
                    st.info(f"Better: {m['best_move_san']}")
    
    with tab3:
        black_moves = [m for m in analysis if m['player'] == 'Black']
        for m in black_moves:
            move_type = m['classification']['type']
            with st.expander(f"Move {m['move_number']}: {m['san']} - {m['classification']['symbol']} {move_type.title()}"):
                st.markdown(f"<span class='move-badge move-{move_type}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Eval:** {m['eval_after']:+.2f} | **CP Loss:** {abs(m['classification']['cp_loss'])}")
                if m['best_move'] and m['best_move'] != m['move']:
                    st.info(f"Better: {m['best_move_san']}")
    
    with tab4:
        critical = [m for m in analysis if m['classification']['type'] in ['mistake', 'blunder']]
        if not critical:
            st.success("🎉 No critical mistakes! Excellent play!")
        else:
            for m in critical:
                emoji = '💥' if m['classification']['type'] == 'blunder' else '❌'
                with st.expander(f"{emoji} Move {m['move_number']}: {m['san']} ({m['player']}) - Lost {abs(m['classification']['cp_loss'])} cp"):
                    st.markdown(f"<span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Played:** {m['san']} | **Best:** {m['best_move_san']}")
                    st.markdown(f"**Eval Change:** {m['eval_before']:+.2f} → {m['eval_after']:+.2f}")
                    st.error(f"💔 Lost {abs(m['classification']['cp_loss'])} centipawns")
                    
                    if st.session_state.tutor_mode:
                        st.info(m['classification']['teaching'])
    
    with tab5:
        excellent = [m for m in analysis if m['classification']['type'] in ['brilliant', 'great', 'best']]
        if not excellent:
            st.info("No standout moves detected. Focus on playing more accurately!")
        else:
            for m in excellent:
                emoji = '✨' if m['classification']['type'] == 'brilliant' else '🌟' if m['classification']['type'] == 'great' else '✓'
                with st.expander(f"{emoji} Move {m['move_number']}: {m['san']} ({m['player']}) - {m['classification']['type'].title()}"):
                    st.markdown(f"<span class='move-badge move-{m['classification']['type']}'>{m['classification']['feedback']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Eval:** {m['eval_after']:+.2f}")
                    
                    if m['classification']['type'] in ['brilliant', 'great']:
                        st.success(f"🎓 {m['classification']['teaching']}")
    
    st.markdown("---")
    
    # Performance Summary
    st.markdown("## 📊 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_moves = len(analysis)
        white_moves_count = len([m for m in analysis if m['player'] == 'White'])
        black_moves_count = len([m for m in analysis if m['player'] == 'Black'])
        st.metric("Total Moves", total_moves)
        st.caption(f"White: {white_moves_count} | Black: {black_moves_count}")
    
    with col2:
        avg_accuracy = (st.session_state.white_stats['accuracy'] + st.session_state.black_stats['accuracy']) / 2
        st.metric("Avg Accuracy", f"{avg_accuracy:.1f}%")
        st.caption("Combined both players")
    
    with col3:
        brilliant_count = sum(m['classification']['type'] == 'brilliant' for m in analysis)
        great_count = sum(m['classification']['type'] == 'great' for m in analysis)
        st.metric("Exceptional Moves", brilliant_count + great_count)
        st.caption(f"Brilliant: {brilliant_count} | Great: {great_count}")
    
    with col4:
        blunder_count = sum(m['classification']['type'] == 'blunder' for m in analysis)
        mistake_count = sum(m['classification']['type'] == 'mistake' for m in analysis)
        st.metric("Errors", blunder_count + mistake_count)
        st.caption(f"Blunders: {blunder_count} | Mistakes: {mistake_count}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0c0; padding: 30px;">
    <h3 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;">
        Chess Coach Pro - Complete Edition
    </h3>
    <p style="margin-top: 1rem;">
        <strong>🤖 Powered by Stockfish Engine</strong><br>
        🎯 9-Level Move Classification | ⚔️ Advanced Tactical Detection | 🎓 AI Tutoring<br>
        📊 ELO Estimation | 📚 Opening Theory | 📈 Performance Analytics
    </p>
    <p style="margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.8;">
        Built with ❤️ for chess players worldwide<br>
        © 2025 - Master Every Move
    </p>
</div>
""", unsafe_allow_html=True)
