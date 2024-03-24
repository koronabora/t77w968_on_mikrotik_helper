import re
import argparse
import paramiko
import time
import os
from pynput.keyboard import Key, Listener

introMsg = r'Welcome to T77W968 Mikrotik Helper. Press `Esc` to exit.'
helpMsg = r'''
Usage example (SSH should be enabled, `Esc` - exit):
  T77W968_signal.exe --host 192.168.88.1 --port 22 -u admin -p pass --delay 500
'''

class colors:
     reset = '\033[0m'
     bold = '\033[01m'
     disable = '\033[02m'
     underline = '\033[04m'
     reverse = '\033[07m'
     strikethrough = '\033[09m'
     invisible = '\033[08m'

     class fg:
          black = '\033[30m'
          red = '\033[31m'
          green = '\033[32m'
          orange = '\033[33m'
          blue = '\033[34m'
          purple = '\033[35m'
          cyan = '\033[36m'
          lightgrey = '\033[37m'
          darkgrey = '\033[90m'
          lightred = '\033[91m'
          lightgreen = '\033[92m'
          yellow = '\033[93m'
          lightblue = '\033[94m'
          pink = '\033[95m'
          lightcyan = '\033[96m'

     class bg:
          black = '\033[40m'
          red = '\033[41m'
          green = '\033[42m'
          orange = '\033[43m'
          blue = '\033[44m'
          purple = '\033[45m'
          cyan = '\033[46m'
          lightgrey = '\033[47m'
          white = '\033[37m'


command = r'interface lte at-chat lte1 input="AT^DEBUG?"'

client = paramiko.SSHClient()
def quit(key):
     if key == Key.esc:
          client.close()
          os._exit(0)

class SignalData:
     type = ''
     band = ''
     rssi = ''
     sinr = ''

     def getSinrColor(self):
          val = float(self.sinr.strip(r'dB'))
          if val < 10:
               return colors.fg.red
          elif val < 18:
               return colors.fg.orange
          else:
               return colors.fg.green

     def debug(self) -> str:
          return f'[B{self.band} {colors.fg.lightblue}RSSI: {self.rssi} {self.getSinrColor()}SINR: {self.sinr}{colors.reset}]'

sData = [[]]
sDataMaxLen = 30


def showData():
     data = sData[-1]
     out = ''
     for rec in data:
          out += rec.debug() + r' '
     print(out)

bandNames = [r'Main', r'Sub1', r'Sub2', r'Sub3', r'Sub4', r'Sub5']

rssiRegexp = re.compile(r'RSSI:\s*([^,\n]+)')
bandRegexp = re.compile(r'BAND:\s*([^,\n\s]+)')
sinrRegexp = re.compile(r'SNR:\s*([^,\n]+)')
def parse_out(data: list):
     global sData
     band = re.findall(bandRegexp, data)
     rssi = re.findall(rssiRegexp, data)
     sinr = re.findall(sinrRegexp, data)
     if (len(band) != len(rssi) or len(rssi) != len(sinr)):
         print('data error')
         return
     recData = list()
     for x in range(len(band)):
         rec = SignalData()
         rec.type = bandNames[x]
         rec.band = band[x].strip('\r')
         rec.rssi = rssi[x].strip('\r')
         rec.sinr = sinr[x].strip('\r')
         recData.append(rec)
     sData.append(recData)
     if len(sData) > sDataMaxLen:
          sData.pop(0)
     showData()


def main():
     parser = argparse.ArgumentParser(
          prog='T77W968 Mikrotik Helper',
          description='Show signal data from T77W969 on mikrotik',
          add_help=helpMsg)
     parser.add_argument('--host', help='ssh host', required=True)
     parser.add_argument('--port', help='ssh port', required=True)
     parser.add_argument('-u', help='ssh user', required=True)
     parser.add_argument('-p', help='ssh pass', required=True)
     parser.add_argument('--delay', type=int, help='requests delay in ms', default=500)
     try:
          args = parser.parse_args()
     except:
          parser.print_help()
          time.sleep(15)
          os._exit(0)

     print(introMsg)
     print(f'Connecting to router via ssh: {args.u}:{args.p}@{args.host}:{args.port}\n')

     try:
          client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
          client.connect(hostname=args.host, port=args.port, username=args.u, password=args.p, look_for_keys = False, allow_agent = False)

          listener =  Listener(on_press=quit, daemon=True)
          listener.start()
          while True:
              stdin, stdout, stderr = client.exec_command(command)
              parse_out(stdout.read().decode('ascii').strip('\n').strip('\r'))
              time.sleep(args.delay/1000.0)
          client.close()
     except Exception as error:
          print(f'Something went wrong:', type(error).__name__, '–', error)

if __name__ == '__main__':
     main()
