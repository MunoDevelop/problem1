import socket 
from _thread import *
import enum
import threading
from random import randint

class User:
    priorityNumCounter = 0
    def __init__(self,userId,socket):
        self.userId = userId
        self.priorityNum = User.priorityNumCounter
        User.priorityNumCounter+=1
        self.socket = socket
class Player(User):
    def __init__(self, userId, socket,priorityNum,score,selectedNum):
        self.userId = userId
        self.priorityNum = priorityNum
        self.socket = socket
        self.score = score
        self.selectedNum = selectedNum
        
class GameState(enum.Enum):
    NOT_PLAYING = 0
    PLAY_WAIT_INPUT = 1
    PLAY_TURNSTART = 2


# 쓰레드에서 실행되는 코드입니다. 

# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다. 
def threaded(client_socket, addr): 
    print('Connected by :', addr[0], ':', addr[1]) 
    # 클라이언트가 접속을 끊을 때 까지 반복합니다. 
    while True: 
        try:
            # 데이터가 수신되면 클라이언트에 다시 전송합니다.(에코)
            if gameState == GameState.PLAY_WAIT_INPUT:
                text = str(client_socket.recv(1024).decode())
                if text.isdecimal():
                    num = int(text)
                    if num>=1 and num<=3:
                        #playerList 에 해당 플레이어가 있는 경우 해당 selectedNum을 변경 (없는경우는 무반응)
                        for player in playerList:
                            if player.socket == client_socket:
                                player.selectedNum = num

                        
            # 비어있는 데이터가 전송될때
            #if not data: 
            #    print('Disconnected by ' + addr[0],':',addr[1])
            #    break

            #print('Received from ' + addr[0],':',addr[1] , data.decode())

            #client_socket.send(data) 

        except ConnectionResetError as e:

            print('Disconnected by ' + addr[0],':',addr[1])
            break
             
    client_socket.close() 


HOST = '127.0.0.1'
PORT = 5050

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT)) 
server_socket.listen() 

print('server start')

userList = list()
playerList = list()
gameState = GameState.NOT_PLAYING
currentTurnNum = 0


def after5second():
    global timer
    #region  획득점수처리로직
    global currentTurnNum
    global gameState
    correctAns = playerList[currentTurnNum].selectedNum
    rightPlayerList = list()
    for player in playerList:
        if player!=playerList[currentTurnNum] and player.selectedNum == correctAns:
            rightPlayerList.append(player)
    if len(rightPlayerList) == 0:
        txt1 = "정답: "+str(correctAns)+"\n"
        txt2 = "정답을 맞춘 플레이어가 없기에 출제자 "+playerList[currentTurnNum].userId+"는 1점을 획득합니다.\n"
        for user in userList:
            user.socket.send((txt1+txt2).encode())

        playerList[currentTurnNum].score+=1
        currentTurnNum += 1
        if currentTurnNum > 2:
            currentTurnNum = 0
        gameState = GameState.PLAY_TURNSTART
        
        
    else:
        txt1 = "정답: "+str(correctAns)+"\n"
        txt2 = " ".join([x.userId for x in rightPlayerList])
        txt3 = "플레이어 "+txt2+"은 정답 "+ str(correctAns) +"을 맞추었기에 1점을 획득합니다.\n"
        for user in userList:
            user.socket.send((txt1+txt3).encode())
        for player in rightPlayerList:
            player.score+=1
        currentTurnNum += 1
        if currentTurnNum > 2:
            currentTurnNum = 0

        gameState = GameState.PLAY_TURNSTART
        
        
    #endregion
    winnerList = list()
    for player in playerList:
        if player.score == 3:
            winnerList.append(player)
    if len(winnerList) >0 :
        txt1 = "-------------------------------------\n"
        txt2 = "플레이어 "+ str([x.userId for x in winnerList]) +" 이 게임에서 승리하였습니다.\n"
        for user in userList:
            user.socket.send((txt1+txt2).encode())
        gameState = GameState.NOT_PLAYING
    



timer = threading.Timer(5.0, after5second)

def acceptUser():
    while True:
        try:
#region   유저의 수가 5보다 작을때 게임진행여부와 상관없이 항상 접수처리 (3이상은 관찰자)
            if len(userList)<5:
                client_socket, addr = server_socket.accept() 
                # 다른 사용자가 있으면 사용자id리스트를 전송
                if len(userList)>0:
                    msg = str(len(userList))+" other user online: "
                    msg2 = " ".join([x.userId for x in userList])
                    client_socket.send((msg + msg2).encode())
                
                data = client_socket.recv(1024)
                userId = data.decode()
                isUserIdExist = False
                for user in userList:
                    if userId == user.userId:
                        isUserIdExist = True
                if isUserIdExist:
                    # if same name user >2
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
#endregion

start_new_thread(acceptUser)


while True: 
    
    # 플레이중이 아니고 유저수가 3 이상일때만 게임시작
    if gameState == GameState.NOT_PLAYING and len(userList)>=3:
        playerList.clear()
        # userList 와 playerList 의 객체는 같은 주소 사용 
        for user in sorted(userList, key=lambda user: user.priorityNum):
            playerList.append(Player(user.userId,user.socket,user.priorityNum,0,0))
        gameState = GameState.PLAY_TURNSTART
        txt1 = "게임이 시작되었습니다\n"
        user.socket.send(txt1.encode())
        

    if gameState == GameState.NOT_PLAYING:
        
        continue
    elif gameState == GameState.PLAY_WAIT_INPUT:
        
        continue
    elif gameState == GameState.PLAY_TURNSTART:
        #
        for user in userList:
            id = playerList[currentTurnNum].userId
            txt1 = "-------------------------------------\n"
            txt2 = "플레이어 "+id+" 님이 숫자를 선택중입니다.\n"
            txt3 = "다른 플레이어들은 5초간 숫자를 선택하시고 선택하지 않으면\n"
            txt4 = "자동으로 1~3 사이의 숫자가 선택됩니다.\n"
            txt5 = "-------------------------------------\n"
            user.socket.send((txt1+txt2+txt3+txt4+txt5).encode())
            #선택할 숫자를 예정
        for player in playerList:
            player.selectedNum = randint(1,3)
        gameState = GameState.PLAY_WAIT_INPUT
        timer = threading.Timer(5.0, after5second)
        timer.start()
        #print("still going")
        


server_socket.close() 