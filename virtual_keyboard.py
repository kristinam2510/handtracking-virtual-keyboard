import cv2
import mediapipe as mp
import time

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# QWERTY layout (rows)
keyboard_layout = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
    ["Space", "Del", "Enter"]
]

# Colors
KEY_COLOR = (203, 72, 183)   # pink
HOVER_COLOR = (0, 255, 0)    # green
TEXT_COLOR = (255, 255, 255)
CHAT_BG = (0, 0, 0)          # black bar for chat

# Settings
current_text = ""
last_key = None
press_start_time = None
hold_time_required = 1.0  # seconds


def draw_keyboard(frame):
    """Draw the keyboard on screen."""
    key_positions = []
    h, w, _ = frame.shape
    start_x, start_y = 50, 150
    key_w, key_h, gap = 50, 50, 8   # smaller keys

    for row_idx, row in enumerate(keyboard_layout):
        for col_idx, key in enumerate(row):
            # Adjust width for Space, Del, Enter
            if key == "Space":
                this_w = key_w * 4
            elif key in ["Del", "Enter"]:
                this_w = key_w * 2
            else:
                this_w = key_w

            x = start_x
            for k in row[:col_idx]:
                if k == "Space":
                    x += key_w * 4 + gap
                elif k in ["Del", "Enter"]:
                    x += key_w * 2 + gap
                else:
                    x += key_w + gap

            y = start_y + row_idx * (key_h + gap)

            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x + this_w, y + key_h), KEY_COLOR, -1)
            cv2.rectangle(frame, (x, y), (x + this_w, y + key_h), (0, 0, 0), 2)

            # Draw text
            font_scale = 0.6 if len(key) == 1 else 0.5
            cv2.putText(frame, key, (x + 10, y + int(key_h * 0.65)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, TEXT_COLOR, 2)

            key_positions.append((key, (x, y, x + this_w, y + key_h)))
    return key_positions


def check_key_press(x, y, key_positions):
    """Check if fingertip is on a key."""
    for key, (x1, y1, x2, y2) in key_positions:
        if x1 < x < x2 and y1 < y < y2:
            return key
    return None


cap = cv2.VideoCapture(0)

# Fullscreen
cv2.namedWindow("Virtual Keyboard", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Virtual Keyboard", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    key_positions = draw_keyboard(frame)
    key = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            x = int(hand_landmarks.landmark[8].x * frame.shape[1])
            y = int(hand_landmarks.landmark[8].y * frame.shape[0])
            cv2.circle(frame, (x, y), 10, (255, 255, 0), -1)

            key = check_key_press(x, y, key_positions)

            if key:
                # Highlight hovered key
                for k, (x1, y1, x2, y2) in key_positions:
                    if k == key:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), HOVER_COLOR, -1)
                        cv2.putText(frame, k, (x1 + 10, y1 + int((y2-y1) * 0.65)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2)

                if key != last_key:
                    last_key = key
                    press_start_time = time.time()
                else:
                    if time.time() - press_start_time > hold_time_required:
                        if key == "Space":
                            current_text += " "
                        elif key == "Del":
                            current_text = current_text[:-1]
                        elif key == "Enter":
                            current_text = ""  # CLEAR chat bar instead of adding "?"
                        else:
                            current_text += key
                        last_key = None
                        press_start_time = None
            else:
                last_key = None
                press_start_time = None

    # Draw black chat bar
    cv2.rectangle(frame, (50, 50), (frame.shape[1] - 50, 120), CHAT_BG, -1)
    cv2.putText(frame, current_text, (70, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_COLOR, 3)

    cv2.imshow("Virtual Keyboard", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
