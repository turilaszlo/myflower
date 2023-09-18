from machine import Pin, ADC
from time import sleep, localtime
import network, usocket, urequests, ntptime

def web_page():
    
    wlanSSID=open("wlanssid.txt","r")
    wlanKEY=open("wlankey.txt","r")
 
    lastValue=open("lastValue.txt","r")
 
    html = """
    <html>
    <head>
        <title>Moisture Sensor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="icon" href="data:,">
        <style>
            html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
            h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}
        </style>
    </head>
    <body>
        <h1>Moisture sensor</h1>
        <h2>Last sensor reading</h2>
          <p>""" + lastValue.read() +"""</p>
        <h2>Currently connected Wifi network</h2>
          <p>SSID: <strong>""" + wlanSSID.read() + """</strong>
        </br>password: <strong>""" + wlanKEY.read() + """</strong></p>
        <h2>Change Wifi network</h2>
        <form>
          <label for="wifinetwork">wifinetwork:</label><br>
          <input type="text" id="wifinetwork" name="wifinetwork"><br>

          <label for="password">password:</label><br>
          <input type="text" id="password" name="password"><br>
          <input type="submit" value="Submit">
        </form>
    </body>
    </html>"""
  
    return html

def updateWifi(ssid,pw):
    wlanssidFile=open("wlanssid.txt","w")
    wlanssidFile.write(ssid)
    wlanssidFile.close()    

    wlankeyFile=open("wlankey.txt","w")
    wlankeyFile.write(pw)
    wlankeyFile.close()
    
    success="wlan updated to: "+ssid+"/"+pw
    return success
    
def accessPoint():
    #wlan=network.WLAN(network.STA_IF)
    #wlan.active(True)
    #wlanSSID =open("wlanssid.txt","r")
    #wlanKEY=open("wlankey.txt","r")
    #wlan.connect(wlanSSID.read(), wlanKEY.read())
    #print('network config:',wlan.ifconfig())

    ap=network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Moisture-Sensor', authmode=network.AUTH_WPA_WPA2_PSK, password="moisture")
    print('access point: ', ap.ifconfig())
    blueLed(2,2)

    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)   
   
    while True:
      conn, addr = s.accept()
      print('Got a connection from %s' % str(addr))
      request = conn.recv(1024)
      request = str(request)
          
      parse1=request.split(" ")[1]
      if len(parse1)>1:
          parse2=parse1.split("&")
          wifiParam=parse2[0].split("=")
          wifi=wifiParam[1]
          passParam=parse2[1].split("=")
          password=passParam[1]
                    
          print(updateWifi(wifi,password))          
 
      response = web_page()
      conn.send('HTTP/1.1 200 OK\n')
      conn.send('Content-Type: text/html\n')
      conn.send('Connection: close\n\n')
      conn.sendall(response)
      conn.close() 

def moistureSensor():
    red=Pin(4,Pin.OUT)
    green=Pin(5,Pin.OUT)
    green(0)
    red(0)

    sm =ADC(0)
    sm_value = sm.read()

    if sm_value<=310:
        for i in range(10):
            green(0)
            sleep(0.1)
            green(1)
            sleep(0.1)
        status="TOO WET"
    elif 310<sm_value<=380:
        green(1)
        status="IDEAL"
    else:
        red(1)
        status="DRY"
    
    return sm_value

def wlanConnect():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(True)
    wlanSSID=open("wlanssid.txt","r")
    wlanKEY=open("wlankey.txt","r")    
    wlan.connect(wlanSSID.read(), wlanKEY.read())
    while not wlan.isconnected(): # wait till we are really connected
            print('.', end='')
            sleep(0.1)
    print('wlan config: ',wlan.ifconfig())  
    
    if wlan.ifconfig()[0]!='0.0.0.0':
        connection=True
    else:
        connection=False      
    return connection

def uploadData(sm_value):
    if wlanConnect()==True:
        print('localtime before NTP: ',str(localtime()[0:5]))
        url="http://myflower.eu.pythonanywhere.com/smvalue/"+str(sm_value)
        requestResult=urequests.get(url)
        print(requestResult.text)
        
        if sm_value<=310:      
            status="TOO WET"
        elif 310<sm_value<=380:
            status="IDEAL"
        else:
            status="DRY"
            
        ntptime.settime()
        devicelog="last value: "+ str(sm_value)+" ("+status+")<br/>timestamp, GMT:  "+str(localtime()[0:5])
        devicelogFile=open("lastValue.txt","w")
        devicelogFile.write(devicelog)
        devicelogFile.close()
        print(devicelog)            
        
        blueLed(3,0.5)
             
    else:
        print('upload failed')
        blueLed(10,0.1)
        pass

def blueLed(blink,sleepTime):
    blue=Pin(2,Pin.OUT)
    for i in range(blink):
        blue(0)
        sleep(sleepTime)
        blue(1)
        sleep(sleepTime)
