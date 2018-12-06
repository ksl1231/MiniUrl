import os, sys, socket, struct, select, time, signal


"""转载于 https://pypi.org/project/python3-ping
   做了一些删减改造

   Example:
    verbose_ping('www.zhihu.com')
"""

if sys.platform == "win32":
    default_timer = time.clock
else:
    default_timer = time.time

''' ICMP参数 '''
ICMP_ECHOREPLY  =    0 
ICMP_ECHO       =    8 
ICMP_MAX_RECV   = 2048 
MAX_SLEEP = 1000

class MyStats:
    thisIP   = "0.0.0.0"
    pktsSent = 0
    pktsRcvd = 0
    minTime  = 999999999
    maxTime  = 0
    totTime  = 0
    avrgTime = 0
    fracLoss = 1.0

myStats = MyStats

#=============================================================================#
def checksum(source_string):

    countTo = (int(len(source_string)/2))*2
    sum = 0
    count = 0

    loByte = 0
    hiByte = 0
    while count < countTo:
        if (sys.byteorder == "little"):
            loByte = source_string[count]
            hiByte = source_string[count + 1]
        else:
            loByte = source_string[count + 1]
            hiByte = source_string[count]
        try:     # For Python3
            sum = sum + (hiByte * 256 + loByte)
        except:  # For Python2
            sum = sum + (ord(hiByte) * 256 + ord(loByte))
        count += 2


    if countTo < len(source_string): 
        loByte = source_string[len(source_string)-1]
        try:      # For Python3
            sum += loByte
        except:   # For Python2
            sum += ord(loByte)

    sum &= 0xffffffff 
                    

    sum = (sum >> 16) + (sum & 0xffff)   
    sum += (sum >> 16)                   
    answer = ~sum & 0xffff             
    answer = socket.htons(answer)

    return answer

#=============================================================================#
def do_one(myStats, destIP, hostname, timeout, mySeqNumber, numDataBytes, quiet = False):

    delay = None

    try: 
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    except socket.error as e:
        return e

    my_ID = os.getpid() & 0xFFFF

    sentTime = send_one_ping(mySocket, destIP, my_ID, mySeqNumber, numDataBytes)
    if sentTime == None:
        mySocket.close()
        return delay

    myStats.pktsSent += 1

    recvTime, dataSize, iphSrcIP, icmpSeqNumber, iphTTL = receive_one_ping(mySocket, my_ID, timeout)

    mySocket.close()

    if recvTime:
        delay = (recvTime-sentTime)*1000
        if not quiet:
            x = ("%d bytes from %s (%s): icmp_seq=%d ttl=%d time=%d ms" % (
                dataSize, hostname, socket.inet_ntoa(struct.pack("!I", iphSrcIP)), icmpSeqNumber, iphTTL, delay)
            )
        myStats.pktsRcvd += 1
        myStats.totTime += delay
        if myStats.minTime > delay:
            myStats.minTime = delay
        if myStats.maxTime < delay:
            myStats.maxTime = delay
    else:
        delay = None
        x = 'timeout'
    return delay,x

def send_one_ping(mySocket, destIP, myID, mySeqNumber, numDataBytes):

    myChecksum = 0

    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
    )

    padBytes = []
    startVal = 0x42

    if sys.version[:1] == '2':
        bytes = struct.calcsize("d")
        data = ((numDataBytes - 8) - bytes) * "Q"
        data = struct.pack("d", default_timer()) + data
    else:
        for i in range(startVal, startVal + (numDataBytes-8)):
            padBytes += [(i & 0xff)] 

        data = bytearray(padBytes)


    myChecksum = checksum(header + data)


    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
    )

    packet = header + data

    sendTime = default_timer()

    try:
        mySocket.sendto(packet, (destIP, 1))
    except socket.error as e:
        print("General failure (%s)" % (e.args[1]))
        return

    return sendTime

def receive_one_ping(mySocket, myID, timeout):

    timeLeft = timeout/1000

    while True: 
        startedSelect = default_timer()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (default_timer() - startedSelect)
        if whatReady[0] == []: # Timeout
            return None, 0, 0, 0, 0

        timeReceived = default_timer()

        recPacket, addr = mySocket.recvfrom(ICMP_MAX_RECV)

        ipHeader = recPacket[:20]
        iphVersion, iphTypeOfSvc, iphLength, \
        iphID, iphFlags, iphTTL, iphProtocol, \
        iphChecksum, iphSrcIP, iphDestIP = struct.unpack(
            "!BBHHHBBHII", ipHeader
        )

        icmpHeader = recPacket[20:28]
        icmpType, icmpCode, icmpChecksum, \
        icmpPacketID, icmpSeqNumber = struct.unpack(
            "!BBHHH", icmpHeader
        )

        if icmpPacketID == myID: # Our packet
            dataSize = len(recPacket) - 28
            return timeReceived, (dataSize+8), iphSrcIP, icmpSeqNumber, iphTTL

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None, 0, 0, 0, 0

def verbose_ping(hostname, timeout = 20000,  # 最大超时时间为1000ms
                     numDataBytes = 64, path_finder = False):

    myStats = MyStats()
    mySeqNumber = 0 
    try:
        destIP = socket.gethostbyname(hostname)
        myStats.thisIP = destIP
        delay,x = do_one(myStats, destIP, hostname, timeout, mySeqNumber, numDataBytes)
        if delay == None:
            delay = 0
        mySeqNumber += 1
        if (MAX_SLEEP > delay):
            time.sleep((MAX_SLEEP - delay)/1000)
        return x
    except:
        return 'None'




