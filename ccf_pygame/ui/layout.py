"""Shared 960x720 Broadcast layout geometry."""

import pygame

W, H = 960, 720

SCORE_H = 104
FIELD_Y, FIELD_H = 104, 124
BODY_Y = 228
ACTION_H = 84
ACTION_Y = 636
BODY_H = 408

RAIL_X, RAIL_W = 14, 252
CHART_W = 176
CHART_X = 770
CEN_X, CEN_W = 278, 480

SCORE_RECT = pygame.Rect(0, 0, W, SCORE_H)
FIELD_RECT = pygame.Rect(0, FIELD_Y, W, FIELD_H)
HAND_RECT = pygame.Rect(RAIL_X, BODY_Y + 8, RAIL_W, BODY_H - 16)
CHART_RECT = pygame.Rect(CHART_X, BODY_Y + 8, CHART_W, BODY_H - 16)
PLAY_RECT = pygame.Rect(CEN_X, BODY_Y + 8, CEN_W, 138)
LOG_RECT = pygame.Rect(CEN_X, BODY_Y + 156, CEN_W, 244)
ACTION_RECT = pygame.Rect(0, ACTION_Y, W, ACTION_H)
