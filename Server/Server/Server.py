import socket 
from _thread import *
import enum
import threading
from random import randint
import time

# userId 유저마다 입력한 아이디를 가지고 이미 존재하는경우 a_1 같은방식으로 중복을 방지합니다.
# priorityNum 서버에 접속한 유저마다 우선순위 번호를 받고 3명이상 연결시 누가 먼저 게임을 
# 시작하는지를 결정합니다.
# socket은 소켓정보를 저장합니다.
class User:
    priorityNumCounter = 0
    def __init__(self,userId,socket):
        self.userId = userId
        self.priorityNum = User.priorityNumCounter
        User.priorityNumCounter+=1
        self.socket = socket

# 플레이어의 priorityNum은 의미가 없습니다.
#score은 플레이할때 점수를 기록합니다.
#selectedNum은 유저가 매 라운드에서 선택한 숫자를 기록합니다.
class Player(User):
    def __init__(self, userId, socket,priorityNum,score,selectedNum):
        self.userId = userId
        self.priorityNum = priorityNum
        self.socket = socket
        self.score = score
        self.selectedNum = selectedNum

#게임의 상태는 플레이중이 아님/플레이중-유저인풋기다림/플레이중-턴시작시 중간상태 로 나뉩니다.
class GameState(enum.Enum):
    NOT_PLAYING = 0
    PLAY_WAIT_INPUT = 1
    PLAY_TURNSTART = 2

# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다. 
def threaded(client_socket, addr): 
    global userList
    global disconnectedPlayerList
    print('Connected by :', addr[0], ':', addr[1]) 
    
    while True: 
        try:
            text = str(client_socket.recv(1024).decode())
            # 게임상태가 플레이어 숫자선택을 기다리는 상태의 경우 
            if gameState == GameState.PLAY_WAIT_INPUT:
                #플레이어에게서 전달받은 데이가 숫자1~3인 경우
                if text.isdecimal():
                    num = int(text)
                    if num>=1 and num<=3:
                        #playerList 에 해당 플레이어가 있는 경우 해당 selectedNum을 변경 (없는경우는 무반응)
                        for player in playerList:
                            if player.socket == client_socket:
                                player.selectedNum = num
        #유저가 강제종료시 다른 유저에게 메서지를 출력
        except (ConnectionResetError,socket.error) as e:

            print('Disconnected by ' + addr[0],':',addr[1])
            #종료한 socket의 유저를 찾고
            for u in userList:
                if u.socket == client_socket:
                    user = u
            #게임중인 플레이어인 경우 연결종료한 플레이어 리스트에 기록합니다.
            for player in playerList:
                if player.userId == user.userId:
                    disconnectedPlayerList.append(player)
            #다른 유저에게 연결중단 메세지를 보냅니다.
            for u in userList:
                if u != user:
                    txt1 = "유저 "+ user.userId+ "이 서버와의 연결을 끊었습니다."
                    try:
                        u.socket.send(txt1.encode())
                    except socket.error as ee:
                        print(ee)
            userList.remove(user)
            break
             
    client_socket.close() 

try:
#서버소켓의 일반적 세팅
    HOST = '127.0.0.1'
    PORT = 5050
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT)) 
    server_socket.listen(5) 
except socket.error as e:
    print(e)
    

print('server start')

#유저 리스트는 게임중인 플레이어와 관찰자를 포함합니다.
userList = list()
playerList = list()
gameState = GameState.NOT_PLAYING
currentTurnNum = 0
disconnectedPlayerList = list()

