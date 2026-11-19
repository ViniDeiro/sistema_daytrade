"""Robustez ao dia de início (offline): janela 08h-22h, entrada fixa de 1% a 5% de $2.000. Começa em CADA dia possível e opera 30 dias."""
src=open('dados/janela.py').read().split("print(f\"Horário")[0]
exec(src)
days=sorted({day(t) for t,*_ in E_}); bydy=defaultdict(list)
for e in E_: bydy[day(e[0])].append(e)
print(f"{len(days)} dias com entradas; para cada início possível, opera 30 dias (08h-22h) com $2.000:\n")
print(f"{'%':<3}{'entrada':>8} | {'inícios':>7} | {'terminam +':>10} | {'quebram':>7} | {'menor banca':>11} | {'pior 30d':>9} | {'mediana 30d':>11} | {'melhor 30d':>10}")
for pct in (1,2,3,4,5):
    st=BANCA*pct/100; res=[]
    for i in range(0,len(days)-29):
        eq=BANCA; low=BANCA; bust=False
        for d_ in days[i:i+30]:
            for t,s,h in bydy[d_]:
                if eq<st: bust=True; break
                eq+= st*PAY if h else -st; low=min(low,eq)
            if bust: break
        res.append((eq-BANCA,bust,low))
    pl=sorted(r[0] for r in res)
    print(f"{pct:<3}{'$'+str(int(st)):>8} | {len(res):>7} | {sum(r[0]>0 for r in res):>10} | {sum(r[1] for r in res):>7} | {min(r[2] for r in res):>11,.0f} | {pl[0]:>+9,.0f} | {pl[len(pl)//2]:>+11,.0f} | {pl[-1]:>+10,.0f}")
