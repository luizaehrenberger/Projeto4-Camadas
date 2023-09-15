#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
#Carareto
#17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo
import time

# Threads
import threading

# Class
class TX(object):
 
    def __init__(self, fisica):
        self.fisica      = fisica
        self.buffer      = bytes(bytearray())
        self.transLen    = 0
        self.empty       = True
        self.threadMutex = False
        self.threadStop  = False


    def thread(self):
        while not self.threadStop:
            if(self.threadMutex):
                self.transLen    = self.fisica.write(self.buffer)
                self.threadMutex = False

    def threadStart(self):
        self.thread = threading.Thread(target=self.thread, args=())
        self.thread.start()

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def sendBuffer(self, data):
        self.transLen   = 0
        self.buffer = data
        self.threadMutex  = True

    def getBufferLen(self):
        return(len(self.buffer))

    def getStatus(self):
        '''
        Esse método retorna o status atual da transmissão de dados
        O método verifica se o valor do atributo transLen é igual ao tamanho do buffer de dados armazenado
        no atributoo buffer. Se for o metodo retorna o valor True, indicando que a transmissão foi concluida com sucesso.
        Caso contrário o metodo retorna False, indicando que a transmissão ainda não foi concluida.
        '''
        return(self.transLen)
        

    def getIsBussy(self):
        return(self.threadMutex)

