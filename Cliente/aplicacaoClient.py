#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código!

from enlace import *
import time
import numpy as np
from math import ceil
from crccheck.crc import Crc16
from timer_error import *
from datetime import datetime



# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM7"                  # Windows(variacao de)

#Segmenta o conteúdo em payloads de 50 bytes
def setPayload(content):
    counter = 0
    size = len(content)
    packages = ceil(size/50)
    payloads = []
    for package in range(packages):
        if package == packages-1:
            payload = content[package*50:size]
            print(f'tamanho do último payload:{len(payload)} | payload_id:{counter}')
        else:
            payload = content[package*50:(package+1)*50]
            print(f'tamanho dos payloads intermediários:{len(payload)}')
        payloads.append(payload)
    return payloads,size

def verifica_eop(head, pacote):
    tamanho = head[2]
    eop = pacote[12+tamanho:]
    if eop == b'\xAA\xBB\xCC\xDD':
        return True
    else:
        print('Payload não recebido corretamente')
        return False

def monta_pacotes(tipo,servidor,total_pacotes,pacote_atual,variavel,restart,last_package,payload,handshake=False):
    if handshake == False:
        crc = Crc16().calc(payload)
        crc = int.to_bytes(crc, 2, byteorder='big')
        crc1 = crc[0]
        crc2 = crc[1]
        CRC = crc1+crc2
    else:
        crc1 = 0
        crc2 = 0
        CRC = 0
    #HEAD
    HEAD = bytes([tipo,servidor,0,total_pacotes,pacote_atual,variavel,restart,last_package,crc1,crc2])
    #PAYLOAD

    PAYLOAD = payload
    #EOP
    EOP =b'\xAA\xBB\xCC\xDD'
    #Junta os componentes do Pacote
    if tipo==1:
        print(crc1,crc2,CRC)
        return np.asarray(HEAD + EOP),bytes([crc1,crc2])
    else:
        return np.asarray(HEAD + PAYLOAD + EOP),bytes([crc1,crc2])

def log(operation:str, type:int, size:int, cont:int=None, pckg_total:int=None, crc_check:int=None):
    file = 'Client.txt'
    if not pckg_total:
        pckg_total = ''
    if not cont:
        cont = ''

    with open(f'{file}', 'a') as f:
        conteudo = f'{datetime.now()} /{operation}/Tipo:{type}/Tamanho:{size}/Num_pacote:{cont}/TotalPacotes:{pckg_total}/crc_check:{crc_check} \n'
        f.write(conteudo)



