import logging
import os
import random
import re
import socket
import threading
import time

import pandas as pd
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG, filename=u'log.log')
subs = []


class IpPortChecker:
    def ip_checker(self, ip_address):
        try:
            ip_address = str(ip_address)
            ip_address = ip_address or 'localhost'
            ip_check = ip_address.split('.')
            for i in ip_check:
                int(i)
        except Exception:
            ip_address = 'localhost'
        return ip_address

    def port_checker(self, port_value):
        if len(port_value) == 0:
            port_value = 4000
        try:
            port_value = int(port_value)
        except BaseException:
            port_value = 4000
        return port_value


class MyHandler(FileSystemEventHandler):

    def __init__(self, subscribers, socket_instance):
        self.subs = subscribers
        self.socket_instance = socket_instance

    def on_created(self, event):
        print("on_created", event.src_path)
        try:
            logging.info('Handler message: File has been created')
            params = {'Params': ['Handler message: File has been created'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.socket_instance.send(message.encode())
            self.socket_instance.send('\nFile has been created'.encode())
        except Exception as err:
            logging.exception(err)
            pass

    # def on_deleted(self, event):
    #     print("on_deleted", event.src_path)
    #     logging.info('Handler message: File has been deleted')
    #     params = {'Params': ['Handler message: File has been deleted'], }
    #     df = pd.DataFrame(params)
    #     df = df.set_index('Params')
    #     message = df.to_xml() + '\n'
    #     self.socket_instance.send(message.encode())

    def on_modified(self, event):
        print("on_modified", event.src_path)
        data = pd.read_json(event.src_path)
        speed = data.loc[0, 'Speed']
        t_in = data.loc[0, 'T_in']
        t_out = data.loc[0, 'T_out']
        df = pd.DataFrame({'Speed': [speed], 'T_in': [t_in], 'T_out': [t_out]})
        message = df.to_xml() + '\n'
        for single_sock in self.subs:
            single_sock.send(message.encode())
        logging.info('Handler message: File has been modified')

    def on_moved(self, event):
        print("on_moved", event.src_path)
        logging.info('File has been moved')
        params = {'Params': ['File has been moved'], }
        df = pd.DataFrame(params)
        df = df.set_index('Params')
        message = df.to_xml() + '\n'
        self.socket_instance.send(message.encode())


class ConditionerConfig:
    def create_cond_file(self, speed, t_in, t_out=random.randrange(10, 40)):
        params = {'Speed': [speed], 'T_in': [t_in], 'T_out': [t_out]}
        df = pd.DataFrame(params)
        df.to_json('conditioner.json')
        logging.info('Create config file: File has been created')
        print('File has been created')

    def get_cond_info(self):

        data = pd.read_json('conditioner.json')
        speed = data.loc[0, 'Speed']
        t_in = data.loc[0, 'T_in']
        t_out = data.loc[0, 'T_out']
        t_out = t_out + random.randrange(-2, 2)

        return t_in, speed, t_out

    def set_speed(self, speed):
        data = pd.read_json('conditioner.json')
        data.loc[0, 'Speed'] = speed
        try:
            data = data.drop(["level_0"], axis=1)
        except Exception as err:
            logging.error(err)
            pass
        data.to_json('conditioner.json')
        logging.info('New speed accepted')

    def set_t_in(self, t_in):
        data = pd.read_json('conditioner.json')
        data.loc[0, 'T_in'] = t_in
        try:
            data = data.drop(["level_0"], axis=1)
        except Exception as err:
            logging.error(err)
            pass
        data.to_json('conditioner.json')
        logging.info('New temperature inside accepted')

    def set_t_out(self, t_out=random.randrange(10, 40)):
        t_out = random.randrange(10, 40)
        return t_out

    def check_cond(self):
        if not os.path.exists('conditioner.json'):
            current_speed = 0
            current_t_in = 0
            current_t_out = self.set_t_out()
            logging.info('File conditioner not exist')
            self.create_cond_file(current_speed, current_t_in, current_t_out)
            print('File conditioner not exist')
        else:
            t_in, speed, t_out = self.get_cond_info()
            logging.info('Conditioner file:ready')
            print(f"Conditioner file ready to use\n"
                  f"Current speed: {speed} rpm\n"
                  f"Current temperature inside: {t_in} C\n"
                  f"Current temperature outside: {t_out} C")


class ConditionerCycle:
    def __init__(self, subscribers, socket_instance):
        self.subs = subscribers
        self.sock = socket_instance

    def check_cond_info(self, conditioner_config):
        t_in, speed, t_out = conditioner_config.get_cond_info()
        df = pd.DataFrame({'Speed': [speed], 'T_in': [t_in], 'T_out': [t_out]})
        message = df.to_xml() + '\n'
        self.sock.send(message.encode())
        logging.info(message)

    def set_speed_info(self, result, conditioner_config):
        try:
            result = int(result[0])
            if 10 >= result >= 0:
                speed = result
                conditioner_config.set_speed(speed)
                self.check_cond_info(conditioner_config)
                conditioner_config.get_cond_info()

            else:
                logging.warning('Incorrect speed value')
                params = {'Params': ['Sorry, incorrect value'], }
                df = pd.DataFrame(params)
                df = df.set_index('Params')
                message = df.to_xml() + '\n'
                self.sock.send(message.encode())
        except Exception as err:
            logging.error(err)
            logging.warning('Incorrect speed value')
            params = {'Params': ['Sorry, incorrect value'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.sock.send(message.encode())

    def set_t_in_info(self, result, conditioner_config):
        try:
            result = int(result[0])
            if 35 >= result >= 15:
                t_in = result
                conditioner_config.set_t_in(t_in)
                self.check_cond_info(conditioner_config)
            else:
                logging.warning('Incorrect inside temperature  value')
                params = {'Params': ['Sorry, incorrect value'], }
                df = pd.DataFrame(params)
                df = df.set_index('Params')
                message = df.to_xml() + '\n'
                self.sock.send(message.encode())
        except Exception as err:
            logging.error(err)
            logging.warning('Incorrect inside temperature value')
            params = {'Params': ['Sorry, incorrect value'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.sock.send(message.encode())

    def stop(self, conditioner_config):
        speed = 0
        conditioner_config.set_speed(speed)
        params = {'Params': ['Conditioner stopped'], }
        df = pd.DataFrame(params)
        df = df.set_index('Params')
        message = df.to_xml() + '\n'
        self.sock.send(message.encode())
        logging.info(message)

    def subscribe(self, socket_instance):
        self.subs.append(socket_instance)

    def help(self):
        params = {'Params': [
            '"\nКоманда /get cond info - Получить значения скорости, целевой и внешней температуры" \ "\nКоманда /set '
            'speed [value] - Задать скорость вращения вентилятора (0-10 rpm)" \ "\nКоманда /set t_in [value] - Задать '
            'внутреннюю температуру кондиционера (10-35 С)" \ "\nКоманда /stop - Выключить кондиционер" \ "\nКоманда '
            '/help - Получить список всех команд" \ "\nКоманда /subscribe - Подписаться на уведомления" \   '
            '"\nКоманда /exit - отключиться от сервера'], }
        df = pd.DataFrame(params)
        df = df.set_index('Params')
        message = df.to_xml() + '\n'
        self.sock.send(message.encode())

    def log_fil_func(self, result):
        if result[0] == 'on':
            logger = logging.getLogger()
            logger.disabled = False
            message = '\nLogging enabled'
            self.sock.send(message.encode())
            logging.info(message)
        elif result[0] == 'off':
            logger = logging.getLogger()
            logger.disabled = True
            params = {'Params': ['\nLogging disabled (only warnings and errors)'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.sock.send(message.encode())
            logging.info(message)

    def admin_panel(self, result):
        if result[0] == '1111':
            params = {'Params': ['"\nКоманда /log off - Выключить сбор логов" \
                      "\nКоманда /log on - Включить сбор логов'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.sock.send(message.encode())
            logging.info('Admin')
        else:
            params = {'Params': ['\nIncorrect password'], }
            df = pd.DataFrame(params)
            df = df.set_index('Params')
            message = df.to_xml() + '\n'
            self.sock.send(message.encode())
            logging.info('Incorrect Admin password')


def client_connection(socket_instance, conditioner_cycle, conditioner_config):
    while True:
        try:
            content = "If you don't know what to do - write '/help'"
            df = pd.DataFrame({"content": [content]})
            message = df.to_xml() + '\n'
            socket_instance.send(message.encode())
            line = socket_instance.recv(1024).decode()
            line = line.rstrip()
            # Check conditioner file #
            if not os.path.exists('conditioner.json'):
                logging.info('Conditioner file not exist. Start creating')
                current_speed = 0
                current_t_in = 0
                conditioner_config.create_cond_file(current_speed, current_t_in)

            # Check conditioner info #
            if re.findall(r"/get cond info", line):
                print(re.findall(r"/get cond info", line))
                logging.info('Get "/get cond info" command')
                conditioner_cycle.check_cond_info(conditioner_config)

            # Set speed #
            elif re.findall(r"/set speed (\w+)", line):
                res = re.findall(r"/set speed (\w+)", line)
                print(res)
                logging.info('Get "/set speed" command with value ' + str(res[0]))
                conditioner_cycle.set_speed_info(res, conditioner_config)

            # Set t_in #
            elif re.findall(r"/set t_in (\w+)", line):
                res = re.findall(r"/set t_in (\w+)", line)
                print(res)
                logging.info('Get "/set t_in" command with value ' + str(res[0]))
                conditioner_cycle.set_t_in_info(res, conditioner_config)

            # Subscribe #
            elif re.findall(r"/subscribe", line):
                print(re.findall(r"/subscribe", line))
                logging.info('Get "/subscribe" command ')
                conditioner_cycle.subscribe(socket_instance)

            # Stop #
            elif re.findall(r"/stop", line):
                print(re.findall(r"/stop", line))
                logging.info('Get "/stop" command ')
                conditioner_cycle.stop(conditioner_config)

            # Help #
            elif re.findall(r"/help", line):
                print(re.findall(r"/help", line))
                logging.info('Get "/help" command ')
                conditioner_cycle.help()

            # Exit #
            elif re.findall(r"/exit", line):
                print(re.findall(r"/exit", line))
                logging.info('Get "/exit" command. Client went out ')
                print('Client went out ')
                socket_instance.close()
                break

            # En/Disable a log file #
            elif re.findall(r"/log (\w+)", line):
                print(re.findall(r"/log (\w+)", line))
                res = re.findall(r"/log (\w+)", line)
                logging.info('Get "/log"' + str(res[0]) + 'command ')
                conditioner_cycle.log_fil_func(res)

            # Admin panel #
            elif re.findall(r"/admin (\w+)", line):
                print(re.findall(r"/admin (\w+)", line))
                res = re.findall(r"/admin (\w+)", line)
                logging.info('Get "/admin" command with pass value: ' + str(res[0]))
                conditioner_cycle.admin_panel(res)

            # Check command
            else:
                print('Incorrect command')
                logging.warning('Incorrect command')
                params = {'Params': ['Sorry, No such command'], }
                df = pd.DataFrame(params)
                df = df.set_index('Params')
                message = df.to_xml() + '\n'
                socket_instance.send(message.encode())
            logging.info('Everything is ok')
            time.sleep(0.1)
        except Exception as err:
            logging.exception(err)


# Create a fan file #
cond_config = ConditionerConfig()
cond_config.check_cond()

# Create a socket #
ip = input('Enter IP: ')
port = input('Enter port: ')
checker = IpPortChecker()
ip = checker.ip_checker(ip)
port = checker.port_checker(port)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(5)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f"Server started on {ip}:{port}")

    # Create an observer #
    observer = Observer()
    observer.schedule(MyHandler(subscribers=subs, socket_instance=s), path='conditioner.json', recursive=True)
    observer.start()

    # Start a cycle #
    while True:
        socks, addr = s.accept()
        if socks:
            print('Get connected ', addr)
            logging.info('Client has connected ' + str(addr))
            cond_cycle = ConditionerCycle(subs, socks)
            t1 = threading.Thread(target=client_connection, args=(socks, cond_cycle, cond_config))
            t1.start()
            time.sleep(0.1)
        else:
            continue
except Exception as e:
    logging.exception(e)
    exit()
