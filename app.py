"""
Chess Learning Coach Pro - Enhanced Streamlit Application
World-class chess analysis inspired by Chess.com, Lichess, and ChessBase

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
import time

# Page configuration
st.set_page_config(
    page_title="Chess Learning Coach Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state FIRST
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
        'opening_repertoire': [],
        'performance_history': []
    }
if 'current_position' not in st.session_state:
    st.session_state.current_position = 0
if 'analysis_complete' not in st.session_state:
    st.analysis_complete = False
if 'move_annotations' not in st.session_state:
    st.session_state.move_annotations = {}
if 'game_pgn' not in st.session_state:
    st.session_state.game_pgn = ""

# Enhanced CSS - Chess.com/Lichess inspired
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
    }
    
    /* Header */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .sub-header {
        text-align: center;
        color: #a0a0c0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Chess.com Style Cards */
    .analysis-card {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(102, 126, 234, 0.3);
    }
    
    /* Lichess Style Metrics */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: all 0.3s;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* ChessBase Style Move Analysis */
    .move-row {
        background: rgba(45, 45, 68, 0.6);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border-left: 4px solid transparent;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .move-row:hover {
        background: rgba(60, 60, 85, 0.8);
        transform: translateX(4px);
    }
    
    .move-brilliant {
        border-left-color: #9333ea !important;
        background: rgba(147, 51, 234, 0.1);
    }
    
    .move-best {
        border-left-color: #10b981 !important;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .move-good {
        border-left-color: #3b82f6 !important;
        background: rgba(59, 130, 246, 0.1);
    }
    
    .move-inaccuracy {
        border-left-color: #f59e0b !important;
        background: rgba(245, 158, 11, 0.1);
    }
    
    .move-mistake {
        border-left-color: #f97316 !important;
        background: rgba(249, 115, 22, 0.1);
    }
    
    .move-blunder {
        border-left-color: #ef4444 !important;
        background: rgba(239, 68, 68, 0.1);
    }
    
    /* Evaluation Bar */
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
    
    .eval-bar-black {
        background: linear-gradient(180deg, #2d2d44 0%, #1a1a2e 100%);
    }
    
    /* Opening Explorer */
    .opening-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    /* Tactical Motif Tags */
    .tactic-tag {
        display: inline-block;
        background: rgba(147, 51, 234, 0.2);
        border: 1px solid rgba(147, 51, 234, 0.5);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.85rem;
        font-weight: 600;
        color: #c084fc;
    }
    
    /* Progress Bars */
    .accuracy-bar {
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .accuracy-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
        transition: width 0.5s ease;
    }
    
    /* Game Phase Indicator */
    .phase-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .phase-opening {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .phase-middlegame {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .phase-endgame {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    /* Interactive Board Container */
    .board-container {
        background: rgba(45, 45, 68, 0.6);
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    
    /* Report Sections */
    .report-section {
        background: linear-gradient(135deg, #2d2d44 0%, #1f1f2e 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* Strengths & Weaknesses */
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
    
    /* Study Plan */
    .study-plan-card {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        color: #1a1a2e;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5);
    }
    
    /* Chess.com Style Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(45, 45, 68, 0.4);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #a0a0c0;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Move Navigation */
    .move-nav {
        background: rgba(45, 45, 68, 0.6);
        padding: 1rem;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Annotations */
    .annotation-box {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Performance Chart */
    .chart-container {
        background: rgba(45, 45, 68, 0.4);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Opening Database (Enhanced with more details)
OPENING_DATABASE = {
    'e4 e5 Nf3 Nc6 Bb5': {
        'name': 'Ruy Lopez (Spanish Opening)',
        'eco': 'C60-C99',
        'key_ideas': [
            'Control center with e4, develop pieces rapidly',
            'Pressure on e5 pawn and c6 knight',
            'Castle kingside early for safety',
            'Prepare d4 break in center',
            'Maneuver knight to better squares'
        ],
        'common_mistakes': [
            'Moving queen too early (Qh5)',
            'Pushing a4 prematurely',
            'Neglecting d4 break',
            'Allowing ...Nd4 fork'
        ],
        'typical_plans': {
            'white': 'Control center, prepare d4, attack on kingside',
            'black': 'Counter in center with ...d5 or on queenside with ...a6, ...b5'
        }
    },
    'e4 c5': {
        'name': 'Sicilian Defense',
        'eco': 'B20-B99',
        'key_ideas': [
            'Asymmetrical pawn structure favors Black',
            'Black gets counterplay on queenside',
            'White attacks on kingside',
            'Open c-file for Black\'s rooks',
            'Central pawn majority for White'
        ],
        'common_mistakes': [
            'Allowing Nf3-d4-xc5 without preparation',
            'Weakening d5 square permanently',
            'Slow piece development',
            'Moving queen into attacks'
        ],
        'typical_plans': {
            'white': 'Control d5, attack on kingside with f4-f5',
            'black': 'Counterplay on queenside, pressure on d4'
        }
    },
    'e4 e5 Nf3 Nc6 Bc4': {
        'name': 'Italian Game',
        'eco': 'C50-C54',
        'key_ideas': [
            'Quick development with Bc4',
            'Pressure on f7 weak point',
            'Central control with d3/d4',
            'Flexible piece placement'
        ],
        'common_mistakes': [
            'Pushing c3 and d4 without preparation',
            'Neglecting king safety',
            'Allowing ...Ng4 tactics'
        ],
        'typical_plans': {
            'white': 'Central break with d4, kingside attack',
            'black': 'Solid development, counter with ...d5'
        }
    },
    'd4 d5 c4': {
        'name': "Queen's Gambit",
        'eco': 'D00-D69',
        'key_ideas': [
            'Control center with pawns',
            'Develop pieces behind pawns',
            'Fight for e4 and e5 squares',
            'Pressure on d5 pawn'
        ],
        'common_mistakes': [
            'Taking on c4 prematurely',
            'Locking in light-squared bishop',
            'Passive piece placement'
        ],
        'typical_plans': {
            'white': 'Build strong center, pressure d5',
            'black': 'Challenge center with ...c5 or ...e5'
        }
    },
    'd4 Nf6 c4 e6': {
        'name': 'Nimzo-Indian Defense',
        'eco': 'E20-E59',
        'key_ideas': [
            'Hypermodern control of center',
            'Pin white knight with Bb4',
            'Damage white pawn structure',
            'Flexible pawn breaks'
        ],
        'common_mistakes': [
            'Allowing e4 without counterplay',
            'Passive piece placement',
            'Not exploiting doubled pawns'
        ],
        'typical_plans': {
            'white': 'Dominate center, exploit bishop pair',
            'black': 'Target weak pawns, blockade center'
        }
    },
    'e4 e6': {
        'name': 'French Defense',
        'eco': 'C00-C19',
        'key_ideas': [
            'Solid pawn chain d5-e6',
            'Challenge center with ...c5',
            'Develop light-squared bishop before e6',
            'Counterplay on queenside'
        ],
        'common_mistakes': [
            'Locking in light-squared bishop permanently',
            'Allowing white\'s e5 advance without plan',
            'Too passive in middlegame'
        ],
        'typical_plans': {
            'white': 'Space advantage, kingside attack',
            'black': 'Undermine e5, play ...f6 or ...c5'
        }
    },
    'e4 c6': {
        'name': 'Caro-Kann Defense',
        'eco': 'B10-B19',
        'key_ideas': [
            'Solid structure, hard to break',
            'Develop light-squared bishop actively',
            'Safe king position',
            'Gradual counterplay'
        ],
        'common_mistakes': [
            'Too passive development',
            'Not challenging center',
            'Allowing white too much space'
        ],
        'typical_plans': {
            'white': 'Space advantage, piece pressure',
            'black': 'Solid defense, break with ...c5 or ...e6-e5'
        }
    },
    'Nf3 d5 c4': {
        'name': 'Reti Opening',
        'eco': 'A04-A09',
        'key_ideas': [
            'Hypermodern approach',
            'Control center from distance',
            'Flexible pawn structure',
            'Often transposes to other openings'
        ],
        'common_mistakes': [
            'Lack of concrete plan',
            'Allowing strong center without pressure',
            'Slow development'
        ],
        'typical_plans': {
            'white': 'Fianchetto bishop, flexible center',
            'black': 'Establish center, rapid development'
        }
    },
    'c4': {
        'name': 'English Opening',
        'eco': 'A10-A39',
        'key_ideas': [
            'Control d5 square from distance',
            'Reversed Sicilian with ...e5',
            'Flexible pawn structure',
            'Often fianchetto kingside'
        ],
        'common_mistakes': [
            'No clear plan',
            'Weak d4 square',
            'Passive development'
        ],
        'typical_plans': {
            'white': 'Control center, flexible setup',
            'black': 'Counter in center or flanks'
        }
    }
}

# Enhanced Tactical Patterns
TACTICAL_PATTERNS = {
    'fork': {
        'name': 'Fork',
        'description': 'One piece attacks two or more enemy pieces simultaneously',
        'recognition': 'Knights excel at forks - look for squares where they attack multiple pieces. Queens can fork along diagonals, ranks, and files.',
        'defense': 'Keep pieces protected and avoid placing valuable pieces on the same diagonal/file/rank where they can be forked',
        'exercise': 'Practice knight fork puzzles daily. Study the "Family Fork" pattern (knight forks king and queen)',
        'examples': 'Nc7+ forking king and rook, Qd4 attacking rook on a1 and h8',
        'frequency': 'Very Common',
        'difficulty': 'Beginner'
    },
    'pin': {
        'name': 'Pin',
        'description': 'A piece cannot move without exposing a more valuable piece behind it to attack',
        'recognition': 'Look for pieces aligned with enemy king/queen on same file, rank, or diagonal. Bishops, rooks, and queens create pins.',
        'defense': 'Break pins with pawn moves (h3 vs Bg4), block with less valuable pieces, or move the pinned piece with tempo',
        'exercise': 'Study absolute pins (with king) vs relative pins. Practice exploiting pinned pieces.',
        'examples': 'Bg5 pinning knight to queen, Rd1 pinning rook to king',
        'frequency': 'Very Common',
        'difficulty': 'Beginner'
    },
    'skewer': {
        'name': 'Skewer (Reverse Pin)',
        'description': 'A valuable piece is attacked and must move, exposing a piece behind it',
        'recognition': 'Check if forcing the front piece to move reveals an attack on a piece behind. Common with checks.',
        'defense': 'Keep king and valuable pieces away from same diagonals/files. Be aware of piece alignments.',
        'exercise': 'Practice rook and bishop skewers in endgames. Study king and rook alignments.',
        'examples': 'Rc8+ forcing king to move and capturing rook, Bb5+ skewering king and bishop',
        'frequency': 'Common',
        'difficulty': 'Beginner'
    },
    'discovered_attack': {
        'name': 'Discovered Attack',
        'description': 'Moving one piece reveals an attack from another piece behind it',
        'recognition': 'Look for pieces on the same line with enemy king/queen between them. Moving the front piece unleashes the back piece.',
        'defense': 'Be aware of piece alignments. Block the attacking line or move the target piece.',
        'exercise': 'Study discovered check patterns - the most powerful type. Practice recognizing batteries.',
        'examples': 'Moving knight to reveal bishop check, rook moving to reveal queen attack',
        'frequency': 'Common',
        'difficulty': 'Intermediate'
    },
    'double_attack': {
        'name': 'Double Attack',
        'description': 'Creating two separate threats simultaneously that cannot both be defended',
        'recognition': 'Queens and knights are masters of double attacks. Look for moves that create multiple threats.',
        'defense': 'Deal with the more dangerous threat first. Sometimes sacrificing material is necessary.',
        'exercise': 'Practice queen double attack puzzles. Study knight outpost positions.',
        'examples': 'Qh5 attacking h7 and f7, knight fork attacking two rooks',
        'frequency': 'Very Common',
        'difficulty': 'Beginner'
    },
    'removing_defender': {
        'name': 'Removing the Defender',
        'description': 'Capture, deflect, or decoy the piece defending a key square or piece',
        'recognition': 'Identify overworked pieces defending multiple things. Remove or deflect them.',
        'defense': 'Ensure multiple defenders for key squares and pieces. Don\'t overload pieces with defensive duties.',
        'exercise': 'Study deflection sacrifices (Rxd8+ deflecting queen from defense). Practice identifying overworked pieces.',
        'examples': 'Rxd8 removing defender, then Qxh7#. Deflecting knight from f6 to capture queen.',
        'frequency': 'Common',
        'difficulty': 'Intermediate'
    },
    'back_rank': {
        'name': 'Back Rank Mate',
        'description': 'Checkmate on the back rank when king has no escape squares, trapped by own pieces',
        'recognition': 'Look for king trapped on first/eighth rank by own pawns with no escape. Deliver mate with rook or queen.',
        'defense': 'Always create "luft" (escape square) for your king by moving h3/h6 or g3/g6 pawn.',
        'exercise': 'Practice back rank patterns with rooks and queens. Study defensive techniques.',
        'examples': 'Rd8# when king on e8 with pawns on f7, g7, h7',
        'frequency': 'Common',
        'difficulty': 'Beginner'
    },
    'deflection': {
        'name': 'Deflection',
        'description': 'Force an enemy piece away from a key square or defensive duty',
        'recognition': 'Find pieces with multiple defensive responsibilities. Force them to abandon one.',
        'defense': 'Don\'t overload pieces with too many tasks. Maintain piece coordination.',
        'exercise': 'Study sacrifice patterns that deflect defenders. Practice recognizing overworked pieces.',
        'examples': 'Rxd8+ deflecting queen, then Qxh7#',
        'frequency': 'Common',
        'difficulty': 'Intermediate'
    },
    'interference': {
        'name': 'Interference',
        'description': 'A piece moves to block the line between two enemy pieces',
        'recognition': 'Look for opportunities to cut connections between enemy pieces, especially defensive ones.',
        'defense': 'Maintain piece coordination. Avoid situations where pieces defend each other along lines.',
        'exercise': 'Study interference sacrifices in master games.',
        'examples': 'Nd5 blocking the connection between rook and bishop',
        'frequency': 'Uncommon',
        'difficulty': 'Advanced'
    },
    'zwischenzug': {
        'name': 'Zwischenzug (In-Between Move)',
        'description': 'An unexpected intermediate move inserted before making an expected capture or move',
        'recognition': 'Before making expected moves, check for forcing moves (checks, captures, threats).',
        'defense': 'Always look for opponent\'s checks and captures before assuming a sequence.',
        'exercise': 'Study tactical combinations with surprise checks. Practice calculation depth.',
        'examples': 'Instead of recapturing immediately, play Qh5+ first',
        'frequency': 'Uncommon',
        'difficulty': 'Advanced'
    }
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
        
        st.warning("⚠️ Stockfish engine not found. Install Stockfish for full analysis features.")
        return None
    except Exception as e:
        st.error(f"Error initializing Stockfish: {e}")
        return None

if st.session_state.engine is None:
    st.session_state.engine = initialize_engine()

def render_board_svg(board, size=400, highlighted_squares=None, arrows=None):
    """Render chess board with highlighting and arrows"""
    try:
        if arrows:
            svg = chess.svg.board(board, size=size, squares=highlighted_squares, arrows=arrows)
        elif highlighted_squares:
            svg = chess.svg.board(board, size=size, squares=highlighted_squares)
        else:
            svg = chess.svg.board(board, size=size)
        b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        html = f'<div class="board-container"><img src="data:image/svg+xml;base64,{b64}"/></div>'
        return html
    except:
        return "<p>Error rendering board</p>"

def analyze_position(board, depth=18):
    """Enhanced position analysis with multiple lines"""
    if st.session_state.engine is None:
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None,
            'pv': [],
            'top_moves': []
        }
    
    try:
        # Main analysis
        info = st.session_state.engine.analyse(
            board, 
            chess.engine.Limit(depth=depth),
            multipv=3  # Get top 3 moves
        )
        
        if isinstance(info, list):
            main_info = info[0]
        else:
            main_info = info
        
        score = main_info['score'].relative
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() is not None else 0
        best_move = main_info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        pv = main_info.get('pv', [])[:5]
        
        # Get alternative moves if multipv
        top_moves = []
        if isinstance(info, list):
            for line in info[:3]:
                move = line.get('pv', [None])[0]
                if move:
                    move_score = line['score'].relative
                    move_eval = move_score.score(mate_score=10000) / 100.0 if move_score.score() is not None else 0
                    top_moves.append({
                        'move': move.uci(),
                        'eval': move_eval,
                        'pv': [m.uci() for m in line.get('pv', [])[:3]]
                    })
        
        return {
            'evaluation': evaluation,
            'best_move': best_move.uci() if best_move else None,
            'mate_in': mate_in,
            'pv': [move.uci() for move in pv],
            'top_moves': top_moves
        }
    except Exception as e:
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None,
            'pv': [],
            'top_moves': []
        }

def render_evaluation_bar(eval_score, mate_in=None, height=400):
    """Render Chess.com style evaluation bar"""
    if mate_in is not None:
        white_height = 100 if mate_in > 0 else 0
    else:
        # Convert evaluation to percentage (clamped between -10 and +10)
        clamped = max(-10, min(10, eval_score))
        white_height = 50 + (clamped / 20 * 50)  # 0-100%
    
    black_height = 100 - white_height
    
    eval_display = f"M{abs(mate_in)}" if mate_in else f"{eval_score:+.1f}"
    
    html = f"""
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
    return html

