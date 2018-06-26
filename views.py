from django.http import HttpResponse
from django.shortcuts import render
import redis
import time
import threading
from datetime import datetime
import logging

r = redis.StrictRedis(host='localhost', port=6379, charset="utf-8", decode_responses=True, db=0)

class PreviaVotacao(threading.Thread):

    candidatos = {
        'A': {'nome':'Candidato A', 'votos':0, 'percentual':0.0},
        'B': {'nome':'Candidato B', 'votos':0, 'percentual':0.0},
        'C': {'nome':'Candidato C', 'votos':0, 'percentual':0.0}}

    total = 0
    atualizado_em = datetime.now()

    def __init__(self):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = 5.0
    
    def setInterval(self, interval):
        """Set the number of seconds we sleep between executing our task"""
        self._interval = interval

    def getTotal(self):
        return self.total

    def getCandidatos(self):
        return self.candidatos

    def getAtualizadoEm(self):
        return self.atualizado_em

    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
            if self._finished.isSet(): return
            self.task()
            
            # sleep for interval or until shutdown
            self._finished.wait(self._interval)

    def task(self):
        
        print("Recalculando estatísticas da prévia...")
        startTime = time.time()

        totalTemp = 0

        for k in self.candidatos.keys():
            self.candidatos[k]['votos'] = 0
            
        for k in r.scan_iter():
            voto = r.get(k)
            if(voto):
                self.candidatos[voto]['votos'] += 1
                totalTemp += 1
            
        for k in self.candidatos.keys():
            self.candidatos[k]['percentual'] = self.candidatos[k]['votos']/totalTemp*100

        self.total = totalTemp
        self.atualizado_em = datetime.now()
        elapsedTime = time.time() - startTime
        print("Prévia atualizada em ", int(elapsedTime*1000), "ms.")
        pass

calcula_previa = PreviaVotacao()
calcula_previa.start()

def index(request):  
    msg = ""
    previa = False

    if request.method == "GET":
        voto = request.GET.get("voto", "")
        if (voto == ""):
            msg="Escolha um candidato."
        else:            
            r.set(time.time(), voto)
            msg="Seu voto foi registrado."
            print("Registrando voto:",voto)            
            previa = True
    
    return render(request, 'votacaoweb/index.html', {'msg':msg,'candidatos':calcula_previa.candidatos, 'previa':previa, 'atualizado_em':calcula_previa.atualizado_em})

def previa(request):      
    return render(request, 'votacaoweb/previa.html', {
        'candidatos':calcula_previa.candidatos,        
        'atualizado_em':calcula_previa.atualizado_em,
        'qtd_votos':calcula_previa.total
    })


