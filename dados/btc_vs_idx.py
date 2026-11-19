"""BTC (público, 1 ano) vs IDX (Ebinex, 90 dias): mesma regra, mesmos períodos. Offline."""
import json
from datetime import datetime
MIN=60_000; BE=1/1.96
def load(f,fmt):
    raw=json.load(open(f))
    if fmt=='ebinex': return {c['t']:[c['o'],c['c']] for c in raw}
    return {int(k):v for k,v in raw.items()}
btc=load('dados/binance_BTCUSDT_1ano.json','b'); idx=load('dados/candles.json','ebinex')
def events(d):
    col=lambda t:(d[t][1]>d[t][0])-(d[t][1]<d[t][0]); out=[]
    for t in sorted(d):
        if t-MIN not in d: continue
        c=col(t-MIN)
        if c==0: continue
        s=1
        while (t-(s+1)*MIN) in d and col(t-(s+1)*MIN)==c: s+=1
        if s>=4: out.append((t, col(t)==c, col(t)==-c, col(t)==0))
    return out
eb,ei=events(btc),events(idx)
t0=min(idx); t1=max(idx); P=(t1-t0)/3
def rate(ev,a,b):
    r=[e for e in ev if a<=e[0]<b]; n=len(r); return 100*sum(e[1] for e in r)/n, 100*sum(e[2] for e in r)/n, 100*sum(e[3] for e in r)/n, n
print("Regra >=4 velas iguais. 'repete' = continuação (a nossa regra); 'reverte' = apostar o contrário. Doji = perda nos dois.\n")
print(f"{'período':<16}{'IDX repete':>11}{'BTC repete':>11}{'diferença':>10} | {'BTC reverte':>11}{'doji BTC':>9}")
diffs=[]
for i in range(3):
    a,b=t0+P*i,t0+P*(i+1) if i<2 else t1+MIN
    ri=rate(ei,a,b); rb=rate(eb,a,b); diffs.append(ri[0]-rb[0])
    print(f"{datetime.fromtimestamp(a/1000):%d/%m}-{datetime.fromtimestamp(b/1000):%d/%m}   {ri[0]:>9.2f}% {rb[0]:>9.2f}% {ri[0]-rb[0]:>+9.2f} | {rb[1]:>10.2f}% {rb[2]:>8.2f}%")
yr=rate(eb,min(btc),max(btc)+1); avg=sum(diffs)/3
print(f"\nBTC no ANO INTEIRO: repete {yr[0]:.2f}% | reverte {yr[1]:.2f}% (equilíbrio {100*BE:.2f}%) | n={yr[3]}")
print(f"Prêmio médio do IDX sobre o BTC nos 90 dias: {avg:+.2f} pontos")
for prem in (avg, avg-1, avg-2):
    h=yr[0]+prem; print(f"  se esse prêmio valesse para o ano todo (prêmio {prem:+.2f}): IDX teria acertado ~{h:.2f}% -> ROI por entrada {100*(h/100*1.96-1):+.1f}%")
# BTC por trimestre para ver a deriva
print("\nBTC repete (>=4), por trimestre móvel de 90 dias:")
T=min(btc); step=90*24*3600_000
a=T
while a+step<=max(btc)+1:
    r=rate(eb,a,a+step); print(f"  {datetime.fromtimestamp(a/1000):%d/%m/%Y}-{datetime.fromtimestamp((a+step)/1000):%d/%m/%Y}: {r[0]:.2f}% (n={r[3]})"); a+=step