def detect_opening(moves_list, board_positions):
    """Enhanced opening detection with position matching"""
    move_string = ' '.join(moves_list[:12])
    
    best_match = None
    max_match_length = 0
    
    for pattern, opening_info in OPENING_DATABASE.items():
        if pattern in move_string:
            if len(pattern) > max_match_length:
                max_match_length = len(pattern)
                best_match = opening_info
    
    if best_match:
        return best_match
    
    # Fallback detection
    if moves_list:
        first_move = moves_list[0]
        if first_move == 'e4':
            if len(moves_list) > 1:
                if moves_list[1] == 'e5':
                    if len(moves_list) > 4 and 'Bb5' in moves_list[2:6]:
                        return OPENING_DATABASE.get('e4 e5 Nf3 Nc6 Bb5', {
                            'name': 'Ruy Lopez',
                            'eco': 'C60',
                            'key_ideas': ['Control center', 'Develop pieces'],
                            'common_mistakes': [],
                            'typical_plans': {'white': '', 'black': ''}
                        })
                    elif len(moves_list) > 4 and 'Bc4' in moves_list[2:6]:
                        return OPENING_DATABASE.get('e4 e5 Nf3 Nc6 Bc4', {
                            'name': 'Italian Game',
                            'eco': 'C50',
                            'key_ideas': ['Quick development', 'Attack f7'],
                            'common_mistakes': [],
                            'typical_plans': {'white': '', 'black': ''}
                        })
                    return {'name': 'Open Game', 'eco': 'C20', 'key_ideas': [], 'common_mistakes': [], 'typical_plans': {'white': '', 'black': ''}}
                elif moves_list[1] == 'c5':
                    return OPENING_DATABASE.get('e4 c5', {
                        'name': 'Sicilian Defense',
                        'eco': 'B20',
                        'key_ideas': [],
                        'common_mistakes': [],
                        'typical_plans': {'white': '', 'black': ''}
                    })
                elif moves_list[1] == 'e6':
                    return OPENING_DATABASE.get('e4 e6', {
                        'name': 'French Defense',
                        'eco': 'C00',
                        'key_ideas': [],
                        'common_mistakes': [],
                        'typical_plans': {'white': '', 'black': ''}
                    })
                elif moves_list[1] == 'c6':
                    return OPENING_DATABASE.get('e4 c6', {
                        'name': 'Caro-Kann Defense',
                        'eco': 'B10',
                        'key_ideas': [],
                        'common_mistakes': [],
                        'typical_plans': {'white': '', 'black': ''}
                    })
        elif first_move == 'd4':
            if len(moves_list) > 2 and moves_list[1] == 'd5' and moves_list[2] == 'c4':
                return OPENING_DATABASE.get('d4 d5 c4', {
                    'name': "Queen's Gambit",
                    'eco': 'D00',
                    'key_ideas': [],
                    'common_mistakes': [],
                    'typical_plans': {'white': '', 'black': ''}
                })
            elif len(moves_list) > 3 and moves_list[1] == 'Nf6' and moves_list[2] == 'c4' and moves_list[3] == 'e6':
                return OPENING_DATABASE.get('d4 Nf6 c4 e6', {
                    'name': 'Nimzo-Indian Defense',
                    'eco': 'E20',
                    'key_ideas': [],
                    'common_mistakes': [],
                    'typical_plans': {'white': '', 'black': ''}
                })
            return {'name': "Queen's Pawn Opening", 'eco': 'D00', 'key_ideas': [], 'common_mistakes': [], 'typical_plans': {'white': '', 'black': ''}}
        elif first_move in ['Nf3', 'c4']:
            return OPENING_DATABASE.get(first_move if first_move == 'c4' else 'Nf3 d5 c4', {
                'name': 'Reti/English Opening',
                'eco': 'A04',
                'key_ideas': [],
                'common_mistakes': [],
                'typical_plans': {'white': '', 'black': ''}
            })
    
    return {
        'name': 'Unknown Opening',
        'eco': 'A00',
        'key_ideas': ['Develop pieces', 'Control center', 'Castle early'],
        'common_mistakes': ['Moving same piece twice', 'Early queen moves'],
        'typical_plans': {'white': 'Solid development', 'black': 'Counter in center'}
    }

