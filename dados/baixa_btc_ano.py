"""Baixa 1 ano de velas M1 PÚBLICAS do BTCUSDT (Binance). Não usa a Ebinex. Retoma de onde parou."""
import json, urllib.request, time, os, sys
MIN=60_000; sym=sys.argv[1] if len(sys.argv)>1 else 'BTCUSDT'
idx=sorted(json.load(open('dados/candles.json')),key=lambda x:x['t']); T1=idx[-1]['t']
START=T1-365*24*3600_000
f=f'dados/binance_{sym}_1ano.json'
out={int(k):v for k,v in json.load(open(f)).items()} if os.path.exists(f) else {}
t=max(out)+MIN if out else START; n=0
while t<=T1:
    u=f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1m&limit=1000&startTime={t}&endTime={T1}"
    try: k=json.load(urllib.request.urlopen(u,timeout=30))
    except Exception as e: print("erro",e); time.sleep(5); continue
    if not k: break
    for x in k: out[int(x[0])]=[float(x[1]),float(x[4])]
    t=int(k[-1][0])+MIN; n+=1
    if n%50==0: json.dump(out,open(f,'w')); print(n,"requisições,",len(out),"velas",flush=True)
    time.sleep(0.12)
json.dump(out,open(f,'w')); print("FIM:",len(out),"velas, de",min(out),"até",max(out),flush=True)
