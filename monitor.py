#! /usr/bin/python
# -*- coding:utf-8 -*-
"""
监控服务器
"""
from email.mime.text import MIMEText
from email.utils import formataddr
from subprocess import PIPE
import threading
import smtplib
import time
import re
import subprocess

# 检测间隔，每5分钟
CHECK_INTERVAL = 15

# 通知邮件的地址
NOTIFY_EMAIL_ADDRESS = []


class Checker(object):
    last_send_mail_time = 0
    hostname = 'none'
    disk_on_fire = False
    mem_on_fire = False
    cpu_on_fire = False
    network_on_fire = False
    file_lock = threading.Lock()

    def __init__(self):
        print("init!")
        temp = subprocess.Popen('hostname', shell=True, stdout=PIPE, stderr=PIPE)
        self.hostname = temp.stdout.read().strip()
        print(self.hostname)

    @staticmethod
    def send_mail(content):
        if content != '':
            from_addr = 'jira@himobi.net'
            password = 'Zn123456'
            to_addr = NOTIFY_EMAIL_ADDRESS
            server = smtplib.SMTP_SSL("smtp.exmail.qq.com", 465)
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['From'] = formataddr(["服务器状态检测脚本", from_addr])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
            msg['To'] = str(to_addr)  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
            msg['Subject'] = '服务器状态异常通知'  # 邮件的主题，也可以说是标题
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addr, msg.as_string())
            server.quit()  # 关闭连接

    @staticmethod
    def shell_exc(shell_code):
        msg = subprocess.Popen(shell_code, shell=True, stdout=PIPE, stderr=PIPE)
        msg.wait()
        out = msg.stdout.readlines()
        return out

    def disk_util(self):
        shell_code = "df -h"
        while True:
            content = ''
            out = self.shell_exc(shell_code)
            for msg in out:
                if "vda" in msg.strip():
                    msg = re.split(r' +', msg.strip())
                    use = int(msg[4].split('%')[0])
                    if use >= 85:
                        if content != '':
                            content = content + '\n'
                        self.disk_on_fire = True
                        content = content + '主机 [' + self.hostname + '] 硬盘使用率告警,磁盘名:' + msg[0] + ',挂载点:' + msg[
                            5] + ',使用率:' + msg[4] + '剩余空间:' + msg[3]

            if content == '' and self.disk_on_fire:
                self.disk_on_fire = False
                content = '主机 [' + self.hostname + '] 硬盘使用率告警恢复.'

            self.send_mail(content)
            # self.write_log('磁盘使用率:999999%')
            time.sleep(CHECK_INTERVAL)

    def mem_util(self):
        shell_code = 'free -m'
        while True:
            content = ''
            out = self.shell_exc(shell_code)
            for msg in out:
                if 'Mem' in msg.strip():
                    msg = re.split(r' +', msg.strip())
                    free = int(msg[3]) + int(msg[5]) + int(msg[6])
                    total = float(msg[1])
                    usge = 1 - (free / total)
                    if usge > 0.9:
                        self.mem_on_fire = True
                        content = '主机 [' + self.hostname + '] 内存使用率告警,使用率为:' + str(usge * 100) + '%'

            if content == '' and self.mem_on_fire:
                self.mem_on_fire = False
                content = '主机 [' + self.hostname + '] 内存使用率告警恢复.'

            self.send_mail(content)
            # self.write_log('内存使用率:9999999%')
            time.sleep(CHECK_INTERVAL)

    def cpu_util(self):
        shell_code = 'sar 1 3'
        while True:
            content = ''
            out = self.shell_exc(shell_code)
            for msg in out:
                if 'Average' in msg.strip():
                    msg = re.split(r' +', msg.strip())
                    iowait = float(msg[5])
                    idle = float(msg[7])
                    if idle < 10:
                        self.cpu_on_fire = True
                        content = '主机 [' + self.hostname + '] cpu使用率告警,使用率为:' + str(100 - idle) + '%'
            if content == '' and self.cpu_on_fire:
                self.cpu_on_fire = False
                content = '主机 [' + self.hostname + '] cpu使用率告警恢复.'

            self.send_mail(content)
            # self.write_log('cpu使用率:99999999%')
            time.sleep(CHECK_INTERVAL)

    def network_util(self):
        shell_code = 'sar -n DEV 1 6'
        while True:
            content = ''
            out = self.shell_exc(shell_code)
            for msg in out:
                if 'Average' in msg.strip() and 'eth0' in msg.strip():
                    msg = re.split(r' +', msg.strip())
                    read = float(msg[4])
                    write = float(msg[5])
                    if read > 2048:
                        self.network_on_fire = True
                        content = '主机 [' + self.hostname + '] 网卡流量告警,流入速率为:' + str(read) + 'KB/S'
            if content == '' and self.network_on_fire:
                self.network_on_fire = False
                content = '主机 [' + self.hostname + '] 网卡流量告警恢复.'
            self.send_mail(content)
            # self.write_log('网卡流量:99999999KB/S')
            time.sleep(CHECK_INTERVAL)

    def run(self):
        threading.Thread(target=self.disk_util, name='disk_util').start()
        threading.Thread(target=self.mem_util, name='mem_util').start()
        threading.Thread(target=self.cpu_util, name='cpu_util').start()
        threading.Thread(target=self.network_util, name='network_util').start()

    def write_log(self, log):
        if self.file_lock.acquire(True):
            log_file = open('host_logs', 'a')
            log_file.write(time.asctime(time.localtime(time.time())) + ' ---------- ' + log + '\n')
            log_file.close()
            self.file_lock.release()


if __name__ == '__main__':
    Checker().run()