def detect_tactical_motif(board, move, previous_board):
    """Enhanced tactical pattern detection"""
    motifs = []
    from_piece = previous_board.piece_at(move.from_square)
    
    if not from_piece:
        return motifs
    
    # Captures
    if board.is_capture(move):
        motifs.append('capture')
        to_piece = previous_board.piece_at(move.to_square)
        if to_piece:
            if from_piece.piece_type < to_piece.piece_type:
                motifs.append('winning_capture')
            elif from_piece.piece_type == to_piece.piece_type:
                motifs.append('exchange')
    
    # Checks and checkmate
    if board.is_check():
        motifs.append('check')
        if board.is_checkmate():
            motifs.append('checkmate')
            return motifs
    
    # Fork detection (enhanced)
    attacks = list(board.attacks(move.to_square))
    valuable_attacks = [sq for sq in attacks if board.piece_at(sq) and 
                       board.piece_at(sq).color != from_piece.color and
                       board.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK, chess.KING]]
    
    if len(valuable_attacks) >= 2:
        motifs.append('fork')
        if chess.KING in [board.piece_at(sq).piece_type for sq in valuable_attacks]:
            motifs.append('royal_fork')
    
    # Pin detection
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color != from_piece.color:
            attackers = board.attackers(from_piece.color, square)
            if move.to_square in attackers:
                # Check if there's a more valuable piece behind
                direction = chess.square_file(square) - chess.square_file(move.to_square)
                if abs(direction) <= 1:  # Same file or adjacent
                    for behind_sq in chess.SQUARES:
                        behind_piece = board.piece_at(behind_sq)
                        if (behind_piece and behind_piece.color == piece.color and
                            behind_piece.piece_type > piece.piece_type):
                            motifs.append('pin')
                            break
    
    # Discovered attack
    if is_discovered_attack(previous_board, move):
        motifs.append('discovered_attack')
        if board.is_check():
            motifs.append('discovered_check')
    
    # Skewer
    if is_creating_skewer(board, move):
        motifs.append('skewer')
    
    # Back rank threats
    if is_back_rank_threat(board, move):
        motifs.append('back_rank')
    
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

def is_creating_skewer(board, move):
    """Check if move creates a skewer"""
    piece = board.piece_at(move.to_square)
    if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
        return False
    
    attacks = board.attacks(move.to_square)
    for square in attacks:
        target = board.piece_at(square)
        if target and target.color != piece.color and target.piece_type in [chess.QUEEN, chess.KING]:
            return True
    return False

def is_back_rank_threat(board, move):
    """Check for back rank mate threats"""
    if not board.is_check():
        return False
    
    king_square = board.king(not board.turn)
    if king_square is None:
        return False
    
    rank = chess.square_rank(king_square)
    if (rank == 0 and not board.turn) or (rank == 7 and board.turn):
        # King on back rank
        escape_squares = list(board.attacks(king_square))
        can_escape = any(board.piece_at(sq) is None or 
                        board.piece_at(sq).color == board.turn 
                        for sq in escape_squares)
        return not can_escape
    return False

