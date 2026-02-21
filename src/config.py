import os

"""
Configuration settings for the Adaptive Persuasion System
"""

class Config:
    # Validated 8B model (Text Mode)
    MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
    
    # ADK Voice Model (Voice Mode)
    # Options: gemini-2.0-flash-exp, gemini-2.0-flash-native-audio-preview
    ADK_VOICE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    
    # HuggingFace Token from System Environment
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # Google API Key for Voice Mode (Updated to match user's env var)
    GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # System settings
    TEMPERATURE = 0.8
    MAX_NEW_TOKENS = 64

    # ---- Initial states ----
    INITIAL_BELIEF = 0.15    # start higher so drops are visible
    INITIAL_TRUST = 0.9     # not perfect trust at start
    TRUST_THRESHOLD = 0.5   # threshold for recovery mode
    
    # Note: Trust can start lower if user expresses distrust early
    # This allows for recovery mode scenarios

    # ---- Learning rates (KEY CHANGE) ----
    ALPHA = 0.35   # belief moves clearly each turn
    BETA = 0.4     # trust reacts noticeably to skepticism
    GAMMA = 0.15   # recovery is visible but not instant

    # ---- Strategy adaptation ----
    HARD_REJECTION_PENALTY = 0.6
    SOFT_REJECTION_PENALTY = 0.35
    MIN_STRATEGY_WEIGHT = 0.05

    # ---- Conversation limits ----
    MAX_TURNS = 15
    MAX_CONSECUTIVE_REJECTIONS = 3

    LOG_FILE = "dialogue_log.jsonl"

    STRATEGIES = [
        "Empathy",
        "Impact",
        "SocialProof",
        "Transparency",
        "EthicalUrgency"
    ]
