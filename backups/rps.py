import pygame
import random
import socket
import threading

# pygame 초기화
pygame.init()

# 화면 크기 설정
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# 폰트 설정
font = pygame.font.Font(None, 36)

# 게임 옵션들
OPTIONS = ["Rock", "Paper", "Scissors"]

# 이미지 로드 (가상의 이미지 경로, 실제 이미지를 사용하려면 경로 수정 필요)
rock_img = pygame.Surface((100, 100))
paper_img = pygame.Surface((100, 100))
scissors_img = pygame.Surface((100, 100))
rock_img.fill((200, 0, 0))
paper_img.fill((0, 200, 0))
scissors_img.fill((0, 0, 200))

images = {"Rock": rock_img, "Paper": paper_img, "Scissors": scissors_img}

# 네트워크 설정
HOST = '127.0.0.1'
PORT = 65432
player_choice = None
opponent_choice = None
result = ""
connected = False

# 소켓 설정
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def handle_server():
    global opponent_choice, result
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data.startswith("OPPONENT:"):
                opponent_choice = data.split(":")[1]
                determine_winner()
        except:
            break

def determine_winner():
    global result
    if player_choice == opponent_choice:
        result = "Draw"
    elif (player_choice == "Rock" and opponent_choice == "Scissors") or \
         (player_choice == "Paper" and opponent_choice == "Rock") or \
         (player_choice == "Scissors" and opponent_choice == "Paper"):
        result = "You Win!"
    else:
        result = "You Lose!"

# 서버에 연결
try:
    client_socket.connect((HOST, PORT))
    threading.Thread(target=handle_server, daemon=True).start()
    connected = True
except:
    print("Unable to connect to the server.")

# 게임 루프
running = True
while running:
    screen.fill(WHITE)

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and connected:
            mouse_x, mouse_y = event.pos
            # 플레이어의 선택 처리
            if 50 < mouse_y < 150:
                if 50 < mouse_x < 150:
                    player_choice = "Rock"
                elif 250 < mouse_x < 350:
                    player_choice = "Paper"
                elif 450 < mouse_x < 550:
                    player_choice = "Scissors"
                # 서버에 선택 전송
                if player_choice:
                    client_socket.sendall(f"CHOICE:{player_choice}".encode())

    # 화면에 텍스트 및 이미지 그리기
    rock_text = font.render("Rock", True, BLACK)
    paper_text = font.render("Paper", True, BLACK)
    scissors_text = font.render("Scissors", True, BLACK)
    screen.blit(rock_text, (75, 160))
    screen.blit(paper_text, (275, 160))
    screen.blit(scissors_text, (475, 160))

    screen.blit(rock_img, (50, 50))
    screen.blit(paper_img, (250, 50))
    screen.blit(scissors_img, (450, 50))

    # 플레이어와 상대방의 선택 및 결과 표시
    if player_choice and opponent_choice:
        player_text = font.render(f"Player: {player_choice}", True, BLACK)
        opponent_text = font.render(f"Opponent: {opponent_choice}", True, BLACK)
        result_text = font.render(result, True, BLACK)
        screen.blit(player_text, (50, 250))
        screen.blit(opponent_text, (50, 300))
        screen.blit(result_text, (50, 350))

    # 화면 업데이트
    pygame.display.flip()

# 소켓 종료
client_socket.close()
# pygame 종료
pygame.quit()
