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

serialName = "COM5"                  # Windows(variacao de)
EOP = bytes([3,2,1]) 

def main():
    try:
        #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
        #para declarar esse objeto é o nome da porta.
        com1 = enlace(serialName)
        # Ativa comunicacao. Inicia os threads e a comunicação seiral 
        com1.enable()

        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print("----COMUNICAÇÃO ABERTA COM SUCESSO----\n")
       
        print("------------RECEPÇÃO VAI COMEÇAR---------\n")

        # Recebendo a quantidade de comandos que será enviado
        fez_handshake = False
        handshake_client, t = com1.getData(12)
        pacotes = handshake_client[4]
        time.sleep(.5)
        print(handshake_client)

        #verificando o handshake do client
        if fez_handshake == False:
            if verifica_handshake(handshake_client):
                tamanho_payload = int(handshake_client[2])
                resto_handshake_client, _ = com1.getData(tamanho_payload+3)
                time.sleep(.1)
                handshake = handshake_client + resto_handshake_client
                if not verifica_eop(handshake_client, handshake):
                    return
                else:
                    handshake_server = np.asarray(bytes([8,1,0,0,0,0,0,0,0,0,0,0])+EOP)
                    print(handshake_server)
                    com1.sendData(handshake_server)
                    time.sleep(.1)
                    print("Handshake do servidor enviado ao client\n")
                    fez_handshake = True

        pacotes_antes = 1
        pacotes_recebidos = 0

        payloads_totais=b''

        while True:
            head, rxHeaderLen = com1.getData(12)
            time.sleep(.1)

            tamanho_payload = head[2]
            pacote_atual = head[3]
            total_pacotes = head[4]

            #tamanho_payload+=1
            if pacote_atual != pacotes_antes: 
                print("Pacote fora de ordem")
                com1.sendData(bytes([1,0,0,0,0,0,0,0,0,0,0,0]) + EOP)
                com1.disable(); return
            com1.sendData(bytes([2,0,0,0,0,0,0,0,0,0,0,0]) + EOP)
            time.sleep(.1)
        
            pacotes_recebidos += 1
            pacotes_antes = pacote_atual

            resto_pacote, _ = com1.getData(tamanho_payload+3)
            time.sleep(.1)
            
            pacote_cliente = head + resto_pacote
            #segmentando pacote
            head_cliente, payload_cliente, eop_cliente = trata_pacote(pacote_cliente)
            payloads_totais+=payload_cliente
    
            #verificando o eop 
            if not verifica_eop(head_cliente, pacote_cliente):
                print("EOP não recebido corretamente")
                com1.disable(); return
            if pacotes_recebidos == pacotes:
                print("Recepção finalizada")
                break
            if pacotes_recebidos != pacotes:
                pacotes_antes += 1

        bt = bytes([1,0,len(payloads_totais),0,0,0,0,0,0,0,0,0])    
        if pacotes_recebidos != pacotes:
            print("Pacotes recebidos diferente do total de pacotes")
        else:
            print("Transmissão finalizada com sucesso")
            bt = bytes([1,0,len(payloads_totais),0,1,0,0,0,0,0,0,0])

        com1.sendData(bt + EOP) 
        time.sleep(.5)

        print('')
        print(len(payloads_totais))
        print('')

        img_recebida_nome = 'img\img_recebida.png'
        f = open(img_recebida_nome,'wb')
        f.write(payloads_totais)
        f.close()

        com1.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()
        

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()