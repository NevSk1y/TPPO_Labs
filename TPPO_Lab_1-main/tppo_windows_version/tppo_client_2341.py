import socket
import threading as thread
import time


class ip_port_checker:
    def ip_checker(self, ip_addr):
        try:
            ip_addr = str(ip_addr)
            if len(ip_addr) == 0:
                ip_addr = 'localhost'
            ip_check = ip_addr.split('.')
            for i in ip_check:
                int(i)
        except:
            ip_addr = 'localhost'
        return ip_addr

    def port_checker(self, port_addr):
        if len(port_addr) == 0:
            port_addr = 4008
        try:
            port_addr = int(port)
        except:
            port_addr = 4008
        return port_addr


print('Enter IP')
ip = input()
print('Enter port')
port = input()
class_instance = ip_port_checker()

ip = class_instance.ip_checker(ip_addr=ip)
port = class_instance.port_checker(port_addr=port)

print(ip, port)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((ip, port))
s.connect((ip, port))
print('Connect is ready')


def receiver():
    while True:
        try:
            message = s.recv(1024).decode()
            message = message.rstrip()
            print(message)
        except:
            break


def sender():
    while True:
        cmd = input('\n Type command: ')
        # s.connect((ip, port))
        if cmd == '/exit':
            s.send(cmd.encode())
            s.close()
            break
        s.send(cmd.encode())
        time.sleep(0.2)


sender = thread.Thread(target=sender)
receiver = thread.Thread(target=receiver)

receiver.start()
time.sleep(0.2)
sender.start()
