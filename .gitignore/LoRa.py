from network import LoRa
import socket
import binascii
import settings
import sys
import time
import pycom


def start(): 
    print('Started')
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AS923, device_class=LoRa.CLASS_C, adr=False)

    lora_otaa_join(lora)
    # create a LoRa socket
    lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
    # self.lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, self.config["lora"]["data_rate"])
    #lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, 2)

    # msg are confirmed at the FMS level
    lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 0)

    # make the socket non blocking y default
    lora_socket.setblocking(False)

    prepare_channels(lora, 2, 2)

    lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                            LoRa.TX_PACKET_EVENT |
                            LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

    
   
    #while(True):
    #    data, port = lora_socket.recvfrom(128)
    #    if data:
    #        print('data read')


def prepare_channels(lora, channel, data_rate):
    if not channel in range(1, 9):
        raise RuntimeError("channels should be in 1-8 for AS923")

    for i in range(0, 8):
        lora.remove_channel(i)

    upstream = (item for item in AS923_FREQUENCIES if item["chan"] == channel).__next__()

    # set default channels frequency
    lora.add_channel(int(upstream.get('chan')), frequency=int(upstream.get('fq')), dr_min=0, dr_max=data_rate)

    from lora_regions import human_fq

    print("Adding channel up %s %s" % (upstream.get('chan'), human_fq(upstream.get('fq'))))


def lora_otaa_join(lora):
    # create an OTA authentication params
    dev_eui = binascii.unhexlify('AD A4 DA E3 AC 12 67 6B'.replace(' ',''))
    app_key = binascii.unhexlify(settings.dic['lora_OTAA_key'])

    start_join_time = time.time()

    # lora.nvram_restore()

    if not lora.has_joined():
        print('Join procedure started...')
        lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_key), timeout=0, dr=2)


    # wait until the module has joined the network
    while not lora.has_joined():
        time.sleep(1)
        pycom.rgbled(0x000000)
        print('.', end='')
        time.sleep(1)
        pycom.rgbled(0x0000ff)

    lora.nvram_save()

    end_join_time = time.time()
    duration = (end_join_time - start_join_time)
    if duration > 0:
        print("")
        print("OTAA took %s secs." % duration)
    pycom.rgbled(0x00ff00)

def proto_handler_multi(data, port):
	i=0
	#print('handle data',binascii.hexlify(data))
	print('Received: {}, on port: {}'.format(data, port))
	while(True):
		try:
			n = i+data[i+1]+3
			msg = data[i:n]
			i=n
		except IndexError: 
			break
		proto_handler(msg)

def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        print('Lora packet received')
    if events & LoRa.TX_PACKET_EVENT:
        print('Lora packet sent')
