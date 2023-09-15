#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 

from enlace import *
import time
import numpy as np
from math import ceil

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
    if eop == b'\x03\x02\x01':
        return True
    else:
        print('Payload não recebido corretamente')
        return False

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
        ● HEAD - 12 BYTES - fixo
            ● TYPE - 1 BYTE - fixo
            ● HANDSHAKE/RESPONSE - 1 BYTE - fixo
            ● PAYLOAD SIZE - 1 BYTE - fixo
            ● ID - 1 BYTES - fixo
            ● QTD PACOTES - 1 BYTES - fixo
            ● STATUS - 1 BYTES - fixo (1=OK, 0=ERROR)  
            ● EMPTY(5-12) BYTES - fixo
        ● PAYLOAD - variável entre 0 e 50 BYTES (pode variar de pacote para pacote)
        ● EOP - 3 BYTES - fixo (valores de sua livre escolha)
            ● 0x03 
            ● 0x02
            ● 0x01
        '''
        #HEAD
        #PAYLOAD
        img = 'img\picasso.png'
        img_r = open(img, 'rb').read()
        lista_payload, size = setPayload(img_r) # Lista de payloads da imagem divida
        print(f'Tamanho da imagem: {size} bytes')
        #EOP
        EOP = bytes([3,2,1])

        #Pacote de Handshake
        handshake = np.asarray(bytes([8,0,0,0,len(lista_payload),0,0,0,0,0,0,0])+EOP)

        print("------------------------HANDSHAKE-------------------------------")
        print("vai começar o handshake")
        #Enviando Handshake ele devera enviar um bit 1 e receber um bit 2
        com1.sendData(handshake)
        time.sleep(0.1)
        print("Handshake enviado")

        startime = time.time() #Inicia a contagem do tempo de transmissão
        #Aguardando Feedback Handshake
        alive = False
        while alive == False:
            if com1.rx.getIsEmpty() == True:
                print("Aguardando resposta do servidor")
                if time.time() - startime > 5:
                    print("Tempo de espera excedido")
                    resposta_imp = str(input("Servidor inativo. Tentar novamente (S/N)?  "))
                    if (resposta_imp == 'S') or (resposta_imp == 's'):
                        alive = False
                        # Enviando bit de sacrifício
                        # com1.sendData(b'00') 
                        # time.sleep(0.1)

                        com1.sendData(handshake)
                        time.sleep(0.1)
                        print("Handshake enviado")
                        startime = time.time()
                    else:
                        print("-------------------------")
                        print("Comunicação encerrada")
                        print("-------------------------")
                        com1.disable(); return
                        

            else:
                rx, nRx = com1.getData(15)
                time.sleep(0.1)
                #Verifica se o bit recebido é o de confirmação
                if rx[:2] == bytes([8,1]):
                    alive = True
                    print("Servidor ativo")
                    alive= True
                    break

                else:
                    alive = False


        
        print("------------------------TRANSMISSÃO-------------------------------")

        print("vai começar a transmissão dos pacotes")
        cur_package = 0
        
        for payload in lista_payload:
            #Enivando pacotes
            head_client = bytes([8,0,len(payload)+cur_package, cur_package, len(lista_payload),0,0,0,0,0,0,0])
            package = np.asarray(head_client + payload + EOP)
            com1.sendData(package)
            print('{}/{} | {}'.format(cur_package,len(lista_payload),payload))


            #Verificando se o pacote recebido é o correto
            com1.rx.clearBuffer()
            feedback_server, _ = com1.getData(1)

            time.sleep(0.1)
            if feedback_server == bytes([1]):
                print(f'^----Tamanho do payload INCORRETO {cur_package}, reenviando o pacote.\n')
                com1.sendData(package)
                time.sleep(0.1)
                #com1.disable(); return
            if feedback_server == bytes([2]):
                print(f'^----Pacote {cur_package} enviado com SUCESSO. \n')

            com1.rx.clearBuffer()
            time.sleep(0.1)
            cur_package += 1

        head_server, _ = com1.getData(12) # Recebendo o head do servidor
        is_trasmission_ok = (head_server[4] == 1)
        eop_server, _ = com1.getData(3) # Recebendo o EOP do servidor
        package_server = head_server + eop_server
        is_eop_ok = verifica_eop(head_server, package_server)

        # Condições para encerrar a conexão
        if not is_trasmission_ok:
            print('Erro no envio de pacotes. Encerrando conexão.')

        if size == head_server[2]:
            print('Tamanho da imagem recebida é igual ao tamanho da imagem enviada {}|{}.'.format(size, head_server[2]))
        if is_trasmission_ok and is_eop_ok:
            print('Transmissão finalizada com sucesso.')

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