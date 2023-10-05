    #####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
import time
import numpy as np
from datetime import datetime

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)


####      FUNÇÕES AUXILIARES      ####
def atualiza_tempo(tempo_referencia):
    tempo_atual = time.time()
    ref = tempo_atual - tempo_referencia
    return ref

def verifica_handshake(handshake_client): # Função para verificar se o handshake está correto
    handshake = handshake_client[:2] #Pega os dois primeiros bytes do head
    delta_tempo = 0

    combinado = bytes([9, 1])
    if not False:
        combinado = bytes([8,0])
    while delta_tempo <= 5:
        tempo_atual = time.time()
        if handshake == combinado: 
            print('Handshake realizado com sucesso')
            return True
        delta_tempo = atualiza_tempo(tempo_atual)
    return False

def verifica_eop(head, pacote): # Função para verificar se o payload está correto
    tamanho = head[2] # Tamanho = 3º byte do head = 0
    eop = pacote[12+tamanho:]
    if eop == b'\x03\x02\x01':
        print('Payload recebido com sucesso, esperando próximo pacote')
        return True
    else:
        print('Payload não recebido corretamente')
        return False

def trata_pacote(pacote):
    tamanho_pacote = len(pacote)
    head = pacote[:12]
    tamanho = head[2]
    payload = pacote[12:-3]
    eop = pacote[12+tamanho:]

    return head, payload, eop



    
####                FIM DAS FUNÇÕES               ####
####               Tipos de mensagens             ####
# Chamado do cliente para o servidor 
TIPO1 = 1
# Resposta do servidor para o cliente
TIPO2 = 2
# Mensagem contendo o tipo de dados
TIPO3 = 3
# Mensagem enviada ao servidor relatando que a mensagem do tipo 3 foi recebida e averiguada
TIPO4 = 4
# Mensagem de time out, toda vez que o limite de espera exceder, esta mensagem será enviada (tanto cliewnte quanto servidor)
TIPO5 = 5
# Mensagem de erro, servidor envia para o cliente quando ocorre algum erro na mensagem tipo 3 - orienta cliente a enviar novamente
TIPO6 = 6
####                FIM DOS TIPOS DE MENSAGENS    ####

serialName = "COM5"                  # Windows(variacao de)
EOP = b'\xAA\xBB\xCC\xDD'

def main():
    try:
        com1 = enlace(serialName) 
        com1.enable()

        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print("----COMUNICAÇÃO ABERTA COM SUCESSO----\n")
        print("------------RECEPÇÃO VAI COMEÇAR---------\n")

        ocioso = True
        
        while ocioso:
            head_client, _ = com1.getData(10)
            end_of_package,_ = com1.getData(4)
            total_pacotes = head_client[3]

            #handshake 
            if head_client[0] == 1 and end_of_package == EOP:
                print("handshake recebido")
                if head_client[1] == 1:
                    ocioso = False
                    print("É para mim")
                    time.sleep(.1)

                    #resposta do handshake
                if ocioso == False:
                    head_server = bytes([2,0,0,0,0,0,0,0,0,0])
                    server_handshake = np.asarray(head_server + EOP)
                    com1.sendData(server_handshake)
                    print("resposta t2 enviada")
                    cont = 1
                else:
                    print("Não é para mim")
                    time.sleep(.1)
            else:
                print("Handshake incorreto")
        sucesso = True 
        cont = 1
        string = b''
        nump = 0
        pacote_recebido_certo = b'\x01'
        resposta = b'\x02\x00\x00' + bytes([total_pacotes]) +  b'\x00\x11\x00\x00\x00\x00' + EOP
        while cont <= total_pacotes:
            time.sleep(.1)
            timer1 = time.time()
            timer2 = time.time()
            while sucesso:
                agora = time.time()
                conteudo = com1.rx.getIsEmpty()
                if conteudo == False:
                    head_client, _ = com1.getData(10)
                    tamanho = head_client[5]
                    tipo = head_client[0]
                    numero = head_client[4]
                    if tipo == 3:
                        payload_cliente, _ = com1.getData(tamanho)
                        string += payload_cliente
                        #verifica o numero do pacote
                        if cont == numero:
                            print("numero do pacote esperado certo")
                            payload_cliente, _ = com1.getData(tamanho)
                            print('peguei payload')

                            string += payload_cliente
                            eop, nEop = com1.getData(4)
                            arquivo = open('Server1.txt', 'a')
                            arquivo.write("'{}' / receb / 3 / '{}'\n".format(datetime.now(), tamanho+14))
                            arquivo.close()

                            #verifica eop
                            if eop == EOP:
                                print("eop correto")
                                cont += 1
                                com1.sendData(b'\x04\x00\x00\x00\x00\x00\x00' + pacote_recebido_certo + b'\x00\x00\xAA\xBB\xCC\xDD')
                                arquivo = open('Server1.txt', 'a')
                                arquivo.write("'{}' / envio / 4 / '{}' / '{}' / '{}'\n".format(datetime.now(), resposta[5]+14, resposta[4],resposta[3]))
                                arquivo.close()
                                pacote_recebido_certo = bytes([numero])
                            else:
                                print("eop incorreto")
                                pacote_recebido_errado = cont
                                com1.sendData(b'\x04\x00\x00\x00\x00\x00\x00' + pacote_recebido_errado + b'\x00\x00\xAA\xBB\xCC\xDD')
                                arquivo = open('Server2.txt', 'a')
                                arquivo.write("'{}' / envio / 6 / '{}' / '{}' / '{}'\n".format(datetime.now(), resposta[5]+14, resposta[4],resposta[3]))
                                arquivo.close()
                        else:
                            print("numero do pacote esperado errado")
                            pacote_recebido_errado = cont
                            com1.sendData(b'\x04\x00\x00\x00\x00\x00\x00' + bytes([pacote_recebido_errado]) + b'\x00\x00\xAA\xBB\xCC\xDD')
                            arquivo = open('Server1.txt', 'a')
                            arquivo.write("'{}' / envio / 6 / '{}' / '{}' / '{}'\n".format(datetime.now(), resposta[5]+14, resposta[4],resposta[3]))
                            arquivo.close()
                    elif agora-timer2 > 20:
                        ocioso = True
                        com1.sendData(b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\xAA\xBB\xCC\xDD')
                        arquivo = open('Server1.txt', 'a')
                        arquivo.write("'{}' / envio / 5 / '{}' / '{}' / '{}'\n".format(datetime.now(), resposta[5]+14, resposta[4],resposta[3]))
                        arquivo.close()
                        print("Time out")
                        print("Encerra")
                        com1.disable()
                        print("-------------------------")
                        print("Comunicação encerrada")
                        print("-------------------------")
                        break
                    elif agora-timer1 > 2:
                        com1.sendData(b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xAA\xBB\xCC\xDD')
                        arquivo = open('Server1.txt', 'a')
                        arquivo.write("'{}' / envio / 4 / '{}' / '{}' / '{}'\n".format(datetime.now(), resposta[5]+14, resposta[4],zresposta[3]))
                        arquivo.close()
                        timer1 = time.time()

        print("chegou")
        imageW = 'crawfinal.png'

        f = open(imageW, 'wb')
        f.write(string)
        f.close()
        
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()

            ##########################
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()