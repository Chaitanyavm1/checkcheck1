"""
Chess Learning Coach - Streamlit Application
A web-based chess analysis and coaching platform using Streamlit

Requirements:
pip install streamlit chess python-chess stockfish plotly pandas
"""

import streamlit as st
import chess
import chess.engine
import chess.pgn
import chess.svg
from io import StringIO
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import base64
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Chess Learning Coach Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #9333ea;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .weakness-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .strength-box {
        background-color: #d1e7dd;
        border-left: 4px solid #198754;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .recommendation-box {
        background-color: #cfe2ff;
        border-left: 4px solid #0d6efd;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .move-brilliant { color: #9333ea; font-weight: bold; }
    .move-best { color: #10b981; font-weight: bold; }
    .move-good { color: #3b82f6; }
    .move-inaccuracy { color: #f59e0b; }
    .move-mistake { color: #f97316; font-weight: bold; }
    .move-blunder { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'moves' not in st.session_state:
    st.session_state.moves = []
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'game_analysis' not in st.session_state:
    st.session_state.game_analysis = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        'username': 'Player',
        'rating': 1200,
        'games_played': 0
    }

# Stockfish Engine Setup
@st.cache_resource
def initialize_engine():
    """Initialize Stockfish engine"""
    try:
        # Try common Stockfish paths
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

# Initialize engine
if st.session_state.engine is None:
    st.session_state.engine = initialize_engine()

def render_board_svg(board, size=400):
    """Render chess board as SVG"""
    svg = chess.svg.board(board, size=size)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    html = f'<img src="data:image/svg+xml;base64,{b64}"/>'
    return html

def analyze_position(board, depth=15):
    """Analyze current position using Stockfish"""
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
        pv = info.get('pv', [])[:5]  # Top 5 moves
        
        return {
            'evaluation': evaluation,
            'best_move': best_move.uci() if best_move else None,
            'mate_in': mate_in,
            'pv': [move.uci() for move in pv]
        }
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None,
            'pv': []
        }

def classify_move(eval_before, eval_after, is_best_move, player_color):
    """Classify move quality"""
    if player_color == chess.BLACK:
        eval_before = -eval_before
        eval_after = -eval_after
    
    centipawn_loss = (eval_before - eval_after) * 100
    
    if is_best_move:
        return 'best', '!', int(centipawn_loss)
    elif centipawn_loss < -50:
        return 'brilliant', '!!', int(centipawn_loss)
    elif centipawn_loss < 50:
        return 'good', '', int(centipawn_loss)
    elif centipawn_loss < 100:
        return 'inaccuracy', '?', int(centipawn_loss)
    elif centipawn_loss < 300:
        return 'mistake', '??', int(centipawn_loss)
    else:
        return 'blunder', '???', int(centipawn_loss)

def analyze_complete_game(pgn_string, progress_bar=None):
    """Analyze a complete game from PGN"""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    if not game:
        return None
    
    board = game.board()
    analysis = []
    move_number = 1
    total_moves = len(list(game.mainline_moves()))
    
    for idx, move in enumerate(game.mainline_moves()):
        if progress_bar:
            progress_bar.progress((idx + 1) / total_moves)
        
        # Analyze position before move
        eval_before = analyze_position(board, depth=12)
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        # Make move
        player_color = board.turn
        san_move = board.san(move)
        board.push(move)
        
        # Analyze position after move
        eval_after = analyze_position(board, depth=12)
        
        # Classify move
        classification, symbol, cp_loss = classify_move(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color
        )
        
        analysis.append({
            'move_number': move_number,
            'move': move.uci(),
            'san': san_move,
            'player': 'White' if player_color == chess.WHITE else 'Black',
            'eval_before': eval_before['evaluation'],
            'eval_after': eval_after['evaluation'],
            'best_move': best_move,
            'classification': classification,
            'symbol': symbol,
            'centipawn_loss': cp_loss
        })
        
        move_number += 1
    
    return analysis

def generate_weakness_report(analysis):
    """Generate personalized weakness report"""
    if not analysis:
        return [], [], []
    
    weaknesses = []
    strengths = []
    recommendations = []
    
    # Count move types
    blunders = len([m for m in analysis if m['classification'] == 'blunder'])
    mistakes = len([m for m in analysis if m['classification'] == 'mistake'])
    brilliant = len([m for m in analysis if m['classification'] == 'brilliant'])
    best = len([m for m in analysis if m['classification'] == 'best'])
    
    total_moves = len(analysis)
    accuracy = ((total_moves - blunders - mistakes) / total_moves * 100) if total_moves > 0 else 0
    
    # Analyze weaknesses
    if blunders > 2:
        weaknesses.append({
            'area': 'Tactical Awareness',
            'severity': 'High',
            'description': f'{blunders} blunders detected. Missing tactical opportunities.'
        })
        recommendations.append({
            'title': 'Tactical Training',
            'priority': 'High',
            'description': 'Practice 20-30 tactical puzzles daily focusing on forks, pins, and skewers.'
        })
    
    # Opening phase analysis
    opening_moves = [m for m in analysis if m['move_number'] <= 10]
    opening_mistakes = len([m for m in opening_moves if m['classification'] in ['mistake', 'blunder']])
    
    if opening_mistakes > 3:
        weaknesses.append({
            'area': 'Opening Knowledge',
            'severity': 'Medium',
            'description': 'Frequent mistakes in opening phase.'
        })
        recommendations.append({
            'title': 'Study Opening Principles',
            'priority': 'Medium',
            'description': 'Focus on the 3 key principles: Control center, develop pieces, castle early.'
        })
    
    # Analyze strengths
    if brilliant > 1:
        strengths.append({
            'area': 'Strategic Vision',
            'description': f'{brilliant} brilliant moves showing excellent position understanding.'
        })
    
    if accuracy > 85:
        strengths.append({
            'area': 'Consistency',
            'description': f'High accuracy ({accuracy:.1f}%) throughout the game.'
        })
    
    if (best + brilliant) / total_moves > 0.5:
        strengths.append({
            'area': 'Move Selection',
            'description': 'Frequently finding the best moves in critical positions.'
        })
    
    return weaknesses, strengths, recommendations

def plot_evaluation_chart(analysis):
    """Create evaluation chart over time"""
    if not analysis:
        return None
    
    moves = [m['move_number'] for m in analysis]
    evals = [m['eval_after'] for m in analysis]
    
    # Cap evaluations for better visualization
    evals = [max(-10, min(10, e)) for e in evals]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=moves,
        y=evals,
        mode='lines',
        name='Evaluation',
        line=dict(color='rgb(147, 51, 234)', width=3),
        fill='tozeroy',
        fillcolor='rgba(147, 51, 234, 0.2)'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Equal")
    
    fig.update_layout(
        title="Game Evaluation Over Time",
        xaxis_title="Move Number",
        yaxis_title="Evaluation (pawns)",
        template="plotly_dark",
        height=400,
        hovermode='x unified'
    )
    
    return fig

# Main App UI
st.markdown('<div class="main-header">♟️ Chess Learning Coach Pro</div>', unsafe_allow_html=True)
st.markdown("**Powered by Stockfish Analysis Engine** | AI-Driven Chess Improvement Platform")

# Sidebar
with st.sidebar:
    st.header("🎯 Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Home", "📊 Analyze Game", "👤 Profile", "📚 Resources"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # User Profile
    st.subheader("👤 Player Profile")
    username = st.text_input("Username", st.session_state.user_profile['username'])
    st.session_state.user_profile['username'] = username
    
    st.metric("Current Rating", st.session_state.user_profile['rating'])
    st.metric("Games Analyzed", st.session_state.user_profile['games_played'])
    
    st.markdown("---")
    
    # Engine Status
    st.subheader("⚙️ Engine Status")
    if st.session_state.engine:
        st.success("✅ Stockfish Connected")
    else:
        st.error("❌ Engine Not Available")
        st.caption("Analysis features limited")

# Main Content Area
if page == "🏠 Home":
    st.header("Welcome to Chess Learning Coach Pro!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-box">
            <h3>🎯 Personalized Coaching</h3>
            <p>Get AI-powered insights tailored to your playing style</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-box">
            <h3>📈 Track Progress</h3>
            <p>Monitor improvement across tactical, positional, and endgame skills</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-box">
            <h3>🔍 Deep Analysis</h3>
            <p>Stockfish-powered move analysis with detailed feedback</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("🚀 Quick Start Guide")
    
    st.markdown("""
    ### How to Use This Platform:
    
    1. **Analyze Your Games**
       - Go to the "Analyze Game" page
       - Paste your PGN (Portable Game Notation)
       - Click "Analyze Game" and wait for results
    
    2. **Review Insights**
       - See move-by-move classification
       - Identify blunders, mistakes, and brilliant moves
       - View evaluation charts
    
    3. **Get Personalized Recommendations**
       - Receive tailored training suggestions
       - Identify your weaknesses and strengths
       - Track improvement over time
    
    4. **Practice & Improve**
       - Follow the recommended training exercises
       - Focus on your weakest areas
       - Re-analyze games to measure progress
    """)
    
    st.markdown("---")
    
    st.info("💡 **Pro Tip**: Analyze your games immediately after playing while the positions are fresh in your mind!")

elif page == "📊 Analyze Game":
    st.header("📊 Game Analysis")
    
    tab1, tab2 = st.tabs(["Analyze New Game", "Position Analysis"])
    
    with tab1:
        st.subheader("Upload Game for Analysis")
        
        pgn_input = st.text_area(
            "Paste PGN here",
            height=200,
            placeholder="""[Event "Casual Game"]
[Site "?"]
[Date "2025.01.20"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6..."""
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            analysis_depth = st.slider("Analysis Depth", 10, 20, 15, 
                                      help="Higher depth = more accurate but slower")
        
        with col2:
            analyze_button = st.button("🔍 Analyze Game", type="primary", use_container_width=True)
        
        if analyze_button and pgn_input:
            with st.spinner("🤔 Analyzing game with Stockfish..."):
                progress_bar = st.progress(0)
                analysis = analyze_complete_game(pgn_input, progress_bar)
                
                if analysis:
                    st.session_state.game_analysis = analysis
                    st.session_state.user_profile['games_played'] += 1
                    progress_bar.empty()
                    st.success("✅ Analysis complete!")
                else:
                    st.error("❌ Invalid PGN format. Please check your input.")
        
        # Display Analysis Results
        if st.session_state.game_analysis:
            st.markdown("---")
            st.subheader("📈 Analysis Results")
            
            analysis = st.session_state.game_analysis
            
            # Summary Statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            total_moves = len(analysis)
            brilliant = len([m for m in analysis if m['classification'] == 'brilliant'])
            blunders = len([m for m in analysis if m['classification'] == 'blunder'])
            mistakes = len([m for m in analysis if m['classification'] == 'mistake'])
            accuracy = ((total_moves - blunders - mistakes) / total_moves * 100) if total_moves > 0 else 0
            
            col1.metric("Total Moves", total_moves)
            col2.metric("Brilliant", brilliant, delta=None)
            col3.metric("Blunders", blunders, delta=None, delta_color="inverse")
            col4.metric("Mistakes", mistakes, delta=None, delta_color="inverse")
            col5.metric("Accuracy", f"{accuracy:.1f}%")
            
            # Evaluation Chart
            st.plotly_chart(plot_evaluation_chart(analysis), use_container_width=True)
            
            # Move by Move Analysis
            st.subheader("📝 Move-by-Move Breakdown")
            
            df_moves = pd.DataFrame([{
                'Move #': m['move_number'],
                'Player': m['player'],
                'Move': m['san'],
                'Classification': m['classification'].title(),
                'Symbol': m['symbol'],
                'Eval': f"{m['eval_after']:+.2f}",
                'CP Loss': m['centipawn_loss']
            } for m in analysis])
            
            st.dataframe(df_moves, use_container_width=True, hide_index=True)
            
            # Weaknesses and Recommendations
            st.markdown("---")
            weaknesses, strengths, recommendations = generate_weakness_report(analysis)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if strengths:
                    st.subheader("💪 Strengths")
                    for strength in strengths:
                        st.markdown(f"""
                        <div class="strength-box">
                            <strong>{strength['area']}</strong><br>
                            {strength['description']}
                        </div>
                        """, unsafe_allow_html=True)
            
            with col2:
                if weaknesses:
                    st.subheader("⚠️ Areas for Improvement")
                    for weakness in weaknesses:
                        st.markdown(f"""
                        <div class="weakness-box">
                            <strong>{weakness['area']}</strong> 
                            <span style="color: red;">({weakness['severity']} Priority)</span><br>
                            {weakness['description']}
                        </div>
                        """, unsafe_allow_html=True)
            
            if recommendations:
                st.markdown("---")
                st.subheader("🎯 Personalized Training Recommendations")
                for rec in recommendations:
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <strong>{rec['title']}</strong> 
                        <span style="color: blue;">({rec['priority']} Priority)</span><br>
                        {rec['description']}
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Analyze Specific Position")
        
        fen_input = st.text_input(
            "Enter FEN",
            value="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            help="Forsyth-Edwards Notation"
        )
        
        if st.button("Analyze Position"):
            try:
                board = chess.Board(fen_input)
                analysis_result = analyze_position(board, depth=18)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(render_board_svg(board, size=400), unsafe_allow_html=True)
                
                with col2:
                    st.metric("Evaluation", f"{analysis_result['evaluation']:+.2f} pawns")
                    
                    if analysis_result['mate_in']:
                        st.success(f"🎯 Mate in {abs(analysis_result['mate_in'])} moves!")
                    
                    if analysis_result['best_move']:
                        st.info(f"💡 Best move: **{analysis_result['best_move']}**")
                    
                    if analysis_result['pv']:
                        st.write("**Principal Variation:**")
                        st.code(" ".join(analysis_result['pv'][:3]))
                
            except Exception as e:
                st.error(f"Invalid FEN: {e}")

elif page == "👤 Profile":
    st.header("👤 Player Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Stats Overview")
        st.metric("Current Rating", st.session_state.user_profile['rating'])
        st.metric("Games Analyzed", st.session_state.user_profile['games_played'])
        st.metric("Win Rate", "N/A")
    
    with col2:
        st.subheader("Performance Metrics")
        
        # Sample performance data
        metrics = {
            'Tactical Accuracy': 75,
            'Positional Awareness': 68,
            'Endgame Skill': 72,
            'Opening Knowledge': 65,
            'Time Management': 80
        }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=list(metrics.values()),
            theta=list(metrics.keys()),
            fill='toself',
            name='Your Performance',
            line_color='rgb(147, 51, 234)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=False,
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

elif page == "📚 Resources":
    st.header("📚 Learning Resources")
    
    st.subheader("🎯 Recommended Training")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Tactical Training
        - **Chess.com Puzzles**: Daily tactical puzzles
        - **Lichess Puzzle Rush**: Timed tactical challenges
        - **ChessTempo**: Rating-based puzzle training
        
        ### Opening Study
        - Study 2-3 openings deeply
        - Learn key principles, not just moves
        - Practice against engines
        """)
    
    with col2:
        st.markdown("""
        ### Endgame Practice
        - Master basic endgames first
        - King and pawn endgames
        - Rook endgames
        
        ### Strategic Improvement
        - Watch annotated master games
        - Study pawn structures
        - Improve position evaluation
        """)
    
    st.markdown("---")
    
    st.subheader("📖 Recommended Books")
    st.markdown("""
    1. **"The Amateur's Mind"** by Jeremy Silman
    2. **"Understanding Chess Middlegames"** by John Nunn
    3. **"100 Endgames You Must Know"** by Jesus de la Villa
    4. **"Logical Chess: Move by Move"** by Irving Chernev
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>Chess Learning Coach Pro | Powered by Stockfish Engine</p>
    <p>Built with ❤️ using Streamlit | © 2025</p>
</div>
""", unsafe_allow_html=True)
