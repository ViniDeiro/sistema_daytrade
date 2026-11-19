"""Compara 3 regras de entrada sobre o forward_log (paper): primeira (run=4), duas primeiras (run<=5) e todas. Uso: python3 -I dados/variantes.py"""
import json, datetime, math
BE = 1/1.96
f = json.load(open('dados/forward_log.json')); f = f if isinstance(f, list) else f['trades']
base = json.load(open('dados/baseline.json')); desde = base.get('t', 0)
fech = [t for t in f if t.get('status') == 'fechado']
dia = lambda t: datetime.datetime.fromtimestamp(t['entryT']/1000).strftime('%Y-%m-%d')
def linha(nome, L):
    emp = sum(1 for t in L if t.get('empate')); w = sum(1 for t in L if t.get('win')); n = len(L) - emp
    p = sum(t.get('pnl', 0) for t in L); r = w/n if n else 0
    print(f"  {nome:<10}{len(L):>5} entradas {w:>4} wins  acerto {100*r:5.1f}%  resultado {p:+9.2f}")
for titulo, sel in (('DESDE 09/10 (referência)', lambda t: True), ('ENTRADAS NOVAS (desde o baseline)', lambda t: t['entryT'] >= desde), ('HOJE', lambda t: dia(t) == datetime.date.today().isoformat())):
    S = [t for t in fech if sel(t)]
    print(titulo)
    for nome, fn in (('primeira', lambda t: t['run'] == 4), ('duas', lambda t: t['run'] <= 5), ('todas', lambda t: True)): linha(nome, [t for t in S if fn(t)])
    print()
print(f"Equilíbrio: {100*BE:.2f}% | decisão só com centenas de entradas por variante")

# ---- FILTRO CONGELADO (força >= 4,9 ATR14): contagem limpa a partir de 29/10/2026 10:05, sem mexer na regra durante a observação
ini = datetime.datetime(2026, 10, 29, 10, 5).timestamp() * 1000
fortes = [t for t in fech if t['entryT'] >= ini and t.get('forte') is True]
todos = [t for t in fech if t['entryT'] >= ini]
print('FILTRO CONGELADO (só sinais fortes, desde 29/10 10:05; regra fixa até 30/11)')
linha('fortes', fortes); linha('todos', todos)
