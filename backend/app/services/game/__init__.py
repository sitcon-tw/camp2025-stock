"""
遊戲服務模組

包含：
- GameService: 遊戲邏輯服務
"""

from .game_service import GameService, get_game_service

__all__ = [
    "GameService",
    "get_game_service"
]