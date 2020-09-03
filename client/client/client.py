import socket 
from _thread import *
from threading import Thread
import sys


HOST = '127.0.0.1'
PORT = 5050
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
userId = ""
# id 에 _의 입력을 금지합니다.
while True:
    print("사용할id 를 입력해 주세요( _ )")
    userId = input()
    if '_' in userId:
        print("_ 를 사용하지 말아 주세요")
        continue
    break
#연결을 시도합니다. 연결되면 사용자가 원하는 userId를 전송합니다.
try:
    client_socket.connect((HOST, PORT)) 
    client_socket.send(userId.encode()) 
except socket.error as e:
    print(e)

#메세지접수는 별도의 스레드에서 진행됩니다
def acceptMsg():
    while True: 
        try:
            data = client_socket.recv(4096) 

            print(str(data.decode())) 
            sys.stdout.flush()
        except socket.error as e:
                print("서버 다운")
                input()
    socket.close()
th = Thread(target = acceptMsg)
th.start()


#사용자의 입력을 서버에 전송합니다.
while True: 
    try:
        msg = input("숫자선택 : ")

        client_socket.send(msg.encode()) 
    
    except socket.error as e:
        print("서버 다운")
        input()

client_socket.close() 