def main():
    try:
        print("Iniciou o main")
        com1 = enlace(serialName)
        # Ativa comunicacao. Inicia os threads e a comunicação seiral
        com1.enable()
        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print("Abriu a comunicação")

        # #Enviando bit de sacrifício
        # com1.sendData(b'00')
        # time.sleep(0.1)


        print("------------------------PREPARANDO-------------------------------")
        print("vai começar a preparação do pacote")

        # Carrega imagem
        print("Carregando pacote para transmissão:")
        '''
        PACOTES DA MENSAGEM
        ●HEAD
            ● h0 - Tipo de mensagem.
            ● h1 - Se tipo for 1: número do servidor. Qualquer outro tipo: livre
            ● h2 - Livre.
            ● h3 - Número total de pacotes do arquivo.
            ● h4 - Número do pacote sendo enviado.
            ● h5 - Se tipo for handshake: id do arquivo (crie um para cada arquivo). Se tipo for dados: tamanho do payload.(variavel)
            ● h6 - Pacote solicitado para recomeço quando a erro no envio.
            ● h7 - Ùltimo pacote recebido com sucesso.
            ● h8 - h9 - CRC (Por ora deixe em branco. Fará parte do projeto 5).
        ● PAYLOAD - variável entre 0 e 114 bytes. Reservado à transmissão dos arquivos.
        ● EOP - 4 bytes: 0xAA 0xBB 0xCC 0xDD.
        '''
        #HEAD
        #PAYLOAD
        img = 'img\picasso.png'
        img_r = open(img, 'rb').read()
        lista_payload, size = setPayload(img_r) # Lista de payloads da imagem divida
        print(f'Tamanho da imagem: {size} bytes')

        #FALTA CRCs
        #Pacote de Handshake
        handshake,_ = monta_pacotes(1,3,len(lista_payload),0,size,0,0,0,handshake=True)


        print("------------------------HANDSHAKE-------------------------------")
        inicia = False
        print("vai começar o handshake")
        #Enviando Handshake ele devera enviar um bit 1 e receber um bit 2
        com1.sendData(handshake)
        time.sleep(0.1)
        print("Handshake enviado")

        startime = time.time() #Inicia a contagem do tempo de transmissão
        #Aguardando Feedback Handshake
        inicia = False
        while inicia == False:
            if com1.rx.getIsEmpty() == True:
                print("Aguardando resposta do servidor")
                if time.time() - startime > 5:
                    print("Tempo de espera excedido")
                    resposta_imp = str(input("Servidor inativo. Tentar novamente (S/N)?  "))
                    if (resposta_imp == 'S') or (resposta_imp == 's'):
                        inicia = False
                        # Enviando bit de sacrifício
                        # com1.sendData(b'00')
                        # time.sleep(0.1)

                        com1.sendData(handshake)
                        log('Handshake Client',1,len(handshake))
                        time.sleep(0.1)
                        print("Handshake enviado")
                        startime = time.time()
                    else:
                        print("-------------------------")
                        print("Comunicação encerrada")
                        print("-------------------------")
                        com1.disable(); return


            else:
                tipo_rx, nRx = com1.getData(10)
                log('Handshake Server',2,10)
                print("tipo_rx: ", tipo_rx)
                time.sleep(0.1)
                #Verifica se o bit recebido é o de confirmação
                if tipo_rx[0] == 2:
                    alive = True
                    print("Servidor ativo")
                    alive= True
                    break

                else:
                    alive = False

        print("------------------------TRANSMISSÃO-------------------------------")

        print("vai começar a transmissão dos pacotes")
        cont = 1
        numPck = len(lista_payload)
        check = False
        check_aux = 0
        while cont<=len(lista_payload):
            print(cont)
            try:
                payload = lista_payload[cont-1]
                payload_size = len(payload)
                #Enivando pacotes
                package,CRC = monta_pacotes(3,3,numPck,cont,payload_size,0,cont-1,payload)
                # crc_check = crc1+crc2

                # Enviando pkcg cont - msg t3
                com1.sendData(package)
                print('{}/{} | {}\n{}'.format(cont,numPck,payload,package))
                log('Pacote enviado',3,14+payload_size,cont,numPck,CRC)

                #Set timer reenvio
                set_timer1 = time.time()

                #Set o timer de timeout
                if check == False and check_aux == 0:
                    set_timer2 = time.time()
                    check_aux = 1


                #Verificando se o pacote recebido é o correto--------------------------------------
                com1.rx.clearBuffer()
                #Pega Feedback do servidor
                feedback_server, _ = com1.getDataT(14,set_timer1,set_timer2)
                time.sleep(0.1)
                feedback_server_type = feedback_server[0]
                log('Feedback Server',feedback_server_type,14)
                feedback_server_package = feedback_server[6]
                print(f'\nFEEDBACK SERVIDOR: {feedback_server}\n')
                    #Verifica se o pacote recebido é o correto
                if feedback_server_type == 4:
                    print('Pacote {} recebido com sucesso'.format(cont))
                    cont += 1
                    check = False
                elif feedback_server_type == 6:
                    print('Pacote {} não foi recebido com sucesso.'.format(cont))
                    cont = feedback_server_package+1
                    com1.rx.clearBuffer()
                    check = False
                print('---------------------------------------------------------------')

            #Checa se o tempo de reenvio foi excedido
            except Timer1Error:
                check = False

            #Checa se o tempo de timeout foi excedido
            except Timer2Error:
                print('Time out, servidor inativo.')
                pckt_timeout,_ = monta_pacotes(5,3,numPck,1,payload_size,0,cont-1,payload)
                com1.sendData(pckt_timeout)
                log('Timeout Enviado',5,14+payload_size)
                time.sleep(0.1)
                # Encerra comunicação
                print("-------------------------")
                print("Comunicação encerrada")
                print("-------------------------")
                com1.disable(); return

        print("-----------------------FIM DA TRANSMISSÃO-------------------------")

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()

    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()


    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()