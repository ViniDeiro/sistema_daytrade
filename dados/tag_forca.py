"""Marca no forward_log.json a "força da sequência" (movimento da sequência / ATR14) dos sinais antigos, usando as velas salvas. Uso: python3 dados/tag_forca.py"""
import json
MIN=60000;LIM=4.9
d={}
for f in ('dados/candles.json','dados/IDXUSDT_candles.json'):
    for c in json.load(open(f)):d[c['t']]=c
raw=json.load(open('dados/forward_log.json'));tr=raw['trades'] if isinstance(raw,dict) else raw
n=ok=0
for t in tr:
    if t.get('forca') is not None:continue
    s=t['sigT'];c=d.get(s);st=d.get(s-(t['run']-1)*MIN)
    cs=[d.get(s-k*MIN) for k in range(14)]
    if not c or not st or any(x is None for x in cs):continue
    atr=sum(x['h']-x['l'] for x in cs)/14
    if atr<=0:continue
    t['forca']=round(abs(c['c']-st['o'])/atr,2);t['forte']=t['forca']>=LIM;ok+=1
n=len(tr);print(f"marcados: {ok} de {n}; fortes: {sum(1 for t in tr if t.get('forte'))}; sem dado de vela: {sum(1 for t in tr if t.get('forca') is None)}")
json.dump(raw,open('dados/forward_log.json','w'),indent=1)