def afterSevenSecond():
    # 7s이후 유저들은 숫자 선택을 완료 했다고 생각합니다.
    #  획득점수처리로직
    global currentTurnNum
    global gameState
    global playerList
    global userList
    global disconnectedPlayerList
    # 7s 기간동안   연결이 끊어진 상황의 예외처리를 먼저 수행
    # 연결을 끊은 유저가 1명 이상일 경우 수행하며
    # 연결을 끊은 유저가 1명, 2명,3명일 경우를 나누어서 처리합니다.
    if len(disconnectedPlayerList) != 0:
        #3명이 연결을 끊었을 경우
        if len(disconnectedPlayerList)>2:
            txt1 = "플레이어 "+(" ".join([x.userId for x in playerList]))+"모두 연결이 끊어졌기에 승자가 없어요.\n"
            for u in userList:
                u.socket.send(txt1.encode())
        #2명이 연결을 끊었을 경우
        elif len(disconnectedPlayerList)>1:
            for player in playerList:
                if player not in disconnectedPlayerList:
                    txt1 = "다른 플레이어의 연결이 모두 끊어져서 "+ player.userId+"가 게임에서 승리하였습니다\n"
                    for u in userList:
                        u.socket.send(txt1.encode())
        #1명이 연결을 끊었을 경우
        else:
            playerList.remove(disconnectedPlayerList[0])
            sp = sorted(playerList, key=lambda player: player.score)
            if sp[0].score == sp[1].score:
                txt1 = "한 플레이어의 연결이 끊어져서 남은 두명의 동점플레이어 "+(" ".join([x.userId for x in playerList]))+"가 승리자입니다\n"
            else:
                txt1 = "한 플레이어의 연결이 끊어졌기에 남은 플레이어중 점수가 높은 "+sp[1].userId+"가 승리자입니다\n"
            for u in userList:
                u.socket.send(txt1.encode())
        #게임플레이에 필요한 기본값을 다시 세팅합니다.
        currentTurnNum = 0
        gameState = GameState.NOT_PLAYING
        playerList.clear()
        disconnectedPlayerList.clear()
        return
    #현재 출제자의 정답을 correctAns 에 저장하고 정답을 맞춘 유저를 리스트에 저장합니다
    correctAns = playerList[currentTurnNum].selectedNum
    rightPlayerList = list()
    for player in playerList:
        if player!=playerList[currentTurnNum] and player.selectedNum == correctAns:
            rightPlayerList.append(player)
    #정답을 맞춘 유저가 없을 경우
    if len(rightPlayerList) == 0:
        playerList[currentTurnNum].score+=1
        txt1 = "정답: "+str(correctAns)+"\n"
        txt2 = "정답을 맞춘 플레이어가 없기에 출제자 "+playerList[currentTurnNum].userId+"는 1점을 획득합니다.\n"
        txt3 = "플레이어: "+ (" ".join([x.userId for x in playerList]))+"\n"
        txt4 = "현재점수: "+ (" ".join([str(x.score) for x in playerList]))+"\n"

        for user in userList:
            user.socket.send((txt1+txt2+txt3+txt4).encode())

        currentTurnNum += 1
        if currentTurnNum > 2:
            currentTurnNum = 0
        gameState = GameState.PLAY_TURNSTART
    #정답을 맞춘 유저가 있을 경우 맞춘 유저마다 1점을 획득합니다.
    else:
        for player in rightPlayerList:
            player.score+=1
        txt1 = "정답: "+str(correctAns)+"\n"
        txt2 = "플레이어 "+(" ".join([x.userId for x in rightPlayerList]))+"은 정답 "+ str(correctAns) +"을 맞추었기에 1점을 획득합니다.\n"
        txt3 = "플레이어: "+ (" ".join([x.userId for x in playerList]))+"\n"
        txt4 = "현재점수: "+ (" ".join([str(x.score) for x in playerList]))+"\n"
        for user in userList:
            user.socket.send((txt1+txt2+txt3+txt4).encode())
        
        currentTurnNum += 1
        if currentTurnNum > 2:
            currentTurnNum = 0

        gameState = GameState.PLAY_TURNSTART

    #마지막에 3 점을 획득하여 승리한 유저를 리스트에 넣고 
    #다른 유저들한테 메세지를 전송합니다.
    #승리한 유저가 없으면 PLAY_TURNSTART상태 , 있으면 NOT_PLAYING 상태로 전환됩니다.
    winnerList = list()
    for player in playerList:
        if player.score == 3:
            winnerList.append(player)
    if len(winnerList) >0 :
        txt1 = "-------------------------------------\n"
        txt2 = "플레이어 "+ str([x.userId for x in winnerList]) +" 이 3점을 먼저 획득하여 게임에서 승리하였습니다.\n"
        currentTurnNum = 0
        for user in userList:
            user.score = 0
            user.socket.send((txt1+txt2).encode())
        gameState = GameState.NOT_PLAYING
        

