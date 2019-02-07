"""
获取服务器信息，需要到vul对我们外网ip开放授权
"""

import paramiko
import requests
import socks
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formataddr

# 报告间隔，每天一次
CHECK_INTERVAL = 1

# 通知邮件的地址
NOTIFY_EMAIL_ADDRESS = ''

# SHADOWSOCKS SOCK5监听地址
PROXIES = {'http': 'socks5://127.0.0.1:1086', 'https': 'socks5://127.0.0.1:1086'}

# 请求头
# vultr提供商api key
HEADERS = {'API-Key': 'DQVUOPGBIZG3TXJ4YYOZTPNJPTOBX5DDIW4A'}

# SERVER信息
server_dict = {}


class AutoReport:
    def __init__(self):
        self.content = ''

    def disk_report(self):
        socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 1086, False)
        paramiko.client.socket.socket = socks.socksocket
        self.content += ('=====硬盘空间统计=====' + '\n')
        for (k, v) in server_dict.items():
            hostname = v['hostname']
            password = v['password']
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=hostname, port=22, username='root', password=password)
                std_in, std_out, std_err = ssh.exec_command('df -h')
                out = std_out.read()
                result = out.decode('utf-8')
                self.content += (k + ':' + '\n')
                for r in result.split('\n'):
                    self.content += (r + '\n')
                ssh.close()
            except TimeoutError as ex:
                self.content += (k + '连接失败:' + str(ex) + '\n')
            except Exception as ex:
                self.content += (k + '失败:' + str(ex) + '\n')
        self.content += '\n'

    def load_report(self):
        socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 1086, False)
        paramiko.client.socket.socket = socks.socksocket
        self.content += ('=====负载统计=====' + '\n')
        for (k, v) in server_dict.items():
            hostname = v['hostname']
            password = v['password']
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=hostname, port=22, username='root', password=password)
                std_in, std_out, std_err = ssh.exec_command('uptime')
                out = std_out.read()
                result = out.decode('utf-8')
                self.content += (k + ':' + '\n')
                self.content += (result + '\n')
                ssh.close()
            except TimeoutError as ex:
                self.content += (k + '连接失败:' + str(ex) + '\n')
            except Exception as ex:
                self.content += (k + '失败:' + str(ex) + '\n')
        self.content += '\n'

    def brand_report(self, r):
        self.content += ("=====流量统计=====" + '\n')
        for (k, v) in r.items():
            info = r[k]
            if info['label'] != '':
                self.content += (info['label'] + ': ' + str(info['current_bandwidth_gb']) + 'GB' + '\n')
        self.content += '\n'

    def get_info(self):
        response = requests.Response()
        # noinspection PyBroadException
        try:
            response = requests.get("https://api.vultr.com/v1/server/list", proxies=PROXIES, headers=HEADERS)
            json_dict = response.json()
            for (k, v) in json_dict.items():
                info = json_dict[k]
                if info['label'] != '':
                    label = info['label']
                    server_dict[label] = {}
                    server_dict[label]['hostname'] = info['main_ip']
                    server_dict[label]['password'] = info['default_password']
            return json_dict
        except Exception:
            print(response.content)
            time.sleep(5)
            self.get_info()

    def send_mail(self):
        try:
            if self.content != '':
                from_address = 'jira@himobi.net'
                password = 'Zn123456'
                to_address = NOTIFY_EMAIL_ADDRESS
                server = smtplib.SMTP_SSL("smtp.exmail.qq.com", 465)
                msg = MIMEText(self.content, 'plain', 'utf-8')
                msg['From'] = formataddr(["服务器信息报告", from_address])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
                msg['To'] = str(to_address)  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
                msg['Subject'] = '服务器信息报告'  # 邮件的主题，也可以说是标题
                server.login(from_address, password)
                server.sendmail(from_address, to_address, msg.as_string())
                server.quit()  # 关闭连接
        except Exception as e:
            print(e)

    def show(self):
        print(self.content)


if __name__ == '__main__':
    auto_report = AutoReport()
    result_dict = auto_report.get_info()
    auto_report.brand_report(result_dict)
    auto_report.load_report()
    auto_report.disk_report()
    # auto_report.send_mail()
    auto_report.show()
