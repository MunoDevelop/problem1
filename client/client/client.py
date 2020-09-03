import socket 
from _thread import *
from threading import Thread
import sys

HOST = '127.0.0.1'
PORT = 5050

client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
userId = ""
while True:
    print("사용할id 를 입력해 주세요( _ )")
    userId = input()
    if '_' in userId:
        print("_ 를 사용하지 말아 주세요")
        continue
    break
#------------------------- try
try:
    client_socket.connect((HOST, PORT)) 
    client_socket.send(userId.encode()) 
except socket.error as e:
    print(e)


def acceptMsg():
    while True: 
        try:
            #message = input('Enter Message : ')
            

            #client_socket.send(message.encode()) 
            data = client_socket.recv(4096) 

            print(str(data.decode())) 
            sys.stdout.flush()
        except socket.error as e:
                print("서버 다운")
                input()
    socket.close()
th = Thread(target = acceptMsg)
th.start()

#def flushPrintBuffer():
    #timer = threading.Timer(7.0, afterSevenSecond)
# 키보드로 입력한 문자열을 서버로 전송하고 

# 서버에서 에코되어 돌아오는 메시지를 받으면 화면에 출력합니다. 

# quit를 입력할 때 까지 반복합니다. 

while True: 
    try:
        #data = client_socket.recv(1024) 

        #print(str(data.decode())) 
        #acceptMsg()

        #print("숫자선택 : ")
        msg = input()

        client_socket.send(msg.encode()) 
    
    except socket.error as e:
        print("서버 다운")
        input()


client_socket.close() 