#유저의 연결요청을 처리합니다. 별도의 스레드로 진행됩니다.
def acceptUser():
    
    while True:
        try:
            
#  유저의 수가 5보다 작을때 게임진행여부와 상관없이 항상 접수처리합니다 (3이상은 관찰자)
            if len(userList)<5:
                
                client_socket, addr = server_socket.accept() 
                # 다른 사용자가 있으면 사용자id리스트를 전송합니다.
                if len(userList)>0:
                    msg = str(len(userList))+" other user online: "
                    msg2 = " ".join([x.userId for x in userList])
                    client_socket.send((msg + msg2).encode())
                
                data = client_socket.recv(1024)
                userId = data.decode()
                #새로 연결한 사용자가 요청한 이름이 이미 존재하는 경우 s_1 같은 방법으로 처리합니다.
                isUserIdExist = False
                for user in userList:
                    if userId == user.userId:
                        isUserIdExist = True
                if isUserIdExist:
                    # 같은 id가 존재하는 경우 가장 큰 s_N 보다 1크게 하여 충돌을 방지합니다.
                    
                    isUserIdExistTwice = False
                    for user in userList:
                        if userId + "_" in user.userId:
                            isUserIdExistTwice = True
                    if isUserIdExistTwice:
                        biggest = 0
                        for user in [x for x in userList if userId + "_" in x.userId]:
                            endNum = int(user.userId[user.userId.find("_")+1::])
                            if endNum>biggest:
                                biggest = endNum
                        userId += "_" + str(biggest+1)
                    else: 
                        userId = userId + "_1"

                userList.append(User(userId,client_socket))
                start_new_thread(threaded, (client_socket, addr)) 
        except socket.error as e:
            print(e)
            

start_new_thread(acceptUser,())



while True: 
    
    # 게임플레이 중이 아니고 유저수가 3 이상일때만 게임을 시작합니다.
    if gameState == GameState.NOT_PLAYING:
        if  len(userList)>=3:
            #먼저 서버에 연결한 3명의 유저를 선택하여 게임을 시작합니다.
            for user in sorted(userList, key=lambda user: user.priorityNum):
                if len(playerList)<3:
                    playerList.append(Player(user.userId,user.socket,user.priorityNum,0,0))
            gameState = GameState.PLAY_TURNSTART
            txt1 = "게임이 시작되었습니다."
            txt2 = "플레이어 "+(" ".join([x.userId for x in playerList]))+"가 게임에 참여중입니다.\n"
            for user in userList:
                user.socket.send((txt1+txt2).encode())
    elif gameState == GameState.PLAY_WAIT_INPUT:
        
        continue
    elif gameState == GameState.PLAY_TURNSTART:
        
        for user in userList:
            id = playerList[currentTurnNum].userId
            txt1 = "-------------------------------------\n"
            txt2 = "플레이어 "+id+" 님이 숫자를 선택중입니다.\n"
            txt3 = "다른 플레이어들은 7초간 숫자를 선택하시고 선택하지 않으면\n"
            txt4 = "자동으로 1~3 사이의 숫자가 선택됩니다.\n"
            txt5 = "-------------------------------------\n"
            user.socket.send((txt1+txt2+txt3+txt4+txt5).encode())
            #선택할 숫자를 예정합니다. 유저가 입력한 선택은 다른 스레드에서 입력됩니다.
        for player in playerList:
            player.selectedNum = randint(1,3)
        gameState = GameState.PLAY_WAIT_INPUT
        #7s 동안 서브스레드가 돌아가고 , 그동안 메인스레드는 sleep합니다
        timer = threading.Timer(7.0, afterSevenSecond)
        timer.start()
        time.sleep(7.4)


server_socket.close() 