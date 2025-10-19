"""
Chess Learning Coach - Enhanced Streamlit Application
Advanced chess analysis with opening theory, tactics, and personalized teaching

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
from datetime import datetime
import base64
import re
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Chess Learning Coach Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .opening-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: white;
    }
    .tactical-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: white;
    }
    .weakness-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #000;
    }
    .strength-box {
        background-color: #d1e7dd;
        border-left: 4px solid #198754;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #000;
    }
    .teaching-box {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #000;
        border: 2px solid #f093fb;
    }
    .lesson-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #000;
    }
    .tactic-pattern {
        background: rgba(147, 51, 234, 0.1);
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.3rem 0;
        border: 1px solid rgba(147, 51, 234, 0.3);
    }
    .move-brilliant { color: #9333ea; font-weight: bold; }
    .move-best { color: #10b981; font-weight: bold; }
    .move-good { color: #3b82f6; }
    .move-inaccuracy { color: #f59e0b; }
    .move-mistake { color: #f97316; font-weight: bold; }
    .move-blunder { color: #ef4444; font-weight: bold; }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Opening Database (ECO codes with names and key ideas)
OPENING_DATABASE = {
    # King's Pawn Openings
    'e4 e5': {
        'name': 'Open Game',
        'eco': 'C20-C99',
        'key_ideas': ['Control center with e4', 'Develop knights to f3 and c3', 'Castle early'],
        'common_mistakes': ['Moving queen too early', 'Neglecting development', 'Pushing too many pawns']
    },
    'e4 c5': {
        'name': 'Sicilian Defense',
        'eco': 'B20-B99',
        'key_ideas': ['Asymmetrical pawn structure', 'Black plays for counterplay', 'White aims for kingside attack'],
        'common_mistakes': ['Allowing Nf3-d4-xc5 without preparation', 'Weakening d5 square', 'Slow development']
    },
    'e4 e6': {
        'name': 'French Defense',
        'eco': 'C00-C19',
        'key_ideas': ['Solid pawn chain', 'Black plays for d5 break', 'Space advantage for White'],
        'common_mistakes': ['Locking in light-squared bishop', 'Passive play', 'Allowing e5 without counterplay']
    },
    'e4 c6': {
        'name': 'Caro-Kann Defense',
        'eco': 'B10-B19',
        'key_ideas': ['Solid structure', 'Develop light-squared bishop before e6', 'Reliable and safe'],
        'common_mistakes': ['Passive piece placement', 'Not contesting center', 'Too slow development']
    },
    # Queen's Pawn Openings
    'd4 d5': {
        'name': "Queen's Pawn Game",
        'eco': 'D00-D69',
        'key_ideas': ['Control center', 'Develop pieces harmoniously', 'Fight for e4/e5 squares'],
        'common_mistakes': ['Early queen moves', 'Neglecting piece development', 'Weakening kingside']
    },
    'd4 Nf6': {
        'name': 'Indian Defenses',
        'eco': 'E00-E99',
        'key_ideas': ['Hypermodern approach', 'Control center from distance', 'Flexible pawn structure'],
        'common_mistakes': ['Allowing strong pawn center', 'Passive play', 'Poor piece coordination']
    },
    # Other Openings
    'Nf3 d5 c4': {
        'name': 'Reti Opening',
        'eco': 'A04-A09',
        'key_ideas': ['Hypermodern strategy', 'Flexible development', 'Control center with pieces'],
        'common_mistakes': ['Lack of concrete plan', 'Allowing strong pawn center', 'Slow development']
    },
    'c4': {
        'name': 'English Opening',
        'eco': 'A10-A39',
        'key_ideas': ['Control d5 square', 'Flexible pawn structure', 'Often transposes'],
        'common_mistakes': ['No clear plan', 'Weak d4 square', 'Passive development']
    }
}

# Tactical Patterns Database
TACTICAL_PATTERNS = {
    'fork': {
        'name': 'Fork',
        'description': 'One piece attacks two or more enemy pieces simultaneously',
        'recognition': 'Look for knights, queens, and pawns that can attack multiple pieces',
        'defense': 'Keep pieces protected, avoid placing valuable pieces on same diagonal/file/rank',
        'exercise': 'Practice knight fork puzzles - knights are the masters of forks!'
    },
    'pin': {
        'name': 'Pin',
        'description': 'A piece cannot move without exposing a more valuable piece behind it',
        'recognition': 'Bishops, rooks, and queens can create pins along lines',
        'defense': 'Break pins with pawn moves, block with less valuable pieces',
        'exercise': 'Study absolute pins (king behind) vs relative pins (other pieces)'
    },
    'skewer': {
        'name': 'Skewer',
        'description': 'Like a reverse pin - a valuable piece is forced to move, exposing a piece behind',
        'recognition': 'Check if moving the attacked piece exposes something valuable',
        'defense': 'Keep king and valuable pieces away from same lines',
        'exercise': 'Practice rook and bishop skewers in endgames'
    },
    'discovered_attack': {
        'name': 'Discovered Attack',
        'description': 'Moving one piece reveals an attack from another piece',
        'recognition': 'Look for pieces on same line with enemy king/queen between',
        'defense': 'Be aware of piece alignments, block attacking lines',
        'exercise': 'Study classic discovered check patterns'
    },
    'double_attack': {
        'name': 'Double Attack',
        'description': 'Creating two threats simultaneously',
        'recognition': 'Queens and knights excel at double attacks',
        'defense': 'Deal with the more dangerous threat first',
        'exercise': 'Practice queen and knight double attack puzzles'
    },
    'removing_defender': {
        'name': 'Removing the Defender',
        'description': 'Capture or deflect a piece defending a key square or piece',
        'recognition': 'Identify overworked pieces defending multiple things',
        'defense': 'Ensure multiple defenders for key squares',
        'exercise': 'Study deflection and decoy sacrifices'
    },
    'back_rank': {
        'name': 'Back Rank Mate',
        'description': 'Checkmate on the back rank when king has no escape squares',
        'recognition': 'Look for trapped kings on first/eighth rank',
        'defense': 'Create luft (escape square) for your king',
        'exercise': 'Practice back rank mate patterns with rooks and queens'
    }
}

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'game_analysis' not in st.session_state:
    st.session_state.game_analysis = []
if 'opening_analysis' not in st.session_state:
    st.session_state.opening_analysis = {}
if 'tactical_motifs' not in st.session_state:
    st.session_state.tactical_motifs = []
if 'lessons_learned' not in st.session_state:
    st.session_state.lessons_learned = []
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        'username': 'Player',
        'rating': 1200,
        'games_analyzed': 0,
        'total_tactics_found': 0,
        'opening_repertoire': []
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
        
        st.warning("⚠️ Stockfish engine not found. Analysis features will be limited.")
        return None
    except Exception as e:
        st.error(f"Error initializing Stockfish: {e}")
        return None

if st.session_state.engine is None:
    st.session_state.engine = initialize_engine()

def render_board_svg(board, size=400, highlighted_squares=None):
    """Render chess board as SVG with optional square highlighting"""
    if highlighted_squares:
        svg = chess.svg.board(board, size=size, squares=highlighted_squares)
    else:
        svg = chess.svg.board(board, size=size)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    return html

def analyze_position(board, depth=15):
    """Analyze position with Stockfish"""
    if st.session_state.engine is None:
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None,
            'pv': []
        }
    
    try:
        info = st.session_state.engine.analyse(
            board, 
            chess.engine.Limit(depth=depth)
        )
        
        score = info['score'].relative
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() is not None else 0
        best_move = info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        pv = info.get('pv', [])[:5]
        
        return {
            'evaluation': evaluation,
            'best_move': best_move.uci() if best_move else None,
            'mate_in': mate_in,
            'pv': [move.uci() for move in pv]
        }
    except Exception as e:
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None,
            'pv': []
        }

def detect_opening(moves_list):
    """Detect opening from move sequence"""
    move_string = ' '.join(moves_list[:6])  # First 6 moves
    
    # Check for exact matches
    for pattern, opening_info in OPENING_DATABASE.items():
        if pattern in move_string:
            return opening_info
    
    # Fallback based on first moves
    if moves_list:
        first_move = moves_list[0]
        if first_move == 'e4':
            if len(moves_list) > 1:
                if moves_list[1] == 'e5':
                    return OPENING_DATABASE.get('e4 e5', {'name': 'Open Game', 'eco': 'C20', 'key_ideas': [], 'common_mistakes': []})
                elif moves_list[1] == 'c5':
                    return OPENING_DATABASE.get('e4 c5', {'name': 'Sicilian Defense', 'eco': 'B20', 'key_ideas': [], 'common_mistakes': []})
        elif first_move == 'd4':
            return {'name': "Queen's Pawn Opening", 'eco': 'D00', 'key_ideas': ['Control center', 'Solid development'], 'common_mistakes': []}
        elif first_move == 'Nf3':
            return {'name': 'Reti Opening', 'eco': 'A04', 'key_ideas': ['Hypermodern', 'Flexible'], 'common_mistakes': []}
        elif first_move == 'c4':
            return OPENING_DATABASE.get('c4', {'name': 'English Opening', 'eco': 'A10', 'key_ideas': [], 'common_mistakes': []})
    
    return {'name': 'Unknown Opening', 'eco': 'A00', 'key_ideas': [], 'common_mistakes': []}

def detect_tactical_motif(board, move, previous_board):
    """Detect tactical patterns in a move"""
    motifs = []
    
    # Check for captures
    if board.is_capture(move):
        motifs.append('capture')
        
        # Check for exchange
        from_piece = previous_board.piece_at(move.from_square)
        to_piece = previous_board.piece_at(move.to_square)
        if to_piece:
            if from_piece.piece_type < to_piece.piece_type:
                motifs.append('winning_capture')
            elif from_piece.piece_type == to_piece.piece_type:
                motifs.append('exchange')
    
    # Check for checks
    if board.is_check():
        motifs.append('check')
        if board.is_checkmate():
            motifs.append('checkmate')
    
    # Check for discovered attacks
    if is_discovered_attack(previous_board, move):
        motifs.append('discovered_attack')
    
    # Check for forks (especially knight forks)
    if from_piece and from_piece.piece_type == chess.KNIGHT:
        attacks = list(board.attacks(move.to_square))
        valuable_attacks = [sq for sq in attacks if board.piece_at(sq) and 
                          board.piece_at(sq).color != from_piece.color and
                          board.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK]]
        if len(valuable_attacks) >= 2:
            motifs.append('fork')
    
    # Check for pins
    if is_creating_pin(board, move):
        motifs.append('pin')
    
    return motifs

def is_discovered_attack(board, move):
    """Check if move creates a discovered attack"""
    moving_piece = board.piece_at(move.from_square)
    if not moving_piece:
        return False
    
    # Check if there's a piece behind that could create discovered attack
    for piece_square in board.piece_map():
        piece = board.piece_at(piece_square)
        if piece and piece.color == moving_piece.color:
            if piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                # Check if moving piece was blocking an attack
                if chess.square_distance(piece_square, move.from_square) > 1:
                    return True
    return False

def is_creating_pin(board, move):
    """Check if move creates a pin"""
    piece = board.piece_at(move.to_square)
    if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
        return False
    
    # Check pieces in the same line
    for square in chess.SQUARES:
        target = board.piece_at(square)
        if target and target.color != piece.color:
            # Check if there's a more valuable piece behind
            if board.is_attacked_by(piece.color, square):
                return True
    return False

def classify_move(eval_before, eval_after, is_best_move, player_color):
    """Classify move quality with detailed feedback"""
    if player_color == chess.BLACK:
        eval_before = -eval_before
        eval_after = -eval_after
    
    centipawn_loss = (eval_before - eval_after) * 100
    
    if is_best_move or centipawn_loss < 10:
        return {
            'type': 'best',
            'symbol': '!',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Excellent move! This is exactly what the engine recommends.',
            'teaching': 'You found the best continuation in this position.'
        }
    elif centipawn_loss < -50:
        return {
            'type': 'brilliant',
            'symbol': '!!',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Brilliant! This move significantly improves your position.',
            'teaching': 'Outstanding calculation! This move demonstrates deep understanding.'
        }
    elif centipawn_loss < 50:
        return {
            'type': 'good',
            'symbol': '',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Good move maintaining your position.',
            'teaching': 'Solid choice. Keep playing with this accuracy!'
        }
    elif centipawn_loss < 100:
        return {
            'type': 'inaccuracy',
            'symbol': '?',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Inaccurate. A better move was available.',
            'teaching': 'Take more time to calculate. Look for improvements in piece activity.'
        }
    elif centipawn_loss < 300:
        return {
            'type': 'mistake',
            'symbol': '??',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Mistake! This significantly weakens your position.',
            'teaching': 'Before moving, ask: Does this move create any weaknesses? Are my pieces safe?'
        }
    else:
        return {
            'type': 'blunder',
            'symbol': '???',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Blunder! This loses material or position.',
            'teaching': 'Critical error! Always check: 1) Is my piece hanging? 2) Can opponent capture with check? 3) Am I walking into a tactic?'
        }

def analyze_game_with_teaching(pgn_string, progress_bar=None):
    """Enhanced game analysis with opening theory and tactical patterns"""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        return None, None, None
    
    board = game.board()
    analysis = []
    move_list = []
    tactical_motifs = []
    move_number = 1
    total_moves = len(list(game.mainline_moves()))
    
    # Reset game mainline
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    
    for idx, move in enumerate(game.mainline_moves()):
        if progress_bar:
            progress_bar.progress((idx + 1) / total_moves)
        
        # Store previous board state
        previous_board = board.copy()
        
        # Analyze position before move
        eval_before = analyze_position(board, depth=12)
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        # Get move info
        player_color = board.turn
        san_move = board.san(move)
        move_list.append(san_move)
        
        # Make move
        board.push(move)
        
        # Analyze position after move
        eval_after = analyze_position(board, depth=12)
        
        # Detect tactical motifs
        motifs = detect_tactical_motif(board, move, previous_board)
        if motifs:
            tactical_motifs.append({
                'move_number': move_number,
                'move': san_move,
                'motifs': motifs,
                'player': 'White' if player_color == chess.WHITE else 'Black'
            })
        
        # Classify move with teaching feedback
        classification = classify_move(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color
        )
        
        # Add teaching moment for critical moves
        teaching_moment = None
        if classification['type'] in ['blunder', 'mistake'] and best_move:
            teaching_moment = f"Better was {best_move}. {classification['teaching']}"
        elif classification['type'] == 'brilliant':
            teaching_moment = f"{classification['teaching']} This move shows excellent understanding!"
        
        analysis.append({
            'move_number': move_number,
            'move': move.uci(),
            'san': san_move,
            'player': 'White' if player_color == chess.WHITE else 'Black',
            'eval_before': eval_before['evaluation'],
            'eval_after': eval_after['evaluation'],
            'best_move': best_move,
            'classification': classification,
            'motifs': motifs,
            'teaching_moment': teaching_moment
        })
        
        move_number += 1
    
    # Detect opening
    opening_info = detect_opening(move_list)
    
    return analysis, opening_info, tactical_motifs

def generate_comprehensive_report(analysis, opening_info, tactical_motifs):
    """Generate detailed analysis report with strengths, weaknesses, and teaching points"""
    if not analysis:
        return {}, [], [], []
    
    weaknesses = []
    strengths = []
    teaching_points = []
    tactical_lessons = []
    
    # Count move types
    move_stats = {
        'brilliant': len([m for m in analysis if m['classification']['type'] == 'brilliant']),
        'best': len([m for m in analysis if m['classification']['type'] == 'best']),
        'good': len([m for m in analysis if m['classification']['type'] == 'good']),
        'inaccuracy': len([m for m in analysis if m['classification']['type'] == 'inaccuracy']),
        'mistake': len([m for m in analysis if m['classification']['type'] == 'mistake']),
        'blunder': len([m for m in analysis if m['classification']['type'] == 'blunder'])
    }
    
    total_moves = len(analysis)
    accuracy = ((total_moves - move_stats['blunder'] - move_stats['mistake']) / total_moves * 100) if total_moves > 0 else 0
    
    # Opening Phase Analysis (moves 1-10)
    opening_moves = [m for m in analysis if m['move_number'] <= 10]
    opening_errors = [m for m in opening_moves if m['classification']['type'] in ['mistake', 'blunder']]
    
    if len(opening_errors) >= 2:
        weaknesses.append({
            'area': '📚 Opening Knowledge',
            'severity': 'High',
            'description': f"Made {len(opening_errors)} errors in the opening phase.",
            'details': f"You struggled with {opening_info['name']}. Review the key principles for this opening."
        })
        teaching_points.append({
            'phase': 'Opening',
            'title': f"Study {opening_info['name']}",
            'lesson': f"Key ideas: {', '.join(opening_info.get('key_ideas', ['Control center', 'Develop pieces', 'King safety']))}",
            'warning': f"Common mistakes to avoid: {', '.join(opening_info.get('common_mistakes', ['Early queen moves', 'Neglecting development']))}"
        })
    elif len(opening_errors) == 0 and len(opening_moves) >= 8:
        strengths.append({
            'area': '📚 Opening Preparation',
            'description': f"Excellent opening play in the {opening_info['name']}!",
            'details': 'You followed opening principles and developed pieces efficiently.'
        })
    
    # Middlegame Analysis (moves 11-30)
    middlegame_moves = [m for m in analysis if 10 < m['move_number'] <= 30]
    middlegame_tactics = [m for m in middlegame_moves if m['motifs']]
    
    if move_stats['blunder'] >= 2:
        weaknesses.append({
            'area': '⚔️ Tactical Awareness',
            'severity': 'Critical',
            'description': f"{move_stats['blunder']} blunders detected - missing tactical threats.",
            'details': 'You need to improve calculation and threat recognition.'
        })
        teaching_points.append({
            'phase': 'Tactics',
            'title': 'Improve Tactical Vision',
            'lesson': 'Before every move, check: 1) Checks, 2) Captures, 3) Threats',
            'warning': 'Use the "Blunder Check" - ask yourself what your opponent can do after your move.'
        })
        tactical_lessons.append({
            'pattern': 'general_tactics',
            'title': 'Tactical Training Needed',
            'description': 'Practice 20-30 tactical puzzles daily',
            'resources': 'Focus on: Pins, forks, discovered attacks, and removing the defender'
        })
    
    if middlegame_tactics:
        strengths.append({
            'area': '⚔️ Tactical Play',
            'description': f"Found {len(middlegame_tactics)} tactical opportunities!",
            'details': 'Good tactical awareness in the middlegame.'
        })
    
    # Analyze specific tactical patterns
    all_motifs = [motif for move in analysis for motif in move['motifs']]
    motif_counts = {}
    for motif in all_motifs:
        motif_counts[motif] = motif_counts.get(motif, 0) + 1
    
    # Generate tactical lessons based on patterns found
    for motif, count in motif_counts.items():
        if motif in TACTICAL_PATTERNS and count >= 2:
            pattern = TACTICAL_PATTERNS[motif]
            tactical_lessons.append({
                'pattern': motif,
                'title': f"{pattern['name']} ({count} times)",
                'description': pattern['description'],
                'recognition': pattern['recognition'],
                'defense': pattern['defense'],
                'exercise': pattern['exercise']
            })
    
    # Endgame Analysis (moves 30+)
    endgame_moves = [m for m in analysis if m['move_number'] > 30]
    if endgame_moves:
        endgame_accuracy = ((len(endgame_moves) - len([m for m in endgame_moves if m['classification']['type'] in ['mistake', 'blunder']])) / len(endgame_moves) * 100)
        
        if endgame_accuracy < 70:
            weaknesses.append({
                'area': '♔ Endgame Technique',
                'severity': 'Medium',
                'description': f"Endgame accuracy: {endgame_accuracy:.1f}%",
                'details': 'Struggled to convert the position in the endgame.'
            })
            teaching_points.append({
                'phase': 'Endgame',
                'title': 'Master Basic Endgames',
                'lesson': 'Study: King and pawn endings, rook endgames, opposition, triangulation',
                'warning': 'Convert advantages by: 1) Activate king, 2) Create passed pawns, 3) Restrict opponent'
            })
        elif endgame_accuracy >= 85:
            strengths.append({
                'area': '♔ Endgame Mastery',
                'description': f"Excellent endgame play ({endgame_accuracy:.1f}% accuracy)!",
                'details': 'Strong understanding of endgame principles.'
            })
    
    # Positional Understanding
    avg_eval_swing = sum([abs(m['eval_after'] - m['eval_before']) for m in analysis]) / total_moves if total_moves > 0 else 0
    
    if avg_eval_swing > 0.5:
        weaknesses.append({
            'area': '🎯 Positional Understanding',
            'severity': 'Medium',
            'description': 'Large evaluation swings indicate positional inconsistency.',
            'details': 'Focus on improving your positional judgment and planning.'
        })
        teaching_points.append({
            'phase': 'Strategy',
            'title': 'Improve Positional Play',
            'lesson': 'Think about: Pawn structure, piece activity, king safety, weak squares',
            'warning': 'Make a plan before moving. Ask: What is my position trying to achieve?'
        })
    
    # Time management and move quality consistency
    if move_stats['inaccuracy'] > total_moves * 0.3:
        teaching_points.append({
            'phase': 'General',
            'title': 'Calculation Depth',
            'lesson': 'Spend more time calculating forcing moves (checks, captures, threats)',
            'warning': 'Use candidate moves: List 2-3 possibilities before deciding'
        })
    
    # Identify brilliant moves for positive reinforcement
    brilliant_moves = [m for m in analysis if m['classification']['type'] == 'brilliant']
    if brilliant_moves:
        for bm in brilliant_moves[:3]:  # Show up to 3 brilliant moves
            strengths.append({
                'area': '🌟 Brilliant Play',
                'description': f"Move {bm['move_number']}: {bm['san']} was brilliant!",
                'details': bm['teaching_moment'] or 'Outstanding tactical vision!'
            })
    
    # Overall performance assessment
    performance_metrics = {
        'accuracy': accuracy,
        'tactical_sharpness': (move_stats['brilliant'] + move_stats['best']) / total_moves * 100,
        'consistency': (1 - move_stats['blunder'] / max(total_moves, 1)) * 100,
        'opening_score': ((len(opening_moves) - len(opening_errors)) / max(len(opening_moves), 1)) * 100 if opening_moves else 0,
        'middlegame_score': ((len(middlegame_moves) - len([m for m in middlegame_moves if m['classification']['type'] in ['mistake', 'blunder']])) / max(len(middlegame_moves), 1)) * 100 if middlegame_moves else 0,
        'endgame_score': endgame_accuracy if endgame_moves else 0
    }
    
    return performance_metrics, weaknesses, strengths, teaching_points, tactical_lessons

def generate_study_plan(weaknesses, tactical_lessons):
    """Generate personalized study plan based on identified weaknesses"""
    study_plan = []
    
    # Priority ordering
    priority_areas = {
        '⚔️ Tactical Awareness': 1,
        '📚 Opening Knowledge': 2,
        '♔ Endgame Technique': 3,
        '🎯 Positional Understanding': 4
    }
    
    sorted_weaknesses = sorted(weaknesses, 
                               key=lambda x: priority_areas.get(x['area'], 5))
    
    for idx, weakness in enumerate(sorted_weaknesses[:3], 1):  # Top 3 priorities
        area = weakness['area']
        
        if 'Tactical' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Tactics',
                'daily_time': '20-30 minutes',
                'exercises': [
                    'Solve 20 tactical puzzles (Chess.com, Lichess, or ChessTempo)',
                    'Focus on patterns: Forks, pins, discovered attacks',
                    'Review mistakes - understand WHY you missed them'
                ],
                'weekly_goal': 'Solve 140+ puzzles with 75%+ accuracy',
                'resources': ['Chess.com Puzzles', 'Lichess Puzzle Rush', 'CT-ART tactics trainer']
            })
        
        elif 'Opening' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Opening Preparation',
                'daily_time': '15-20 minutes',
                'exercises': [
                    'Study 1-2 opening lines deeply',
                    'Learn the IDEAS behind moves, not just memorization',
                    'Play practice games in your chosen opening'
                ],
                'weekly_goal': 'Master first 10 moves of 2 openings',
                'resources': ['Lichess Opening Explorer', 'Chessable courses', 'YouTube opening guides']
            })
        
        elif 'Endgame' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Endgame Mastery',
                'daily_time': '15 minutes',
                'exercises': [
                    'Practice basic checkmates (Q+K vs K, R+K vs K)',
                    'Study King and Pawn endings',
                    'Learn key endgame principles (opposition, triangulation)'
                ],
                'weekly_goal': 'Master 5 essential endgame positions',
                'resources': ['Lichess Practice mode', 'Silman Endgame Course', '100 Endgames You Must Know']
            })
        
        elif 'Positional' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Positional Understanding',
                'daily_time': '20 minutes',
                'exercises': [
                    'Study annotated master games',
                    'Analyze pawn structures',
                    'Practice positional evaluation'
                ],
                'weekly_goal': 'Understand 3 key strategic concepts deeply',
                'resources': ['ChessBase videos', 'My System by Nimzowitsch', 'Positional play lectures']
            })
    
    # Add tactical pattern-specific training
    if tactical_lessons:
        for lesson in tactical_lessons[:2]:  # Top 2 patterns
            if lesson['pattern'] in TACTICAL_PATTERNS:
                study_plan.append({
                    'priority': len(study_plan) + 1,
                    'area': f"Master: {lesson['title']}",
                    'daily_time': '10 minutes',
                    'exercises': [
                        f"Focus puzzles on {lesson['pattern']} patterns",
                        lesson['exercise'],
                        f"Recognition tip: {lesson['recognition']}"
                    ],
                    'weekly_goal': f"Recognize {lesson['pattern']} patterns instantly",
                    'resources': ['Pattern-specific puzzle filters on tactics trainers']
                })
    
    return study_plan

# Main App Layout
st.markdown('<div class="main-header">♟️ Chess Learning Coach Pro</div>', unsafe_allow_html=True)
st.markdown("**🧠 AI-Powered Analysis | 📚 Opening Theory | ⚔️ Tactical Training | 🎯 Personalized Teaching**")

# Sidebar
with st.sidebar:
    st.header("🎯 Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Home", "📊 Analyze Game", "📚 Learn Openings", "⚔️ Tactical Patterns", "👤 Profile"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # User Profile
    st.subheader("👤 Player Profile")
    username = st.text_input("Username", st.session_state.user_profile['username'])
    st.session_state.user_profile['username'] = username
    
    st.metric("Current Rating", st.session_state.user_profile['rating'])
    st.metric("Games Analyzed", st.session_state.user_profile['games_analyzed'])
    st.metric("Tactics Found", st.session_state.user_profile['total_tactics_found'])
    
    st.markdown("---")
    
    # Engine Status
    st.subheader("⚙️ Engine Status")
    if st.session_state.engine:
        st.success("✅ Stockfish Connected")
    else:
        st.error("❌ Engine Not Available")

# Main Content
if page == "🏠 Home":
    st.header("Welcome to Chess Learning Coach Pro!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-box">
            <h3>📊 Deep Analysis</h3>
            <p>Stockfish-powered move analysis with opening theory and tactical pattern recognition</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-box">
            <h3>🎓 Personalized Teaching</h3>
            <p>Get specific feedback on each move with actionable improvement suggestions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-box">
            <h3>📈 Track Progress</h3>
            <p>Monitor tactical awareness, opening knowledge, and overall game understanding</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("🚀 Enhanced Features")
    
    tab1, tab2, tab3 = st.tabs(["Opening Analysis", "Tactical Training", "Teaching System"])
    
    with tab1:
        st.markdown("""
        ### 📚 Opening Theory Integration
        
        - **Automatic Opening Detection**: Identifies your opening and provides relevant theory
        - **Key Ideas**: Learn the strategic goals of each opening
        - **Common Mistakes**: Avoid typical errors in your chosen openings
        - **ECO Classification**: Proper opening nomenclature for study
        
        **Supported Openings:**
        - King's Pawn Games (e4)
        - Queen's Pawn Games (d4)
        - English Opening (c4)
        - Reti Opening (Nf3)
        - And many more variations!
        """)
    
    with tab2:
        st.markdown("""
        ### ⚔️ Tactical Pattern Recognition
        
        **Automatically Detected Patterns:**
        - ✓ Forks (especially knight forks)
        - ✓ Pins (absolute and relative)
        - ✓ Skewers
        - ✓ Discovered Attacks
        - ✓ Double Attacks
        - ✓ Removing the Defender
        - ✓ Back Rank Threats
        
        Each pattern includes:
        - Description and how to recognize it
        - Defensive techniques
        - Practice exercises
        """)
    
    with tab3:
        st.markdown("""
        ### 🎓 Intelligent Teaching System
        
        **Personalized Feedback:**
        - Move-by-move evaluation with explanations
        - Teaching moments for critical errors
        - Positive reinforcement for good moves
        
        **Comprehensive Reports:**
        - Strengths identification
        - Weakness analysis by game phase
        - Specific improvement recommendations
        - Customized study plans
        
        **Learning Approach:**
        1. Understand WHY moves are good/bad
        2. Learn patterns, not just moves
        3. Build systematic thinking habits
        """)

elif page == "📊 Analyze Game":
    st.header("📊 Comprehensive Game Analysis")
    
    st.info("💡 **Tip**: Paste your PGN below for in-depth analysis including opening theory, tactical patterns, and personalized teaching!")
    
    pgn_input = st.text_area(
        "Paste PGN here",
        height=250,
        placeholder="""[Event "Casual Game"]
