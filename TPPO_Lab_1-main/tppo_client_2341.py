1#!/usr/bin/env python3
import socket, time
import threading as thread 


class IpPortChecker:
    def ip_checker(self, ip):
        try:
            ip = str(ip)
            ip = ip or 'localhost'
            ip_check = ip.split('.')
            for i in ip_check:
                int(i)
        except Exception as e:
            ip = 'localhost'
        return ip

    def port_checker(self, port):
        if len(port) == 0:
            port = 4000
        try:
            port = int(port)
        except Exception as e:
            port = 4000
        return port

ip = input('Enter IP: ')
port = input('Enter port: ')
checker = IpPortChecker()
ip = checker.ip_checker(ip)
port = checker.port_checker(port)

print (ip, port)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
print ('Connect is ready')


def receiver ():
    while True:
        try:
            message = s.recv(1024).decode()
            message = message.rstrip()
            print (message)
        except:
            break
        
def sender ():
    while True:
        cmd = input ('\n Type command: ')
        if cmd == '/exit':
            s.send (cmd.encode())
            s.close()
            break
        s.send (cmd.encode())
        time.sleep(0.2)
        

sender = thread.Thread(target=sender)
receiver = thread.Thread(target= receiver)

receiver.start()
time.sleep(0.2)
sender.start()
