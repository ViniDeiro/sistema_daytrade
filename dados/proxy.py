"""Baixa 1 mês de velas M1 PÚBLICAS (Binance) de BTC/ETH/SOL e roda o mesmo teste de continuação. Não usa a Ebinex."""
import json, math, urllib.request, time, os
MIN=60_000
idx=sorted(json.load(open('dados/candles.json')),key=lambda x:x['t']); T0,T1=idx[0]['t'],idx[-1]['t']
def fetch(sym):
    f=f'dados/binance_{sym}_1mes.json'
    if os.path.exists(f): return json.load(open(f))
    out={}; t=T0
    while t<=T1:
        u=f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1m&limit=1000&startTime={t}"
        k=json.load(urllib.request.urlopen(u,timeout=20))
        if not k: break
        for x in k: out[int(x[0])]=[float(x[1]),float(x[4])]
        t=int(k[-1][0])+MIN; time.sleep(0.15)
    json.dump(out,open(f,'w')); return out
def study(name,data):
    ts=sorted(int(t) for t in data); d={int(k):v for k,v in data.items()}
    col=lambda t:(d[t][1]>d[t][0])-(d[t][1]<d[t][0])        # 1 verde, -1 vermelha, 0 doji
    res={}
    for t in ts:
        if t-MIN not in d: continue
        c=col(t-MIN)
        if c==0: continue
        s=1
        while (t-(s+1)*MIN) in d and col(t-(s+1)*MIN)==c: s+=1
        res.setdefault(min(s,7),[0,0]); res[min(s,7)][0]+= col(t)==c; res[min(s,7)][1]+=1
    line=" | ".join(f"s={k}: {100*h/n:.1f}% ({n})" for k,(h,n) in sorted(res.items()))
    n4=sum(res[k][1] for k in res if k>=4); h4=sum(res[k][0] for k in res if k>=4)
    print(f"{name}: {len(ts)} velas\n   {line}\n   >=4 iguais: {100*h4/n4:.2f}% em {n4} entradas (equilíbrio 51,02%)")
study("IDX (Ebinex)",{t['t']:[t['o'],t['c']] for t in idx})
for s in ("BTCUSDT","ETHUSDT","SOLUSDT"): study(s,fetch(s))
