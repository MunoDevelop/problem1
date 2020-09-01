import socket 
from _thread import *
import enum
from time import sleep


class User:
    priorityNumCounter = 0
    def __init__(self,userId,socket):
        self.userId = userId
        self.priorityNum = User.priorityNumCounter
        User.priorityNumCounter+=1
        self.socket = socket
    
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
            data = client_socket.recv(1024)
            # 비어있는 데이터가 전송될때
            if not data: 
                print('Disconnected by ' + addr[0],':',addr[1])
                break

            print('Received from ' + addr[0],':',addr[1] , data.decode())

            client_socket.send(data) 

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
# 클라이언트가 접속하면 accept 함수에서 새로운 소켓을 리턴합니다.

# 새로운 쓰레드에서 해당 소켓을 사용하여 통신을 하게 됩니다. 
while True: 
#region   유저의 수가 5보다 작을때 게임진행여부와 상관없이 항상 접수처리 
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
#endregion
    if gameState == GameState.NOT_PLAYING and len(userList)>=3:
        playerList.clear()
        # userList 와 playerList 의 객체는 같은 주소 사용 
        for user in sorted(userList, key=lambda user: user.priorityNum):
            playerList.append(user)
        #print([x.priorityNum for x in playerList])
        gameState = GameState.PLAY_TURNSTART

    if gameState == GameState.NOT_PLAYING:
        continue
    elif gameState == GameState.PLAY_WAIT_INPUT:
        continue
    elif gameState == GameState.PLAY_TURNSTART:

        continue


server_socket.close() 