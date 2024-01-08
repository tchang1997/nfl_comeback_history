import numpy as np

DRAW_SCALE = 10
X_HOME_ENDZONE = 0
X_HOME_10YD = 20
X_AWAY_GOAL_LINE = 110
X_AWAY_ENDZONE = 120
X_NUMBER_SPACING = 10
X_N_NUMBERS = 9
YARD_NUMBERS = list(map(str, list(np.arange(10, 51, X_NUMBER_SPACING)) + list(np.arange(40, 9, -X_NUMBER_SPACING))))

PLAY_HEIGHT = 12
DRIVE_PADDING = 20
TEXT_MARGIN = 3
