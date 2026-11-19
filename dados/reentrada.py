"""Offline: depois de entrar na 5ª vela, continua entrando? Compara 3 jeitos de contar, 1 ano de IDX."""
import numpy as np
exec(open('dados/estudo10.py').read().split("if __name__")[0])
I=prep('idx'); t=I['t']
import json
raw=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t'])
col=np.sign(np.array([c['c'] for c in raw])-np.array([c['o'] for c in raw])).astype(int)
n=len(col); contig=np.zeros(n,bool); contig[1:]=(t[1:]-t[:-1])==60_000
run=np.zeros(n,int)
for i in range(1,n): run[i]=(run[i-1]+1 if (col[i]!=0 and contig[i] and col[i]==col[i-1]) else (1 if col[i]!=0 else 0))
pr=np.zeros(n,int); pr[1:]=run[:-1]                 # velas iguais seguidas ANTES da vela de entrada
idx=np.arange(n); hit=(col==col[idx-1])&contig&(col[idx-1]!=0)
day=(I['hour']>=8)&(I['hour']<22)
def row(label,mask,mk):
    for nome,m in (("24h",mk),("08-22h",mk&day)):
        k=int(hit[m].sum()); N=int(m.sum()); u=k*0.96-(N-k)
        print(f"  {label:<44}{nome:>7}: {100*k/N:.2f}% em {N:>6} entradas ({N/365:.0f}/dia) | $20 fixo: {20*u:>+9,.0f}")
print("Quando a sequência de velas iguais ANTES da entrada é...")
row("A) exatamente 4 (entra só na 5ª, uma vez por sequência)",None,(pr==4))
row("B) 4 ou mais (continua entrando a cada vela)",None,(pr>=4))
row("C) 4, 8, 12... (espera mais 4 iguais para reentrar)",None,(pr>=4)&(pr%4==0))
print("\nAcerto por tamanho da sequência antes da entrada (24h): ",end="")
for s in range(4,11): 
    m=(pr==s); print(f"{s}: {100*hit[m].mean():.1f}% ({int(m.sum())})",end=" | ")
print()