[Site "?"]
[Date "2025.01.20"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7..."""
    )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        analysis_depth = st.slider("Analysis Depth", 10, 20, 15, 
                                  help="Higher = more accurate but slower")
    
    with col2:
        show_teaching = st.checkbox("Include Teaching Moments", value=True,
                                   help="Show detailed explanations for critical moves")
    
    with col3:
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if analyze_button and pgn_input:
        with st.spinner("🤔 Analyzing your game with Stockfish..."):
            progress_bar = st.progress(0)
            analysis, opening_info, tactical_motifs = analyze_game_with_teaching(pgn_input, progress_bar)
            
            if analysis:
                st.session_state.game_analysis = analysis
                st.session_state.opening_analysis = opening_info
                st.session_state.tactical_motifs = tactical_motifs
                st.session_state.user_profile['games_analyzed'] += 1
                st.session_state.user_profile['total_tactics_found'] += len(tactical_motifs)
                
                progress_bar.empty()
                st.success("✅ Analysis complete!")
                
                # Generate comprehensive report
                performance, weaknesses, strengths, teaching_points, tactical_lessons = generate_comprehensive_report(
                    analysis, opening_info, tactical_motifs
                )
                
                st.session_state.performance_metrics = performance
                st.session_state.weaknesses = weaknesses
                st.session_state.strengths = strengths
                st.session_state.teaching_points = teaching_points
                st.session_state.tactical_lessons = tactical_lessons
            else:
                st.error("❌ Invalid PGN format. Please check your input.")
    
    # Display Results
    if st.session_state.game_analysis:
        analysis = st.session_state.game_analysis
        opening_info = st.session_state.opening_analysis
        
        st.markdown("---")
        
        # Opening Analysis Section
        st.subheader("📚 Opening Analysis")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="opening-box">
                <h3>{opening_info.get('name', 'Unknown Opening')}</h3>
                <p><strong>ECO Code:</strong> {opening_info.get('eco', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if opening_info.get('key_ideas'):
                st.markdown("**📖 Key Ideas:**")
                for idea in opening_info['key_ideas']:
                    st.markdown(f"- ✓ {idea}")
            
            if opening_info.get('common_mistakes'):
                st.markdown("**⚠️ Common Mistakes to Avoid:**")
                for mistake in opening_info['common_mistakes']:
                    st.markdown(f"- ❌ {mistake}")
        
        with col2:
            opening_moves = [m for m in analysis if m['move_number'] <= 10]
            opening_quality = len([m for m in opening_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(opening_moves), 1) * 100
            
            st.metric("Opening Quality", f"{opening_quality:.1f}%")
            st.metric("Opening Moves", len(opening_moves))
            
            if opening_quality >= 80:
                st.success("Excellent opening preparation!")
            elif opening_quality >= 60:
                st.info("Good opening play")
            else:
                st.warning("Opening needs improvement")
        
        st.markdown("---")
        
        # Performance Dashboard
        st.subheader("📈 Performance Dashboard")
        
        if 'performance_metrics' in st.session_state:
            metrics = st.session_state.performance_metrics
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            col1.metric("Overall Accuracy", f"{metrics['accuracy']:.1f}%")
            col2.metric("Tactical Sharpness", f"{metrics['tactical_sharpness']:.1f}%")
            col3.metric("Opening", f"{metrics['opening_score']:.0f}%")
            col4.metric("Middlegame", f"{metrics['middlegame_score']:.0f}%")
            col5.metric("Endgame", f"{metrics['endgame_score']:.0f}%" if metrics['endgame_score'] > 0 else "N/A")
            
            # Performance Radar Chart
            fig = go.Figure()
            
            categories = ['Accuracy', 'Tactical<br>Sharpness', 'Opening', 'Middlegame', 'Endgame']
            values = [
                metrics['accuracy'],
                metrics['tactical_sharpness'],
                metrics['opening_score'],
                metrics['middlegame_score'],
                metrics['endgame_score'] if metrics['endgame_score'] > 0 else 50
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Your Performance',
                line_color='rgb(147, 51, 234)',
                fillcolor='rgba(147, 51, 234, 0.3)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=10)
                    )
                ),
                showlegend=False,
                height=400,
                title="Performance Analysis"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Strengths and Weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            if 'strengths' in st.session_state and st.session_state.strengths:
                st.subheader("💪 Your Strengths")
                for strength in st.session_state.strengths:
                    st.markdown(f"""
                    <div class="strength-box">
                        <strong>{strength['area']}</strong><br>
                        {strength['description']}<br>
                        <small><em>{strength.get('details', '')}</em></small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Play more accurately to identify your strengths!")
        
        with col2:
            if 'weaknesses' in st.session_state and st.session_state.weaknesses:
                st.subheader("⚠️ Areas to Improve")
                for weakness in st.session_state.weaknesses:
                    severity_color = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}
                    st.markdown(f"""
                    <div class="weakness-box">
                        <strong>{weakness['area']}</strong> {severity_color.get(weakness['severity'], '🔵')}<br>
                        {weakness['description']}<br>
                        <small><em>{weakness.get('details', '')}</em></small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No significant weaknesses detected!")
        
        st.markdown("---")
        
        # Tactical Patterns Found
        if 'tactical_motifs' in st.session_state and st.session_state.tactical_motifs:
            st.subheader("⚔️ Tactical Patterns Detected")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                for motif_data in st.session_state.tactical_motifs[:10]:
                    motif_str = ', '.join([m.replace('_', ' ').title() for m in motif_data['motifs']])
                    st.markdown(f"""
                    <div class="tactical-box">
                        <strong>Move {motif_data['move_number']}</strong>: {motif_data['move']} 
                        ({motif_data['player']})<br>
                        <em>Patterns: {motif_str}</em>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Tactical Moves", len(st.session_state.tactical_motifs))
                st.metric("Patterns Found", len(set([m for data in st.session_state.tactical_motifs for m in data['motifs']])))
        
        st.markdown("---")
        
        # Teaching Points
        if 'teaching_points' in st.session_state and st.session_state.teaching_points:
            st.subheader("🎓 Teaching & Learning Points")
            
            for idx, point in enumerate(st.session_state.teaching_points, 1):
                st.markdown(f"""
                <div class="teaching-box">
                    <h4>{idx}. {point['title']} ({point['phase']})</h4>
                    <p><strong>💡 Lesson:</strong> {point['lesson']}</p>
                    <p><strong>⚠️ Remember:</strong> {point['warning']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Personalized Study Plan
        if 'weaknesses' in st.session_state and 'tactical_lessons' in st.session_state:
            st.subheader("📋 Your Personalized Study Plan")
            
            study_plan = generate_study_plan(
                st.session_state.weaknesses,
                st.session_state.get('tactical_lessons', [])
            )
            
            for plan_item in study_plan:
                with st.expander(f"Priority {plan_item['priority']}: {plan_item['area']}", expanded=(plan_item['priority'] == 1)):
                    st.markdown(f"**⏱ Daily Time:** {plan_item['daily_time']}")
                    st.markdown(f"**🎯 Weekly Goal:** {plan_item['weekly_goal']}")
                    
                    st.markdown("**📝 Daily Exercises:**")
                    for exercise in plan_item['exercises']:
                        st.markdown(f"- {exercise}")
                    
                    st.markdown("**📚 Recommended Resources:**")
                    for resource in plan_item['resources']:
                        st.markdown(f"- {resource}")
        
        st.markdown("---")
        
        # Move-by-Move Analysis
        st.subheader("📝 Detailed Move Analysis")
        
        show_all = st.checkbox("Show all moves", value=False)
        
        if show_all:
            display_moves = analysis
        else:
            # Show only critical moves (mistakes and better)
            display_moves = [m for m in analysis if m['classification']['type'] in ['brilliant', 'best', 'mistake', 'blunder'] or m.get('teaching_moment')]
        
        for move_data in display_moves[:50]:  # Limit display
            class_type = move_data['classification']['type']
            class_color = {
                'brilliant': '🟣',
                'best': '🟢',
                'good': '🔵',
                'inaccuracy': '🟡',
                'mistake': '🟠',
                'blunder': '🔴'
            }
            
            with st.expander(
                f"{class_color.get(class_type, '⚪')} Move {move_data['move_number']}: {move_data['san']} ({move_data['player']}) - {move_data['classification']['type'].title()} {move_data['classification']['symbol']}",
                expanded=False
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Evaluation:** {move_data['eval_after']:+.2f}")
                    st.markdown(f"**CP Loss:** {move_data['classification']['cp_loss']}")
                    st.markdown(f"**{move_data['classification']['feedback']}**")
                    
                    if move_data.get('teaching_moment') and show_teaching:
                        st.info(f"🎓 {move_data['teaching_moment']}")
                    
                    if move_data['motifs']:
                        st.success(f"⚔️ Tactical elements: {', '.join([m.replace('_', ' ').title() for m in move_data['motifs']])}")
                
                with col2:
                    if move_data['best_move'] and move_data['best_move'] != move_data['move']:
                        st.markdown(f"**Better:** {move_data['best_move']}")

elif page == "📚 Learn Openings":
    st.header("📚 Opening Theory Database")
    
    st.markdown("""
    Understanding opening principles is crucial for chess improvement. 
    Study the key ideas behind each opening, not just memorizing moves!
    """)
    
    st.markdown("---")
    
    # Opening selector
    opening_names = list(set([info['name'] for info in OPENING_DATABASE.values()]))
    selected_opening = st.selectbox("Select an opening to study:", ["All Openings"] + opening_names)
    
    if selected_opening == "All Openings":
        for moves, info in OPENING_DATABASE.items():
            with st.expander(f"{info['name']} ({info['eco']})"):
                st.markdown(f"**Move sequence:** {moves}")
                
                if info.get('key_ideas'):
                    st.markdown("**🎯 Key Ideas:**")
                    for idea in info['key_ideas']:
                        st.markdown(f"- {idea}")
                
                if info.get('common_mistakes'):
                    st.markdown("**⚠️ Common Mistakes:**")
                    for mistake in info['common_mistakes']:
                        st.markdown(f"- {mistake}")
    else:
        for moves, info in OPENING_DATABASE.items():
            if info['name'] == selected_opening:
                st.subheader(f"{info['name']}")
                st.markdown(f"**ECO Code:** {info['eco']}")
                st.markdown(f"**Starting Moves:** {moves}")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🎯 Key Strategic Ideas")
                    if info.get('key_ideas'):
                        for idx, idea in enumerate(info['key_ideas'], 1):
                            st.markdown(f"{idx}. {idea}")
                    else:
                        st.info("No specific ideas listed yet")
                
                with col2:
                    st.markdown("### ⚠️ Mistakes to Avoid")
                    if info.get('common_mistakes'):
                        for idx, mistake in enumerate(info['common_mistakes'], 1):
                            st.markdown(f"{idx}. {mistake}")
                    else:
                        st.info("No common mistakes listed yet")

elif page == "⚔️ Tactical Patterns":
    st.header("⚔️ Master Tactical Patterns")
    
    st.markdown("""
    Tactics are the building blocks of chess combinations. 
    Learn to recognize these patterns instantly to improve your tactical vision!
    """)
    
    st.markdown("---")
    
    # Display all tactical patterns
    for pattern_key, pattern_info in TACTICAL_PATTERNS.items():
        with st.expander(f"🎯 {pattern_info['name']}", expanded=False):
            st.markdown(f"**Description:** {pattern_info['description']}")
            st.markdown(f"**How to recognize:** {pattern_info['recognition']}")
            st.markdown(f"**How to defend:** {pattern_info['defense']}")
            st.markdown(f"**Practice exercise:** {pattern_info['exercise']}")
            
            st.markdown("---")
            st.info(f"💡 **Training Tip:** Spend 10 minutes daily practicing {pattern_info['name']} puzzles")

elif page == "👤 Profile":
    st.header("👤 Your Chess Profile")
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Rating", st.session_state.user_profile['rating'])
    col2.metric("Games Analyzed", st.session_state.user_profile['games_analyzed'])
    col3.metric("Tactics Found", st.session_state.user_profile['total_tactics_found'])
    
    st.markdown("---")
    
    if 'performance_metrics' in st.session_state:
        st.subheader("📊 Your Performance Metrics")
        
        metrics = st.session_state.performance_metrics
        
        # Create detailed metrics display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Game Phase Scores")
            st.progress(metrics['opening_score'] / 100, text=f"Opening: {metrics['opening_score']:.0f}%")
            st.progress(metrics['middlegame_score'] / 100, text=f"Middlegame: {metrics['middlegame_score']:.0f}%")
            if metrics['endgame_score'] > 0:
                st.progress(metrics['endgame_score'] / 100, text=f"Endgame: {metrics['endgame_score']:.0f}%")
        
        with col2:
            st.markdown("### Overall Stats")
            st.progress(metrics['accuracy'] / 100, text=f"Accuracy: {metrics['accuracy']:.1f}%")
            st.progress(metrics['tactical_sharpness'] / 100, text=f"Tactical Sharpness: {metrics['tactical_sharpness']:.1f}%")
            st.progress(metrics['consistency'] / 100, text=f"Consistency: {metrics['consistency']:.1f}%")
    else:
        st.info("📊 Analyze a game to see your detailed performance metrics!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p><strong>Chess Learning Coach Pro</strong> | Powered by Stockfish Engine</p>
    <p>🧠 Advanced Analysis | 📚 Opening Theory | ⚔️ Tactical Training | 🎓 Personalized Teaching</p>
    <p>Built with ❤️ using Streamlit | © 2025</p>
</div>
""", unsafe_allow_html=True)