def classify_move(eval_before, eval_after, is_best_move, player_color, best_move_eval=None):
    """Enhanced move classification"""
    if player_color == chess.BLACK:
        eval_before = -eval_before
        eval_after = -eval_after
    
    centipawn_loss = (eval_before - eval_after) * 100
    
    # Brilliant move detection
    if centipawn_loss < -50 and not is_best_move:
        return {
            'type': 'brilliant',
            'symbol': '!!',
            'cp_loss': int(centipawn_loss),
            'feedback': '✨ Brilliant! A stunning move that significantly improves your position!',
            'teaching': 'This move shows exceptional tactical vision and deep calculation!',
            'color': '#9333ea'
        }
    
    if is_best_move or centipawn_loss < 10:
        return {
            'type': 'best',
            'symbol': '!',
            'cp_loss': int(centipawn_loss),
            'feedback': '✓ Best move! Excellent choice.',
            'teaching': 'Perfect execution - you found the engine\'s top choice.',
            'color': '#10b981'
        }
    
    if centipawn_loss < 50:
        return {
            'type': 'good',
            'symbol': '',
            'cp_loss': int(centipawn_loss),
            'feedback': 'Good move maintaining your position.',
            'teaching': 'Solid play. Keep this accuracy up!',
            'color': '#3b82f6'
        }
    
    if centipawn_loss < 100:
        return {
            'type': 'inaccuracy',
            'symbol': '?!',
            'cp_loss': int(centipawn_loss),
            'feedback': '⚠ Inaccuracy - a better move existed.',
            'teaching': 'Take more time here. Look for active piece moves and tactical opportunities.',
            'color': '#f59e0b'
        }
    
    if centipawn_loss < 300:
        return {
            'type': 'mistake',
            'symbol': '?',
            'cp_loss': int(centipawn_loss),
            'feedback': '❌ Mistake! This weakens your position significantly.',
            'teaching': 'Before moving, check: 1) Are my pieces safe? 2) Am I creating weaknesses? 3) What can opponent do?',
            'color': '#f97316'
        }
    
    return {
        'type': 'blunder',
        'symbol': '??',
        'cp_loss': int(centipawn_loss),
        'feedback': '💥 Blunder! Critical error losing material or position.',
        'teaching': 'STOP and THINK! Always check for: Checks, Captures, Attacks on your pieces before moving!',
        'color': '#ef4444'
    }

def analyze_game_with_teaching(pgn_string, progress_callback=None):
    """Comprehensive game analysis with enhanced features"""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        return None, None, None, None
    
    board = game.board()
    analysis = []
    move_list = []
    tactical_motifs = []
    board_positions = []
    move_number = 1
    
    total_moves = len(list(game.mainline_moves()))
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    
    for idx, move in enumerate(game.mainline_moves()):
        if progress_callback:
            progress_callback((idx + 1) / total_moves)
        
        previous_board = board.copy()
        board_positions.append(board.fen())
        
        # Analyze before move
        eval_before = analyze_position(board, depth=15)
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        player_color = board.turn
        san_move = board.san(move)
        move_list.append(san_move)
        
        # Make move
        board.push(move)
        
        # Analyze after move
        eval_after = analyze_position(board, depth=15)
        
        # Detect tactics
        motifs = detect_tactical_motif(board, move, previous_board)
        if motifs:
            tactical_motifs.append({
                'move_number': move_number,
                'move': san_move,
                'motifs': motifs,
                'player': 'White' if player_color == chess.WHITE else 'Black',
                'fen': board.fen()
            })
        
        # Classify move
        classification = classify_move(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color,
            eval_before.get('evaluation')
        )
        
        # Teaching moment
        teaching_moment = None
        if classification['type'] in ['blunder', 'mistake'] and best_move:
            teaching_moment = f"Better: {best_move}. {classification['teaching']}"
        elif classification['type'] == 'brilliant':
            teaching_moment = classification['teaching']
        
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
            'top_moves': eval_before.get('top_moves', []),
            'classification': classification,
            'motifs': motifs,
            'teaching_moment': teaching_moment,
            'fen': board.fen()
        })
        
        move_number += 1
    
    # Detect opening
    opening_info = detect_opening(move_list, board_positions)
    
    # Calculate ACPL (Average Centipawn Loss)
    white_acpl = sum([m['classification']['cp_loss'] for m in analysis if m['player'] == 'White' and m['classification']['cp_loss'] > 0]) / max(len([m for m in analysis if m['player'] == 'White']), 1)
    black_acpl = sum([m['classification']['cp_loss'] for m in analysis if m['player'] == 'Black' and m['classification']['cp_loss'] > 0]) / max(len([m for m in analysis if m['player'] == 'Black']), 1)
    
    acpl_data = {
        'white_acpl': white_acpl,
        'black_acpl': black_acpl
    }
    
    return analysis, opening_info, tactical_motifs, acpl_data

def generate_comprehensive_report(analysis, opening_info, tactical_motifs):
    """Generate detailed performance report"""
    if not analysis:
        return {}, [], [], [], []
    
    weaknesses = []
    strengths = []
    teaching_points = []
    tactical_lessons = []
    
    # Statistics
    total_moves = len(analysis)
    white_moves = [m for m in analysis if m['player'] == 'White']
    black_moves = [m for m in analysis if m['player'] == 'Black']
    
    move_stats = {
        'brilliant': len([m for m in analysis if m['classification']['type'] == 'brilliant']),
        'best': len([m for m in analysis if m['classification']['type'] == 'best']),
        'good': len([m for m in analysis if m['classification']['type'] == 'good']),
        'inaccuracy': len([m for m in analysis if m['classification']['type'] == 'inaccuracy']),
        'mistake': len([m for m in analysis if m['classification']['type'] == 'mistake']),
        'blunder': len([m for m in analysis if m['classification']['type'] == 'blunder'])
    }
    
    accuracy = ((move_stats['brilliant'] + move_stats['best'] + move_stats['good']) / total_moves * 100) if total_moves > 0 else 0
    
    # Game phases
    opening_moves = [m for m in analysis if m['move_number'] <= 10]
    middlegame_moves = [m for m in analysis if 10 < m['move_number'] <= 30]
    endgame_moves = [m for m in analysis if m['move_number'] > 30]
    
    opening_errors = [m for m in opening_moves if m['classification']['type'] in ['mistake', 'blunder']]
    
    # Opening analysis
    if len(opening_errors) >= 2:
        weaknesses.append({
            'area': '📚 Opening Knowledge',
            'severity': 'High',
            'description': f"Made {len(opening_errors)} errors in the opening ({opening_info['name']}).",
            'details': f"Study the key ideas: {', '.join(opening_info.get('key_ideas', ['Control center', 'Develop pieces'])[:2])}"
        })
    elif len(opening_errors) == 0 and len(opening_moves) >= 8:
        strengths.append({
            'area': '📚 Opening Mastery',
            'description': f"Excellent opening play! Flawless execution of {opening_info['name']}.",
            'details': 'You followed opening principles perfectly.'
        })
    
    # Tactical awareness
    if move_stats['blunder'] >= 2:
        weaknesses.append({
            'area': '⚔️ Tactical Awareness',
            'severity': 'Critical',
            'description': f"{move_stats['blunder']} blunders - tactical vision needs work.",
            'details': 'Practice 20-30 tactical puzzles daily. Focus on calculation depth.'
        })
        teaching_points.append({
            'phase': 'Tactics',
            'title': 'Improve Tactical Vision',
            'lesson': 'Before EVERY move, check: 1) Checks 2) Captures 3) Attacks',
            'warning': 'Use "Blunder Check" method - verify opponent has no immediate threats'
        })
    
    if len(tactical_motifs) >= 5:
        strengths.append({
            'area': '⚔️ Tactical Execution',
            'description': f"Found {len(tactical_motifs)} tactical opportunities!",
            'details': 'Excellent tactical awareness throughout the game.'
        })
    
    # Endgame
    if endgame_moves:
        endgame_accuracy = len([m for m in endgame_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / len(endgame_moves) * 100
        
        if endgame_accuracy < 70:
            weaknesses.append({
                'area': '♔ Endgame Technique',
                'severity': 'Medium',
                'description': f"Endgame accuracy: {endgame_accuracy:.1f}%",
                'details': 'Study fundamental endgames: K+P, K+R, opposition, triangulation'
            })
        elif endgame_accuracy >= 85:
            strengths.append({
                'area': '♔ Endgame Excellence',
                'description': f"Outstanding endgame play ({endgame_accuracy:.1f}% accuracy)!",
                'details': 'Strong technique in converting advantages.'
            })
    
    # Tactical patterns analysis
    all_motifs = [motif for move in analysis for motif in move['motifs']]
    motif_counts = {}
    for motif in all_motifs:
        motif_counts[motif] = motif_counts.get(motif, 0) + 1
    
    for motif, count in motif_counts.items():
        if motif in TACTICAL_PATTERNS and count >= 2:
            pattern = TACTICAL_PATTERNS[motif]
            tactical_lessons.append({
                'pattern': motif,
                'title': f"{pattern['name']} ({count}×)",
                'description': pattern['description'],
                'recognition': pattern['recognition'],
                'defense': pattern['defense'],
                'exercise': pattern['exercise'],
                'frequency': pattern.get('frequency', 'Common'),
                'difficulty': pattern.get('difficulty', 'Intermediate')
            })
    
    # Brilliant moves
    brilliant_moves = [m for m in analysis if m['classification']['type'] == 'brilliant']
    for bm in brilliant_moves[:3]:
        strengths.append({
            'area': '✨ Brilliant Play',
            'description': f"Move {bm['move_number']}: {bm['san']} - Brilliant!",
            'details': bm['teaching_moment'] or 'Outstanding move!'
        })
    
    # Performance metrics
    performance_metrics = {
        'accuracy': accuracy,
        'white_accuracy': len([m for m in white_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(white_moves), 1) * 100,
        'black_accuracy': len([m for m in black_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(black_moves), 1) * 100,
        'tactical_sharpness': (move_stats['brilliant'] + len(tactical_motifs)) / total_moves * 100,
        'consistency': (1 - move_stats['blunder'] / max(total_moves, 1)) * 100,
        'opening_score': len([m for m in opening_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(opening_moves), 1) * 100 if opening_moves else 0,
        'middlegame_score': len([m for m in middlegame_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(middlegame_moves), 1) * 100 if middlegame_moves else 0,
        'endgame_score': len([m for m in endgame_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(endgame_moves), 1) * 100 if endgame_moves else 0,
        'move_stats': move_stats
    }
    
    return performance_metrics, weaknesses, strengths, teaching_points, tactical_lessons

def generate_study_plan(weaknesses, tactical_lessons, performance_metrics):
    """Generate personalized study plan"""
    study_plan = []
    
    priority_map = {
        '⚔️ Tactical Awareness': 1,
        '📚 Opening Knowledge': 2,
        '♔ Endgame Technique': 3,
        '🎯 Positional Understanding': 4
    }
    
    sorted_weaknesses = sorted(weaknesses, key=lambda x: priority_map.get(x['area'], 5))
    
    for idx, weakness in enumerate(sorted_weaknesses[:3], 1):
        area = weakness['area']
        
        if 'Tactical' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Tactical Training',
                'icon': '⚔️',
                'daily_time': '25-30 minutes',
                'exercises': [
                    'Solve 25-30 tactical puzzles (Chess.com/Lichess)',
                    'Focus on: Forks, pins, discovered attacks',
                    'Review missed puzzles - understand WHY',
                    'Practice visualization: Calculate 3 moves deep'
                ],
                'weekly_goal': 'Solve 150+ puzzles with 80%+ accuracy',
                'resources': [
                    'Chess.com Puzzle Rush',
                    'Lichess Puzzle Storm',
                    'CT-ART Tactical Training',
                    'Chesstempo.com'
                ],
                'tracking': 'Track puzzle rating improvement weekly'
            })
        
        elif 'Opening' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Opening Repertoire',
                'icon': '📚',
                'daily_time': '20 minutes',
                'exercises': [
                    f"Deep dive: {area.split('(')[1].split(')')[0] if '(' in area else 'chosen opening'}",
                    'Learn the IDEAS, not just moves',
                    'Study 2-3 model games',
                    'Practice against computer'
                ],
                'weekly_goal': 'Master first 12 moves of 2 openings',
                'resources': [
                    'Lichess Opening Explorer',
                    'Chessable video courses',
                    'ChessBase Opening Videos',
                    'YouTube: Hanging Pawns, GothamChess'
                ],
                'tracking': 'Play 5 games with your opening this week'
            })
        
        elif 'Endgame' in area:
            study_plan.append({
                'priority': idx,
                'area': 'Endgame Mastery',
                'icon': '♔',
                'daily_time': '15-20 minutes',
                'exercises': [
                    'Master basic checkmates (Q+K, R+K vs K)',
                    'King and Pawn endings',
                    'Learn opposition and triangulation',
                    'Practice theoretical positions'
                ],
                'weekly_goal': 'Master 7 essential endgame positions',
                'resources': [
                    'Lichess Practice - Endgames',
                    '100 Endgames You Must Know (book)',
                    'Silman Endgame Course',
                    'ChessKid Endgame Practice'
                ],
                'tracking': 'Test yourself on 10 endgame positions'
            })
    
    # Add pattern-specific training
    if tactical_lessons:
        for lesson in tactical_lessons[:2]:
            study_plan.append({
                'priority': len(study_plan) + 1,
                'area': f"{lesson['title']} Focus",
                'icon': '🎯',
                'daily_time': '10-15 minutes',
                'exercises': [
                    f"Filter puzzles for {lesson['pattern']} patterns",
                    f"Recognition drill: {lesson['recognition']}",
                    lesson['exercise'],
                    'Review master games with this pattern'
                ],
                'weekly_goal': f"Recognize {lesson['pattern']} instantly",
                'resources': [
                    'Pattern-filtered puzzle sets',
                    'Tactical motif trainers',
                    'Master game databases'
                ],
                'tracking': f"Find 10 {lesson['pattern']} examples this week"
            })
    
    # Add analysis recommendation
    study_plan.append({
        'priority': len(study_plan) + 1,
        'area': 'Game Analysis',
        'icon': '📊',
        'daily_time': '15 minutes',
        'exercises': [
            'Analyze 1 of your games daily',
            'Compare your moves with engine suggestions',
            'Identify recurring mistakes',
            'Study similar positions from master games'
        ],
        'weekly_goal': 'Analyze 7 games, identify 3 improvement areas',
        'resources': [
            'This Chess Coach Pro app',
            'Lichess Analysis Board',
            'Chess.com Game Review',
            'ChessBase Analysis'
        ],
        'tracking': 'Keep a training journal of insights'
    })
    
    return study_plan

def create_evaluation_chart(analysis):
    """Create evaluation chart over time"""
    move_numbers = [m['move_number'] for m in analysis]
    evaluations = [m['eval_after'] for m in analysis]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=move_numbers,
        y=evaluations,
        mode='lines+markers',
        name='Position Evaluation',
        line=dict(color='#667eea', width=3),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title='Game Evaluation Over Time',
        xaxis_title='Move Number',
        yaxis_title='Evaluation (pawns)',
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    return fig

def create_accuracy_comparison(analysis):
    """Create accuracy comparison chart"""
    white_moves = [m for m in analysis if m['player'] == 'White']
    black_moves = [m for m in analysis if m['player'] == 'Black']
    
    white_accuracy = len([m for m in white_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(white_moves), 1) * 100
    black_accuracy = len([m for m in black_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(black_moves), 1) * 100
    
    fig = go.Figure(data=[
        go.Bar(name='White', x=['Accuracy'], y=[white_accuracy], marker_color='#f0f0f0'),
        go.Bar(name='Black', x=['Accuracy'], y=[black_accuracy], marker_color='#2d2d44')
    ])
    
    fig.update_layout(
        title='Player Accuracy Comparison',
        yaxis_title='Accuracy %',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300,
        showlegend=True
    )
    
    return fig

# Main App
st.markdown('<div class="main-header">♟️ Chess Learning Coach Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">🎯 Professional Analysis | 📚 Opening Theory | ⚔️ Tactical Training | 🧠 AI-Powered Coaching</div>', unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🎯 Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Dashboard", "📊 Analyze Game", "📚 Opening Explorer", "⚔️ Tactical Patterns", "👤 Profile & Stats"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # User Profile
    st.markdown("### 👤 Your Profile")
    username = st.text_input("Username", st.session_state.user_profile['username'], key='username_input')
    st.session_state.user_profile['username'] = username
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rating", st.session_state.user_profile['rating'], delta=None)
    with col2:
        st.metric("Games", st.session_state.user_profile['games_analyzed'])
    
    st.metric("Tactics Found", st.session_state.user_profile['total_tactics_found'])
    
    st.markdown("---")
    
    # Engine Status
    st.markdown("### ⚙️ Engine Status")
    if st.session_state.engine:
        st.success("✅ Stockfish Active")
        st.caption("Depth: 15-18 ply")
    else:
        st.warning("⚠️ Limited Mode")
        st.caption("Install Stockfish for full analysis")

# Page Content
if page == "🏠 Dashboard":
    st.markdown("## Welcome to Your Chess Command Center")
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem;">📊</div>
            <div class="metric-label">Deep Analysis</div>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                Stockfish-powered analysis with evaluation graphs, 
                move-by-move breakdown, and alternative variations
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem;">🎓</div>
            <div class="metric-label">Smart Coaching</div>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                Personalized feedback on every move with 
                teaching moments and improvement suggestions
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem;">📈</div>
            <div class="metric-label">Track Progress</div>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                Monitor your tactical awareness, opening knowledge,
                and overall improvement over time
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Start Guide
    st.markdown("## 🚀 Quick Start Guide")
    
    tab1, tab2, tab3 = st.tabs(["📊 Analyze Games", "📚 Study Openings", "⚔️ Train Tactics"])
    
    with tab1:
        st.markdown("""
        ### How to Analyze Your Games
        
        1. **Get Your PGN**: Export your game from Chess.com, Lichess, or any chess platform
        2. **Paste & Analyze**: Go to 'Analyze Game' page and paste your PGN
        3. **Review Results**: Get detailed analysis with:
           - Move-by-move evaluation
           - Tactical pattern detection
           - Opening classification
           - Strengths & weaknesses report
           - Personalized study plan
        
        **Pro Tips:**
        - Analyze both wins and losses
        - Focus on recurring mistakes
        - Study the suggested alternatives
        - Use the interactive board to replay positions
        """)
    
    with tab2:
        st.markdown("""
        ### Master Your Opening Repertoire
        
        **Available Openings:**
        - Ruy Lopez / Spanish Opening
        - Sicilian Defense (all variations)
        - Italian Game
        - French Defense
        - Caro-Kann Defense
        - Queen's Gambit
        - Nimzo-Indian Defense
        - English Opening
        - Reti Opening
        
        **Learn:**
        - Key strategic ideas
        - Typical plans for both sides
        - Common mistakes to avoid
        - ECO codes and variations
        """)
    
    with tab3:
        st.markdown("""
        ### Tactical Pattern Recognition
        
        **Master These Patterns:**
        - ⚔️ Forks & Royal Forks
        - 📌 Pins (Absolute & Relative)
        - 🔪 Skewers
        - 💥 Discovered Attacks & Checks
        - 🎯 Double Attacks
        - 🛡️ Removing the Defender
        - 👑 Back Rank Mates
        - 🔄 Deflection & Interference
        - ⚡ Zwischenzug (In-Between Moves)
        
        **Each pattern includes:**
        - Clear description
        - Recognition tips
        - Defense strategies
        - Practice exercises
        """)
    
    st.markdown("---")
    
    # Recent Activity
    if st.session_state.user_profile['games_analyzed'] > 0:
        st.markdown("## 📈 Your Recent Activity")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Games", st.session_state.user_profile['games_analyzed'])
        col2.metric("Tactics Found", st.session_state.user_profile['total_tactics_found'])
        col3.metric("Avg. Accuracy", "87.3%")  # Placeholder
        col4.metric("Study Streak", "3 days")  # Placeholder

elif page == "📊 Analyze Game":
    st.markdown("## 📊 Comprehensive Game Analysis")
    
    st.markdown("""
    <div class="analysis-card">
        <h3>🎯 Professional Chess Analysis</h3>
        <p>Paste your PGN below for world-class analysis featuring:</p>
        <ul>
            <li>🤖 <strong>Stockfish Engine Analysis</strong> - Deep position evaluation</li>
            <li>📊 <strong>Evaluation Graphs</strong> - Visualize game momentum</li>
            <li>⚔️ <strong>Tactical Detection</strong> - Automatic pattern recognition</li>
            <li>📚 <strong>Opening Classification</strong> - ECO codes and theory</li>
            <li>🎓 <strong>Teaching Moments</strong> - Learn from every mistake</li>
            <li>📋 <strong>Study Plan</strong> - Personalized improvement roadmap</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    pgn_input = st.text_area(
        "Paste your PGN here",
        height=200,
        placeholder="""[Event "Rated Blitz Game"]
[Site "Chess.com"]
[Date "2025.01.20"]
[White "YourUsername"]
[Black "Opponent"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O..."""
    )
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        analysis_depth = st.slider("Analysis Depth", 10, 20, 15, help="Higher = More accurate but slower")
    
    with col2:
        show_variations = st.checkbox("Show Alternative Lines", value=True)
    
    with col3:
        show_teaching = st.checkbox("Teaching Mode", value=True)
    
    with col4:
        analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if analyze_btn and pgn_input:
        st.markdown("---")
        
        with st.spinner("🧠 Analyzing your game with Stockfish..."):
            progress_bar = st.progress(0)
            
            def update_progress(progress):
                progress_bar.progress(progress)
            
            analysis, opening_info, tactical_motifs, acpl_data = analyze_game_with_teaching(
                pgn_input, 
                progress_callback=update_progress
            )
            
            if analysis:
                st.session_state.game_analysis = analysis
                st.session_state.opening_analysis = opening_info
                st.session_state.tactical_motifs = tactical_motifs
                st.session_state.acpl_data = acpl_data
                st.session_state.game_pgn = pgn_input
                st.session_state.user_profile['games_analyzed'] += 1
                st.session_state.user_profile['total_tactics_found'] += len(tactical_motifs)
                
                progress_bar.empty()
                st.success("✅ Analysis Complete!")
                
                # Generate report
                performance, weaknesses, strengths, teaching_points, tactical_lessons = generate_comprehensive_report(
                    analysis, opening_info, tactical_motifs
                )
                
                st.session_state.performance_metrics = performance
                st.session_state.weaknesses = weaknesses
                st.session_state.strengths = strengths
                st.session_state.teaching_points = teaching_points
                st.session_state.tactical_lessons = tactical_lessons
                
                # Generate study plan
                study_plan = generate_study_plan(weaknesses, tactical_lessons, performance)
                st.session_state.study_plan = study_plan
            else:
                st.error("❌ Invalid PGN format. Please check your input.")
    
    # Display Analysis Results
    if st.session_state.game_analysis:
        analysis = st.session_state.game_analysis
        opening_info = st.session_state.opening_analysis
        
        st.markdown("---")
        
        # Performance Overview
        st.markdown("## 🏆 Performance Overview")
        
        if 'performance_metrics' in st.session_state:
            metrics = st.session_state.performance_metrics
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['accuracy']:.1f}%</div>
                    <div class="metric-label">Overall Accuracy</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['move_stats']['brilliant']}</div>
                    <div class="metric-label">Brilliant Moves</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['move_stats']['best']}</div>
                    <div class="metric-label">Best Moves</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['move_stats']['mistake']}</div>
                    <div class="metric-label">Mistakes</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['move_stats']['blunder']}</div>
                    <div class="metric-label">Blunders</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Charts
            col1, col2 = st.columns([2, 1])
            
            with col1:
                eval_chart = create_evaluation_chart(analysis)
                st.plotly_chart(eval_chart, use_container_width=True)
            
            with col2:
                accuracy_chart = create_accuracy_comparison(analysis)
                st.plotly_chart(accuracy_chart, use_container_width=True)
        
        st.markdown("---")
        
        # Opening Analysis
        st.markdown("## 📚 Opening Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="opening-card">
                <h2>{opening_info.get('name', 'Unknown Opening')}</h2>
                <p style="font-size: 1.1rem;"><strong>ECO:</strong> {opening_info.get('eco', 'N/A')}</p>
                <p style="margin-top: 1rem;"><strong>📖 Key Ideas:</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            if opening_info.get('key_ideas'):
                for idx, idea in enumerate(opening_info['key_ideas'], 1):
                    st.markdown(f"**{idx}.** {idea}")
            
            st.markdown("---")
            
            if opening_info.get('typical_plans'):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**⚪ White's Plan:**")
                    st.info(opening_info['typical_plans'].get('white', 'Standard development'))
                with col_b:
                    st.markdown("**⚫ Black's Plan:**")
                    st.info(opening_info['typical_plans'].get('black', 'Counter in center'))
        
        with col2:
            opening_moves = [m for m in analysis if m['move_number'] <= 10]
            opening_quality = len([m for m in opening_moves if m['classification']['type'] in ['best', 'good', 'brilliant']]) / max(len(opening_moves), 1) * 100
            
            st.metric("Opening Quality", f"{opening_quality:.1f}%", 
                     delta=f"{opening_quality - 75:.1f}%" if opening_quality > 75 else None)
            
            if opening_quality >= 85:
                st.success("🌟 Excellent opening preparation!")
            elif opening_quality >= 70:
                st.info("✓ Good opening play")
            else:
                st.warning("⚠️ Opening needs work")
            
            st.markdown("**⚠️ Common Mistakes:**")
            if opening_info.get('common_mistakes'):
                for mistake in opening_info['common_mistakes'][:3]:
                    st.caption(f"• {mistake}")
        
        st.markdown("---")
        
        # Tactical Patterns
        if st.session_state.tactical_motifs:
            st.markdown("## ⚔️ Tactical Patterns Detected")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                for motif_data in st.session_state.tactical_motifs[:8]:
                    motifs_str = ', '.join([
                        f'<span class="tactic-tag">{m.replace("_", " ").title()}</span>' 
                        for m in motif_data['motifs']
                    ])
                    
                    st.markdown(f"""
                    <div class="move-row">
                        <strong>Move {motif_data['move_number']}</strong>: 
                        <strong style="color: #667eea;">{motif_data['move']}</strong> 
                        ({motif_data['player']})<br>
                        {motifs_str}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Total Tactics", len(st.session_state.tactical_motifs))
                unique_patterns = len(set([m for data in st.session_state.tactical_motifs for m in data['motifs']]))
                st.metric("Pattern Types", unique_patterns)
        
        st.markdown("---")
        
        # Strengths & Weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("## 💪 Your Strengths")
            if 'strengths' in st.session_state and st.session_state.strengths:
                for strength in st.session_state.strengths:
                    st.markdown(f"""
                    <div class="strength-item">
                        <h4>{strength['area']}</h4>
                        <p>{strength['description']}</p>
                        <small><em>{strength.get('details', '')}</em></small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Keep playing to identify your strengths!")
        
        with col2:
            st.markdown("## 📈 Areas to Improve")
            if 'weaknesses' in st.session_state and st.session_state.weaknesses:
                for weakness in st.session_state.weaknesses:
                    severity_emoji = {
                        'Critical': '🔴',
                        'High': '🟠',
                        'Medium': '🟡',
                        'Low': '🟢'
                    }
                    st.markdown(f"""
                    <div class="weakness-item">
                        <h4>{weakness['area']} {severity_emoji.get(weakness.get('severity', 'Medium'), '🔵')}</h4>
                        <p>{weakness['description']}</p>
                        <small><em>{weakness.get('details', '')}</em></small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("🎉 No major weaknesses detected!")
        
        st.markdown("---")
        
        # Study Plan
        if 'study_plan' in st.session_state and st.session_state.study_plan:
            st.markdown("## 📋 Your Personalized Study Plan")
            
            for plan in st.session_state.study_plan:
                with st.expander(
                    f"{plan['icon']} Priority {plan['priority']}: {plan['area']}", 
                    expanded=(plan['priority'] == 1)
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**⏱ Daily Time:** {plan['daily_time']}")
                        st.markdown(f"**🎯 Weekly Goal:** {plan['weekly_goal']}")
                        
                        st.markdown("**📝 Daily Exercises:**")
                        for exercise in plan['exercises']:
                            st.markdown(f"- {exercise}")
                    
                    with col2:
                        st.markdown("**📚 Resources:**")
                        for resource in plan['resources']:
                            st.markdown(f"• {resource}")
                        
                        if 'tracking' in plan:
                            st.info(f"📊 {plan['tracking']}")
        
        st.markdown("---")
        
        # Move-by-Move Analysis
        st.markdown("## 📝 Move-by-Move Analysis")
        
        filter_option = st.selectbox(
            "Filter moves:",
            ["All Moves", "Critical Moves Only", "Mistakes & Blunders", "Best & Brilliant"]
        )
        
        if filter_option == "Critical Moves Only":
            display_moves = [m for m in analysis if m['classification']['type'] in ['brilliant', 'best', 'mistake', 'blunder']]
        elif filter_option == "Mistakes & Blunders":
            display_moves = [m for m in analysis if m['classification']['type'] in ['mistake', 'blunder']]
        elif filter_option == "Best & Brilliant":
            display_moves = [m for m in analysis if m['classification']['type'] in ['best', 'brilliant']]
        else:
            display_moves = analysis
        
        for idx, move_data in enumerate(display_moves[:30]):
            class_type = move_data['classification']['type']
            
            # Determine game phase
            if move_data['move_number'] <= 10:
                phase = '<span class="phase-badge phase-opening">Opening</span>'
            elif move_data['move_number'] <= 30:
                phase = '<span class="phase-badge phase-middlegame">Middlegame</span>'
            else:
                phase = '<span class="phase-badge phase-endgame">Endgame</span>'
            
            move_class = f"move-{class_type}"
            
            with st.expander(
                f"Move {move_data['move_number']}: {move_data['san']} ({move_data['player']}) - {class_type.title()} {move_data['classification']['symbol']}",
                expanded=False
            ):
                st.markdown(phase, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"**Evaluation:** {move_data['eval_after']:+.2f}")
                    st.markdown(f"**CP Loss:** {abs(move_data['classification']['cp_loss'])}")
                    
                    st.markdown(f"<p style='color: {move_data['classification'].get('color', 'white')};'>**{move_data['classification']['feedback']}**</p>", unsafe_allow_html=True)
                    
                    if move_data.get('teaching_moment') and show_teaching:
                        st.info(f"🎓 **Teaching:** {move_data['teaching_moment']}")
                    
                    if move_data['motifs']:
                        motif_tags = ' '.join([
                            f'<span class="tactic-tag">{m.replace("_", " ").title()}</span>'
                            for m in move_data['motifs']
                        ])
                        st.markdown(f"**⚔️ Tactics:** {motif_tags}", unsafe_allow_html=True)
                    
                    if move_data['best_move'] and move_data['best_move'] != move_data['move']:
                        st.warning(f"**Better move:** {move_data['best_move']}")
                
                with col2:
                    # Render position
                    try:
                        board_for_display = chess.Board(move_data['fen'])
                        board_svg = render_board_svg(board_for_display, size=300)
                        st.markdown(board_svg, unsafe_allow_html=True)
                    except:
                        st.caption("Board display unavailable")

elif page == "📚 Opening Explorer":
    st.markdown("## 📚 Opening Theory Database")
    
    st.markdown("""
    <div class="analysis-card">
        <p>Master chess openings by understanding their strategic ideas, not just memorizing moves. 
        Study the plans, typical positions, and common mistakes for each opening.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Opening filter
    all_openings = list(set([info['name'] for info in OPENING_DATABASE.values()]))
    all_openings.sort()
    
    selected_opening = st.selectbox(
        "🔍 Select an opening to study:",
        ["📖 All Openings"] + all_openings
    )
    
    st.markdown("---")
    
    if selected_opening == "📖 All Openings":
        for moves, info in OPENING_DATABASE.items():
            with st.expander(f"{info['name']} ({info['eco']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Starting moves:** `{moves}`")
                    st.markdown(f"**ECO Code:** {info['eco']}")
                    
                    if info.get('key_ideas'):
                        st.markdown("**🎯 Key Strategic Ideas:**")
                        for idx, idea in enumerate(info['key_ideas'], 1):
                            st.markdown(f"{idx}. {idea}")
                
                with col2:
                    if info.get('common_mistakes'):
                        st.markdown("**⚠️ Common Mistakes:**")
                        for mistake in info['common_mistakes']:
                            st.caption(f"• {mistake}")
    else:
        for moves, info in OPENING_DATABASE.items():
            if info['name'] == selected_opening:
                st.markdown(f"# {info['name']}")
                st.markdown(f"**ECO Code:** {info['eco']}")
                st.markdown(f"**Move Sequence:** `{moves}`")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🎯 Key Strategic Ideas")
                    if info.get('key_ideas'):
                        for idx, idea in enumerate(info['key_ideas'], 1):
                            st.markdown(f"""
                            <div class="report-section">
                                <strong>{idx}.</strong> {idea}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if info.get('typical_plans'):
                        st.markdown("### 📋 Typical Plans")
                        st.info(f"**⚪ White:** {info['typical_plans'].get('white', 'N/A')}")
                        st.info(f"**⚫ Black:** {info['typical_plans'].get('black', 'N/A')}")
                
                with col2:
                    st.markdown("### ⚠️ Common Mistakes")
                    if info.get('common_mistakes'):
                        for idx, mistake in enumerate(info['common_mistakes'], 1):
                            st.markdown(f"""
                            <div class="weakness-item">
                                <strong>{idx}.</strong> {mistake}
                            </div>
                            """, unsafe_allow_html=True)

elif page == "⚔️ Tactical Patterns":
    st.markdown("## ⚔️ Master Tactical Patterns")
    
    st.markdown("""
    <div class="analysis-card">
        <p>Tactics win games! Learn to recognize these patterns instantly to dramatically improve your chess.</p>
        <p><strong>Study Method:</strong> Understand the pattern → Learn recognition → Practice puzzles → Apply in games</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Pattern categories
    pattern_categories = {
        'Beginner': ['fork', 'pin', 'skewer', 'back_rank', 'double_attack'],
        'Intermediate': ['discovered_attack', 'removing_defender', 'deflection'],
        'Advanced': ['interference', 'zwischenzug']
    }
    
    selected_level = st.selectbox(
        "📊 Select Difficulty Level:",
        ["🌟 All Patterns", "🟢 Beginner", "🟡 Intermediate", "🔴 Advanced"]
    )
    
    st.markdown("---")
    
    if selected_level == "🌟 All Patterns":
        display_patterns = TACTICAL_PATTERNS
    else:
        level_name = selected_level.split()[1]
        display_patterns = {k: v for k, v in TACTICAL_PATTERNS.items() if k in pattern_categories.get(level_name, [])}
    
    for pattern_key, pattern_info in display_patterns.items():
        difficulty_color = {
            'Beginner': '#10b981',
            'Intermediate': '#f59e0b',
            'Advanced': '#ef4444'
        }
        
        color = difficulty_color.get(pattern_info.get('difficulty', 'Intermediate'), '#3b82f6')
        
        with st.expander(f"⚔️ {pattern_info['name']} - {pattern_info.get('difficulty', 'Intermediate')}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {pattern_info['description']}")
                st.markdown("---")
                st.markdown(f"**🔍 How to Recognize:** {pattern_info['recognition']}")
                st.markdown(f"**🛡️ How to Defend:** {pattern_info['defense']}")
                st.markdown(f"**📝 Practice Exercise:** {pattern_info['exercise']}")
                
                if 'examples' in pattern_info:
                    st.info(f"💡 **Examples:** {pattern_info['examples']}")
            
            with col2:
                freq_color = {
                    'Very Common': '#10b981',
                    'Common': '#3b82f6',
                    'Uncommon': '#f59e0b'
                }
                freq = pattern_info.get('frequency', 'Common')
                st.markdown(f"""
                <div class="metric-card" style="background: {freq_color.get(freq, '#3b82f6')};">
                    <div class="metric-label">Frequency</div>
                    <div class="metric-value" style="font-size: 1.2rem;">{freq}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-card" style="background: {color}; margin-top: 1rem;">
                    <div class="metric-label">Difficulty</div>
                    <div class="metric-value" style="font-size: 1.2rem;">{pattern_info.get('difficulty', 'Intermediate')}</div>
                </div>
                """, unsafe_allow_html=True)

elif page == "👤 Profile & Stats":
    st.markdown("## 👤 Your Chess Profile")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.user_profile['rating']}</div>
            <div class="metric-label">Current Rating</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.user_profile['games_analyzed']}</div>
            <div class="metric-label">Games Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.user_profile['total_tactics_found']}</div>
            <div class="metric-label">Tactics Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{"🔥" if st.session_state.user_profile['games_analyzed'] > 0 else "💤"}</div>
            <div class="metric-label">Status</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if 'performance_metrics' in st.session_state:
        st.markdown("## 📊 Your Performance Analysis")
        
        metrics = st.session_state.performance_metrics
        
        # Performance Radar Chart
        fig = go.Figure()
        
        categories = ['Overall<br>Accuracy', 'Opening<br>Phase', 'Middlegame<br>Phase', 
                     'Endgame<br>Phase', 'Tactical<br>Sharpness', 'Consistency']
        values = [
            metrics['accuracy'],
            metrics['opening_score'],
            metrics['middlegame_score'],
            metrics['endgame_score'] if metrics['endgame_score'] > 0 else 50,
            metrics['tactical_sharpness'],
            metrics['consistency']
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Your Performance',
            line_color='#667eea',
            fillcolor='rgba(102, 126, 234, 0.3)',
            line_width=3
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10, color='white'),
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='white'),
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            height=500,
            title={
                'text': 'Performance Radar',
                'font': {'color': 'white', 'size': 20}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Game Phase Performance
        st.markdown("## 📈 Performance by Game Phase")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="analysis-card">
                <span class="phase-badge phase-opening">Opening</span>
                <h2 style="color: #667eea; margin-top: 1rem;">{metrics['opening_score']:.1f}%</h2>
                <p style="margin-top: 0.5rem;">
                    {"🌟 Excellent!" if metrics['opening_score'] >= 85 else 
                     "✓ Good" if metrics['opening_score'] >= 70 else 
                     "⚠️ Needs Work"}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="analysis-card">
                <span class="phase-badge phase-middlegame">Middlegame</span>
                <h2 style="color: #f093fb; margin-top: 1rem;">{metrics['middlegame_score']:.1f}%</h2>
                <p style="margin-top: 0.5rem;">
                    {"🌟 Excellent!" if metrics['middlegame_score'] >= 85 else 
                     "✓ Good" if metrics['middlegame_score'] >= 70 else 
                     "⚠️ Needs Work"}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if metrics['endgame_score'] > 0:
                st.markdown(f"""
                <div class="analysis-card">
                    <span class="phase-badge phase-endgame">Endgame</span>
                    <h2 style="color: #4facfe; margin-top: 1rem;">{metrics['endgame_score']:.1f}%</h2>
                    <p style="margin-top: 0.5rem;">
                        {"🌟 Excellent!" if metrics['endgame_score'] >= 85 else 
                         "✓ Good" if metrics['endgame_score'] >= 70 else 
                         "⚠️ Needs Work"}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="analysis-card">
                    <span class="phase-badge phase-endgame">Endgame</span>
                    <h2 style="color: #4facfe; margin-top: 1rem;">N/A</h2>
                    <p style="margin-top: 0.5rem;">No endgame data yet</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Move Quality Distribution
        st.markdown("## 📊 Move Quality Distribution")
        
        move_stats = metrics['move_stats']
        
        labels = ['Brilliant', 'Best', 'Good', 'Inaccuracy', 'Mistake', 'Blunder']
        values = [
            move_stats['brilliant'],
            move_stats['best'],
            move_stats['good'],
            move_stats['inaccuracy'],
            move_stats['mistake'],
            move_stats['blunder']
        ]
        colors = ['#9333ea', '#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker_colors=colors,
            textinfo='label+percent',
            textfont_size=12
        )])
        
        fig.update_layout(
            title={
                'text': 'Move Classification Breakdown',
                'font': {'color': 'white', 'size': 18}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📊 Analyze a game to see your detailed statistics and performance metrics!")
    
    st.markdown("---")
    
    # Improvement Tips
    st.markdown("## 💡 Personalized Improvement Tips")
    
    if 'study_plan' in st.session_state and st.session_state.study_plan:
        st.markdown("**Your Active Study Plan:**")
        for plan in st.session_state.study_plan[:3]:
            st.markdown(f"""
            <div class="study-plan-card">
                <h3>{plan['icon']} {plan['area']}</h3>
                <p><strong>⏱ Daily:</strong> {plan['daily_time']}</p>
                <p><strong>🎯 This Week:</strong> {plan['weekly_goal']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="analysis-card">
            <h3>🎯 General Improvement Guidelines</h3>
            <ol>
                <li><strong>Tactics Training:</strong> 20-30 minutes daily (Chess.com/Lichess puzzles)</li>
                <li><strong>Opening Study:</strong> 15 minutes daily (Learn ideas, not just moves)</li>
                <li><strong>Game Analysis:</strong> Analyze 1 game daily using this tool</li>
                <li><strong>Endgame Practice:</strong> 10 minutes daily (Basic checkmates & K+P endings)</li>
                <li><strong>Play Practice Games:</strong> 2-3 longer time control games per week</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0c0; padding: 30px;">
    <h3 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               -webkit-background-clip: text;
               -webkit-text-fill-color: transparent;">
        Chess Learning Coach Pro
    </h3>
    <p style="margin-top: 1rem;">
        <strong>🤖 Powered by Stockfish Engine</strong><br>
        🧠 Advanced AI Analysis | 📚 Comprehensive Opening Theory | ⚔️ Tactical Pattern Recognition<br>
        🎓 Personalized Teaching | 📊 Performance Tracking | 📈 Smart Study Plans
    </p>
    <p style="margin-top: 1.5rem; font-size: 0.9rem;">
        Built with ❤️ using Streamlit & Python-Chess<br>
        Inspired by Chess.com, Lichess & ChessBase<br>
        © 2025 - Elevate Your Chess Game
    </p>
</div>
""", unsafe_allow_html=True)
