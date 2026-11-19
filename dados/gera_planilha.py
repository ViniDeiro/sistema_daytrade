"""Gera Levantamentos_Estrategia_IDX.xlsx a partir dos dados em dados/ (offline). Uso: python3 dados/gera_planilha.py"""
import json, math
import numpy as np
from collections import defaultdict
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment

exec(open('dados/estudo10.py').read().split("if __name__")[0])      # load, prep, MIN, BE, PAY, BANCA
I = prep('idx'); B = prep('btc')
SKIP = {'t', 'hour', 'ym', 'cont', 'hit_c', 'rev', 'hit_r'}

def runs(kind):
    t, o, c = load(kind); n = len(t); col = np.sign(c - o).astype(int)
    contig = np.zeros(n, bool); contig[1:] = (t[1:] - t[:-1]) == MIN
    run = np.zeros(n, int)
    for i in range(1, n): run[i] = (run[i-1] + 1 if (col[i] != 0 and contig[i] and col[i] == col[i-1]) else (1 if col[i] != 0 else 0))
    pr = np.zeros(n, int); pr[1:] = run[:-1]; idx = np.arange(n)
    elig = contig & (col[idx-1] != 0)
    return pr, (col == col[idx-1]) & elig, elig
prI, hitI, eI = runs('idx'); prB, hitB, eB = runs('btc')
dayI = (I['hour'] >= 8) & (I['hour'] < 22); dayB = (B['hour'] >= 8) & (B['hour'] < 22)
tI = I['t']; tB = B['t']

# ---------- estilos ----------
F = 'Arial'
fN = Font(name=F, size=10); fB = Font(name=F, size=10, bold=True); fT = Font(name=F, size=14, bold=True)
fIn = Font(name=F, size=10, color='0000FF'); fH = Font(name=F, size=10, bold=True, color='FFFFFF'); fG = Font(name=F, size=9, italic=True, color='666666')
fillH = PatternFill('solid', fgColor='1F3A5F'); fillIn = PatternFill('solid', fgColor='FFF2CC'); fillS = PatternFill('solid', fgColor='E8EEF5'); fillTot = PatternFill('solid', fgColor='DDE6F0')
thin = Side(style='thin', color='BBBBBB'); bd = Border(left=thin, right=thin, top=thin, bottom=thin)
PCT = '0.00%'; USD = '$#,##0;($#,##0);-'; INT = '#,##0'
wb = Workbook(); wb.remove(wb.active)

def sheet(name, title, sub=None, widths=None):
    ws = wb.create_sheet(name); ws.sheet_view.showGridLines = False
    ws['A1'] = title; ws['A1'].font = fT
    if sub: ws['A2'] = sub; ws['A2'].font = fG
    for i, w in enumerate(widths or [], 1): ws.column_dimensions[L(i)].width = w
    return ws
def hdr(ws, r, labels, c0=1):
    for j, lab in enumerate(labels):
        c = ws.cell(r, c0 + j, lab); c.font = fH; c.fill = fillH; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = bd
    ws.row_dimensions[r].height = 32
def put(ws, r, c, v, fmt=None, font=None, fill=None, bold=False, align=None):
    cell = ws.cell(r, c, v); cell.font = font or (fB if bold else fN); cell.border = bd
    if fmt: cell.number_format = fmt
    if fill: cell.fill = fill
    if align: cell.alignment = Alignment(horizontal=align)
    return cell
def note(ws, r, text, c=1, span=None):
    cell = ws.cell(r, c, text); cell.font = fG; cell.alignment = Alignment(wrap_text=True, vertical='top')
    if span: ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + span - 1); ws.row_dimensions[r].height = 15 * (1 + len(text) // (span * 14))

# =============== Premissas ===============
P = sheet('Premissas', 'Premissas (edite só as células azuis)', 'Todas as planilhas calculam P/L a partir destas células.', [44, 16, 70])
rows = [('Payout da Ebinex', 0.96, PCT, 'Informado pelo usuário (receita +96%).'),
        ('Banca inicial (US$)', 2000, '$#,##0', 'Informado pelo usuário.'),
        ('Entrada 1% da banca (US$)', '=B3*0.01', '$#,##0', '1% da banca inicial, valor fixo.'),
        ('Entrada 2% da banca (US$)', '=B3*0.02', '$#,##0', ''), ('Entrada 3% da banca (US$)', '=B3*0.03', '$#,##0', ''),
        ('Ponto de equilíbrio por entrada', '=1/(1+B2)', PCT, 'Acerto mínimo para não perder: 1 / (1 + payout).'),
        ('Horário de operação (local)', '08h–22h', None, 'Informado pelo usuário. Fuso do Mac (UTC-3).'),
        ('Doji (fechou = abriu)', 'conta como perda', None, 'Premissa conservadora usada em todos os backtests.'),
        ('Entrada no backtest', 'abertura da vela seguinte', None, 'Premissa: sem atraso de clique e preço = abertura. Só a demo confirma.')]
hdr(P, 1, ['Parâmetro', 'Valor', 'Observação'])
for i, (a_, b_, f_, o_) in enumerate(rows):
    r = i + 2; calc = isinstance(b_, str) and b_.startswith('=')
    put(P, r, 1, a_); put(P, r, 2, b_, f_, font=(fN if calc else fIn), fill=(None if calc else fillIn), align='right'); put(P, r, 3, o_)
note(P, 12, 'Células azuis com fundo amarelo são as editáveis. As demais abas leem estes valores (entrada de 1%/2% e payout); mudar o payout ou a banca recalcula todos os P/L.', span=3)
ST1, ST2, ST3, BEc, PAYc, BANCAc = 'Premissas!$B$4', 'Premissas!$B$5', 'Premissas!$B$6', 'Premissas!$B$7', 'Premissas!$B$2', 'Premissas!$B$3'

# =============== Regra 1 mensal IDX ===============
def months(ym): return sorted(set(ym))
M = months(I['ym'])
ws = sheet('Regra1_Mensal_IDX', 'Regra 1 — 4 ou mais velas iguais, a próxima repete (IDX, 1 ano)', 'Dados: 524.448 velas M1 da Ebinex, 07/10/2025–07/10/2026. Entradas/acertos são contagens; o resto é fórmula.', [11, 11, 11, 11, 13, 13, 12, 12, 11, 13, 13])
hdr(ws, 4, ['Mês', 'Entradas 24h', 'Acertos 24h', 'Acerto 24h', 'P/L 24h entrada 1%', 'P/L 24h entrada 2%', 'Entradas 08–22h', 'Acertos 08–22h', 'Acerto 08–22h', 'P/L 08–22h entrada 1%', 'P/L 08–22h entrada 2%'])
r0 = 5
for i, m in enumerate(M):
    r = r0 + i; mk = I['cont'] & (I['ym'] == m); md = mk & dayI
    put(ws, r, 1, m, align='center')
    put(ws, r, 2, int(mk.sum()), INT, font=fIn); put(ws, r, 3, int(I['hit_c'][mk].sum()), INT, font=fIn); put(ws, r, 4, f'=IF(B{r}=0,0,C{r}/B{r})', PCT)
    put(ws, r, 5, f'={ST1}*(C{r}*{PAYc}-(B{r}-C{r}))', USD); put(ws, r, 6, f'={ST2}*(C{r}*{PAYc}-(B{r}-C{r}))', USD)
    put(ws, r, 7, int(md.sum()), INT, font=fIn); put(ws, r, 8, int(I['hit_c'][md].sum()), INT, font=fIn); put(ws, r, 9, f'=IF(G{r}=0,0,H{r}/G{r})', PCT)
    put(ws, r, 10, f'={ST1}*(H{r}*{PAYc}-(G{r}-H{r}))', USD); put(ws, r, 11, f'={ST2}*(H{r}*{PAYc}-(G{r}-H{r}))', USD)
rl = r0 + len(M) - 1; rt = rl + 1
put(ws, rt, 1, 'ANO', bold=True, fill=fillTot, align='center')
for c in (2, 3, 7, 8): put(ws, rt, c, f'=SUM({L(c)}{r0}:{L(c)}{rl})', INT, bold=True, fill=fillTot)
put(ws, rt, 4, f'=C{rt}/B{rt}', PCT, bold=True, fill=fillTot); put(ws, rt, 9, f'=H{rt}/G{rt}', PCT, bold=True, fill=fillTot)
for c in (5, 6, 10, 11): put(ws, rt, c, f'=SUM({L(c)}{r0}:{L(c)}{rl})', USD, bold=True, fill=fillTot)
put(ws, rt + 1, 1, 'Meses +', bold=True, align='center'); put(ws, rt + 1, 5, f'=COUNTIF(E{r0}:E{rl},">0")', INT); put(ws, rt + 1, 10, f'=COUNTIF(J{r0}:J{rl},">0")', INT)
put(ws, rt + 2, 1, 'Equilíb.', bold=True, align='center'); put(ws, rt + 2, 4, f'={BEc}', PCT); put(ws, rt + 2, 9, f'={BEc}', PCT)
note(ws, rt + 4, 'Out/2026 tem só 7 dias. Meses positivos contam todas as linhas (13). P/L assume entrada fixa e doji como perda. Resultados passados, em backtest; não são previsão.', span=11)
ws.freeze_panes = 'B5'
REG1_TOT = rt

# =============== IDX vs BTC ===============
ws = sheet('Regra1_IDX_vs_BTC', 'Regra 1: IDX (Ebinex) vs Bitcoin real (Binance), mês a mês, 24h', 'Mesmos meses e mesma regra. O BTC fica abaixo do equilíbrio quase o ano todo; o IDX tem um "prêmio" que variou de +2,7 a +7,3 pontos.', [11, 12, 12, 12, 12, 12, 12, 12])
hdr(ws, 4, ['Mês', 'Entradas IDX', 'Acertos IDX', 'Entradas BTC', 'Acertos BTC', 'Acerto IDX', 'Acerto BTC', 'Diferença (pontos)'])
MB = [m for m in months(B['ym']) if m in set(M)]
for i, m in enumerate(MB):
    r = 5 + i; a = I['cont'] & (I['ym'] == m); b = B['cont'] & (B['ym'] == m)
    put(ws, r, 1, m, align='center'); put(ws, r, 2, int(a.sum()), INT, font=fIn); put(ws, r, 3, int(I['hit_c'][a].sum()), INT, font=fIn)
    put(ws, r, 4, int(b.sum()), INT, font=fIn); put(ws, r, 5, int(B['hit_c'][b].sum()), INT, font=fIn)
    put(ws, r, 6, f'=C{r}/B{r}', PCT); put(ws, r, 7, f'=E{r}/D{r}', PCT); put(ws, r, 8, f'=(F{r}-G{r})*100', '0.00')
rl = 5 + len(MB) - 1; rt = rl + 1
put(ws, rt, 1, 'ANO', bold=True, fill=fillTot, align='center')
for c in (2, 3, 4, 5): put(ws, rt, c, f'=SUM({L(c)}5:{L(c)}{rl})', INT, bold=True, fill=fillTot)
put(ws, rt, 6, f'=C{rt}/B{rt}', PCT, bold=True, fill=fillTot); put(ws, rt, 7, f'=E{rt}/D{rt}', PCT, bold=True, fill=fillTot); put(ws, rt, 8, f'=(F{rt}-G{rt})*100', '0.00', bold=True, fill=fillTot)
put(ws, rt + 1, 1, 'Equilíb.', bold=True, align='center'); put(ws, rt + 1, 6, f'={BEc}', PCT); put(ws, rt + 1, 7, f'={BEc}', PCT)
note(ws, rt + 3, 'BTC: dados públicos da Binance (BTCUSDT 1m), 525.601 velas. Doji do BTC é mais frequente (~3%) do que o do IDX (~0,7%) e conta como perda nos dois.', span=8)
ws.freeze_panes = 'B5'
BTC_TOT = rt

# =============== Sequência e reentrada ===============
ws = sheet('Sequencia_e_Reentrada', 'Acerto da continuação por tamanho da sequência de velas iguais antes da entrada', 'Ano inteiro, 24h. "s" = nº de velas iguais seguidas imediatamente antes da vela de entrada.', [14, 13, 13, 12, 13, 13, 12])
hdr(ws, 4, ['Sequência (s)', 'Entradas IDX', 'Acertos IDX', 'Acerto IDX', 'Entradas BTC', 'Acertos BTC', 'Acerto BTC'])
for i, s in enumerate(list(range(1, 11))):
    r = 5 + i; mi = (prI == s) & eI; mb = (prB == s) & eB
    lab = f'{s}' if s < 10 else '10'
    put(ws, r, 1, s, align='center'); put(ws, r, 2, int(mi.sum()), INT, font=fIn); put(ws, r, 3, int(hitI[mi].sum()), INT, font=fIn); put(ws, r, 4, f'=C{r}/B{r}', PCT)
    put(ws, r, 5, int(mb.sum()), INT, font=fIn); put(ws, r, 6, int(hitB[mb].sum()), INT, font=fIn); put(ws, r, 7, f'=F{r}/E{r}', PCT)
put(ws, 15, 1, 'Equilíbrio', bold=True, align='center'); put(ws, 15, 4, f'={BEc}', PCT); put(ws, 15, 7, f'={BEc}', PCT)
note(ws, 16, 'A partir de s=4 o IDX fica ~52–57%; o BTC fica abaixo de 50%. s=1 e s=2 não dão vantagem estável.', span=7)
ws['A18'] = 'Como contar as reentradas depois da 5ª vela (IDX, 1 ano, entrada fixa de 1% = $20)'; ws['A18'].font = fB
hdr(ws, 19, ['Variante', 'Entradas 24h', 'Acertos 24h', 'Acerto 24h', 'Entradas 08–22h', 'Acertos 08–22h', 'Acerto 08–22h', 'P/L 24h', 'P/L 08–22h'])
for c, w in zip('HI', (13, 13)): ws.column_dimensions[c].width = w
variants = [('A) só 1 vez por sequência (s = 4)', (prI == 4) & eI), ('B) continua a cada vela (s ≥ 4)', (prI >= 4) & eI), ('C) espera mais 4 para reentrar (s = 4, 8, 12…)', (prI >= 4) & (prI % 4 == 0) & eI)]
for i, (lab, mk) in enumerate(variants):
    r = 20 + i; md = mk & dayI
    put(ws, r, 1, lab); put(ws, r, 2, int(mk.sum()), INT, font=fIn); put(ws, r, 3, int(hitI[mk].sum()), INT, font=fIn); put(ws, r, 4, f'=C{r}/B{r}', PCT)
    put(ws, r, 5, int(md.sum()), INT, font=fIn); put(ws, r, 6, int(hitI[md].sum()), INT, font=fIn); put(ws, r, 7, f'=F{r}/E{r}', PCT)
    put(ws, r, 8, f'={ST1}*(C{r}*{PAYc}-(B{r}-C{r}))', USD); put(ws, r, 9, f'={ST1}*(F{r}*{PAYc}-(E{r}-F{r}))', USD)
ws.column_dimensions['A'].width = 46; ws.freeze_panes = 'A5'

# =============== Regra 2 ===============
ws = sheet('Regra2_Reversao_IDX', 'Regra 2 — reversão após vela grande (≥3× a média das 60 anteriores), 1ª vela do quadrante de 5 min', 'Aposta na cor oposta da vela anterior quando minuto%5 = 0. IDX, 1 ano.', [11, 11, 11, 11, 13, 13, 12, 12, 11, 13, 13])
hdr(ws, 4, ['Mês', 'Entradas 24h', 'Acertos 24h', 'Acerto 24h', 'P/L 24h entrada 1%', 'P/L 24h entrada 2%', 'Entradas 08–22h', 'Acertos 08–22h', 'Acerto 08–22h', 'P/L 08–22h entrada 1%', 'P/L 08–22h entrada 2%'])
for i, m in enumerate(M):
    r = 5 + i; mk = I['rev'] & (I['ym'] == m); md = mk & dayI
    put(ws, r, 1, m, align='center'); put(ws, r, 2, int(mk.sum()), INT, font=fIn); put(ws, r, 3, int(I['hit_r'][mk].sum()), INT, font=fIn); put(ws, r, 4, f'=IF(B{r}=0,0,C{r}/B{r})', PCT)
    put(ws, r, 5, f'={ST1}*(C{r}*{PAYc}-(B{r}-C{r}))', USD); put(ws, r, 6, f'={ST2}*(C{r}*{PAYc}-(B{r}-C{r}))', USD)
    put(ws, r, 7, int(md.sum()), INT, font=fIn); put(ws, r, 8, int(I['hit_r'][md].sum()), INT, font=fIn); put(ws, r, 9, f'=IF(G{r}=0,0,H{r}/G{r})', PCT)
    put(ws, r, 10, f'={ST1}*(H{r}*{PAYc}-(G{r}-H{r}))', USD); put(ws, r, 11, f'={ST2}*(H{r}*{PAYc}-(G{r}-H{r}))', USD)
rl = 5 + len(M) - 1; rt = rl + 1
put(ws, rt, 1, 'ANO', bold=True, fill=fillTot, align='center')
for c in (2, 3, 7, 8): put(ws, rt, c, f'=SUM({L(c)}5:{L(c)}{rl})', INT, bold=True, fill=fillTot)
put(ws, rt, 4, f'=C{rt}/B{rt}', PCT, bold=True, fill=fillTot); put(ws, rt, 9, f'=H{rt}/G{rt}', PCT, bold=True, fill=fillTot)
for c in (5, 6, 10, 11): put(ws, rt, c, f'=SUM({L(c)}5:{L(c)}{rl})', USD, bold=True, fill=fillTot)
REG2_TOT = rt
r = rt + 3; ws.cell(r, 1, 'Validação do limiar (escolhido só no treino do BTC, antes de 09/07/2026) — valores reportados na conversa').font = fB
hdr(ws, r + 1, ['Onde', 'Acerto', 'Entradas', 'IC 95% inf.', 'IC 95% sup.'])
val = [('BTC treino (limiar 3×)', 0.5825, 3097, None, None), ('BTC 09/07–07/10', 0.5228, 1272, 0.490, 0.553), ('IDX 09/07–07/10', 0.5327, 1100, 0.504, 0.561), ('ETH ~1 mês', 0.5180, 305, 0.473, 0.564), ('SOL ~1 mês', 0.5490, 286, 0.487, 0.608)]
for i, (a, b, c_, d_, e_) in enumerate(val):
    put(ws, r + 2 + i, 1, a); put(ws, r + 2 + i, 2, b, PCT, font=fIn); put(ws, r + 2 + i, 3, c_, INT, font=fIn); put(ws, r + 2 + i, 4, d_, PCT, font=fIn); put(ws, r + 2 + i, 5, e_, PCT, font=fIn)
note(ws, r + 8, 'O efeito encolheu do treino (58%) para os testes (52–55%). Nenhum teste individual é estatisticamente forte; eles cobrem o mesmo período e não são independentes. Fonte: dados/estudo9.py.', span=11)
ws.column_dimensions['A'].width = 24; ws.freeze_panes = 'B5'

# =============== Banca ===============
def day_entries(mask, kind=I, hits=None):
    t = kind['t']; hits = kind['hit_c'] if hits is None else hits
    d = defaultdict(list)
    for i in np.where(mask)[0]: d[datetime.fromtimestamp(t[i] / 1000).date()].append(bool(hits[i]))
    return d
def sim_bank(entries, stake, bank0=2000, pay=0.96):
    eq = bank0; pk = bank0; dd = 0; low = bank0; bust = False
    for h in entries:
        if eq < stake: bust = True; break
        eq += stake * pay if h else -stake; pk = max(pk, eq); dd = max(dd, pk - eq); low = min(low, eq)
    return eq, low, dd, bust
byd = {'08–22h': day_entries(I['cont'] & dayI), '24h': day_entries(I['cont'])}
ws = sheet('Banca_Inicio_Aleatorio', 'Regra 1 — e se tivesse começado em QUALQUER dia? (IDX, 30 dias seguidos, banca de $2.000)', 'Para cada dia do ano como início, opera 30 dias com entrada fixa. "Quebrou" = banca menor que a entrada em algum momento.', [11, 12, 10, 14, 11, 16, 14, 13, 13])
rr = 4
for nome, dd_ in byd.items():
    ws.cell(rr, 1, f'Horário: {nome}').font = fB; rr += 1
    hdr(ws, rr, ['% da banca', 'Entrada (US$)', 'Inícios', 'Terminam no positivo', 'Quebram', 'Menor banca vista', 'Pior resultado 30d', 'Mediana 30d', 'Melhor 30d']); rr += 1
    days = sorted(dd_)
    for pct in (1, 2, 3, 4, 5):
        stake = 2000 * pct / 100; res = []
        for k in range(0, len(days) - 29):
            seq = [h for d_ in days[k:k + 30] for h in dd_[d_]]
            eq, low, dd2, bust = sim_bank(seq, stake); res.append((eq - 2000, bust, low))
        pl = sorted(x[0] for x in res)
        put(ws, rr, 1, pct / 100, '0%', font=fIn); put(ws, rr, 2, f'={BANCAc}*A{rr}', '$#,##0'); put(ws, rr, 3, len(res), INT, font=fIn)
        put(ws, rr, 4, sum(x[0] > 0 for x in res), INT, font=fIn); put(ws, rr, 5, sum(x[1] for x in res), INT, font=fIn)
        put(ws, rr, 6, min(x[2] for x in res), USD, font=fIn); put(ws, rr, 7, pl[0], USD, font=fIn); put(ws, rr, 8, pl[len(pl) // 2], USD, font=fIn); put(ws, rr, 9, pl[-1], USD, font=fIn); rr += 1
    rr += 2
note(ws, rr, 'Com 1% e só 08–22h nenhuma janela quebrou, mas a banca chegou a ~$427. A partir de 2% aparecem inícios em que quebra. Entradas calculadas na simulação com banca de $2.000 e payout de 96% fixos (Premissas).', span=9)
BANCA_SHEET_ROWS = rr

# 90 dias e ano inteiro, banca desde o 1º dia
ws = sheet('Banca_Desde_1o_Dia', 'Regra 1 — banca de $2.000 desde o 1º dia (IDX)', 'Ano inteiro e últimos 90 dias, horário 08h–22h, entrada fixa em % da banca inicial.', [22, 12, 14, 14, 14, 14, 14, 14, 12])
tmax = tI.max(); is90 = tI >= (tmax - 90 * 86400_000)
hdr(ws, 4, ['Período', '% da banca', 'Entrada (US$)', 'Resultado', 'Banca final', 'Menor banca', 'Maior queda', 'Pior dia', 'Quebrou?'])
rr = 5
for lab, extra in (('Ano inteiro (08–22h)', np.ones(len(tI), bool)), ('Últimos 90 dias (08–22h)', is90)):
    mk = I['cont'] & dayI & extra; ents = [(tI[i], bool(I['hit_c'][i])) for i in np.where(mk)[0]]
    for pct in (1, 2, 3, 4, 5):
        stake = 2000 * pct / 100; eq = 2000; pk = 2000; dd_ = 0; low = 2000; bust = False; byday = defaultdict(float)
        for t_, h in ents:
            if eq < stake: bust = True; break
            r_ = stake * 0.96 if h else -stake; eq += r_; byday[datetime.fromtimestamp(t_ / 1000).date()] += r_; pk = max(pk, eq); dd_ = max(dd_, pk - eq); low = min(low, eq)
        put(ws, rr, 1, lab); put(ws, rr, 2, pct / 100, '0%', font=fIn); put(ws, rr, 3, f'={BANCAc}*B{rr}', '$#,##0')
        put(ws, rr, 4, eq - 2000, USD, font=fIn); put(ws, rr, 5, f'={BANCAc}+D{rr}', USD); put(ws, rr, 6, low, USD, font=fIn); put(ws, rr, 7, dd_, USD, font=fIn)
        put(ws, rr, 8, min(byday.values()), USD, font=fIn); put(ws, rr, 9, 'SIM' if bust else 'não', align='center'); rr += 1
    rr += 1
note(ws, rr, 'Começando no 1º dia nenhuma faixa quebra, mas isso depende de o início ter sido tranquilo — veja a aba Banca_Inicio_Aleatorio. Resultado/queda/pior dia são valores da simulação; banca final = banca inicial + resultado.', span=9)

# =============== Diário ===============
ws = sheet('Diario_Regra1_08a22', 'Resultado diário — Regra 1, 08h–22h, IDX (1 ano)', 'Entradas e acertos por dia (contagens); P/L e banca acumulada por fórmula (entrada fixa = 1% e 2% da Premissas).', [12, 10, 10, 10, 14, 14, 15, 15])
hdr(ws, 4, ['Data', 'Entradas', 'Acertos', 'Acerto', 'P/L entrada 1%', 'P/L entrada 2%', 'Banca acum. 1%', 'Banca acum. 2%'])
dd_ = byd['08–22h']; dl = sorted(dd_)
for i, d in enumerate(dl):
    r = 5 + i; n = len(dd_[d]); k = sum(dd_[d])
    put(ws, r, 1, d.strftime('%Y-%m-%d'), align='center'); put(ws, r, 2, n, INT, font=fIn); put(ws, r, 3, k, INT, font=fIn); put(ws, r, 4, f'=IF(B{r}=0,0,C{r}/B{r})', PCT)
    put(ws, r, 5, f'={ST1}*(C{r}*{PAYc}-(B{r}-C{r}))', USD); put(ws, r, 6, f'={ST2}*(C{r}*{PAYc}-(B{r}-C{r}))', USD)
    put(ws, r, 7, f'={BANCAc}+E{r}' if i == 0 else f'=G{r-1}+E{r}', USD); put(ws, r, 8, f'={BANCAc}+F{r}' if i == 0 else f'=H{r-1}+F{r}', USD)
ws.freeze_panes = 'B5'

# =============== Quadrantes / Martingale (estáticos da conversa) ===============
ws = sheet('Quadrantes_Martingale', 'Estratégias de quadrante (4x2 e Padrão 23) e o teste de Martingale — resultados da conversa', 'Valores estáticos reportados nas etapas iniciais (backtest.py, backtest_mes.py, mes_ilimitado.py). Entradas: 22 / 50 / 112 / 251 / 565.', [30, 12, 12, 12, 12, 12, 12, 12, 13, 13])
ws['A4'] = 'Catalogação das últimas 5 horas (07/10, ~11:40) — win de 1ª, Gale 1, Gale 2, loss'; ws['A4'].font = fB
hdr(ws, 5, ['Estratégia', 'Ciclos', 'Win 1ª', 'Gale 1', 'Gale 2', 'Loss', 'Assertividade (win 1ª)'])
for i, (n, c, a, b, d_, e) in enumerate((('4x2', 69, 33, 21, 6, 9), ('Padrão 23', 70, 27, 22, 9, 12))):
    r = 6 + i; put(ws, r, 1, n); [put(ws, r, j + 2, v, INT, font=fIn) for j, v in enumerate((c, a, b, d_, e))]; put(ws, r, 7, f'=C{r}/B{r}', PCT)
ws['A9'] = 'Backtest com Martingale contra o win de 1ª (gatilho: 4x2 após 3 wins; Padrão 23 após 4 wins)'; ws['A9'].font = fB
hdr(ws, 10, ['Janela / estratégia', 'Entradas', 'Acertos', 'Ciclos', 'Win nív. 1', 'Win nív. 2', 'Win nív. 3', 'Win nív. 4', 'Win nív. 5', 'Loss de ciclo', 'Resultado US$', 'Maior queda US$'])
ws.column_dimensions['K'].width = 14; ws.column_dimensions['L'].width = 14
mart = [('48h — 4x2', 49, 32, 33, 26, 2, 3, 0, 1, 1, -184.92, 1185.24), ('48h — Padrão 23', 38, 20, 20, 10, 5, 3, 1, 1, 0, 612.12, 435.00),
        ('72h — 4x2', 81, 47, 48, 32, 6, 6, 1, 2, 1, 316.72, 1185.24), ('72h — Padrão 23', 61, 31, 31, 15, 8, 4, 2, 2, 0, 995.60, 435.00),
        ('30 dias — 4x2 (banca ilimitada)', 988, 485, 505, 258, 111, 75, 22, 19, 20, -5707, 7263), ('30 dias — Padrão 23 (banca ilimitada)', 617, 283, 296, 139, 69, 40, 20, 15, 13, -4099, 6705)]
for i, row in enumerate(mart):
    r = 11 + i; put(ws, r, 1, row[0])
    for j, v in enumerate(row[1:], 2): put(ws, r, j, v, USD if j >= 11 else INT, font=fIn)
note(ws, 17, 'Com banca de $2.000 e ciclo completo de $1.000, a 4x2 quebrou em 09/09 e o Padrão 23 em 12/09 (simulação de 30 dias). Os resultados de 48h/72h pareciam positivos por ausência de um ciclo perdido — uma única perda de $1.000 vira o resultado.', span=12)
ws['A19'] = 'Valor esperado por ciclo (Martingale 5 níveis) conforme a chance de acerto por entrada — por fórmula'; ws['A19'].font = fB
ws['A20'] = 'Entradas por nível'; ws['A20'].font = fN
for j, v in enumerate((22, 50, 112, 251, 565)): put(ws, 20, 2 + j, v, '$#,##0', font=fIn, fill=fillIn)
hdr(ws, 21, ['Chance de acerto por entrada', 'P(perder o ciclo)', '1 a cada N ciclos', 'Valor esperado por ciclo (US$)'])
for i, p in enumerate((0.46, 0.50, 0.54, 0.58)):
    r = 22 + i; put(ws, r, 1, p, '0%', font=fIn, fill=fillIn)
    put(ws, r, 2, f'=(1-A{r})^5', PCT); put(ws, r, 3, f'=1/B{r}', '0');
    ev = '+'.join(f'((1-A{r})^{k}*A{r}*({L(2+k)}$20*{PAYc}-SUM($B$20:{L(2+k)}$20)+{L(2+k)}$20))' for k in range(5))
    put(ws, r, 4, f'={ev}-B{r}*SUM($B$20:$F$20)', '$#,##0.00;($#,##0.00)')
note(ws, 27, 'Com 50% de acerto o valor esperado é negativo: nenhum esquema de Martingale muda o valor esperado de cada entrada, só a distribuição (muitos ganhos pequenos, poucas perdas de $1.000).', span=8)

# =============== Primeiros estudos (estáticos) ===============
ws = sheet('Estudos_Iniciais', 'Estudos iniciais e comparações pontuais — resultados da conversa', 'Valores estáticos reportados nas respostas (estudo1–5, proxy.py, estudo6.py).', [44, 14, 14, 14, 16, 14])
ws['A4'] = 'Padrões vela a vela: 1 mês de IDX, treino = 1ª metade, teste = 2ª metade (equilíbrio 51,02%)'; ws['A4'].font = fB
hdr(ws, 5, ['Condição (4+ iguais) / tendência', 'Treino', 'Teste', 'n teste'])
for i, (a, b, c_, d_) in enumerate((('A favor da tendência de 15 velas', 0.539, 0.551, 2550), ('Contra a tendência de 15 velas', 0.524, 0.536, 614), ('A favor da tendência de 60 velas', 0.538, 0.538, 2022), ('Contra a tendência de 60 velas', 0.533, 0.565, 1144), ('A favor da tendência de 240 velas', 0.525, 0.541, 1753), ('Contra a tendência de 240 velas', 0.549, 0.556, 1412))):
    r = 6 + i; put(ws, r, 1, a); put(ws, r, 2, b, PCT, font=fIn); put(ws, r, 3, c_, PCT, font=fIn); put(ws, r, 4, d_, INT, font=fIn)
note(ws, 12, 'O filtro de tendência não melhorou o acerto: os dois lados ficam em ~53–56%.', span=6)
ws['A14'] = 'Mesma regra (4+ iguais) em 1 mês de mercado público (07/09–07/10/2026)'; ws['A14'].font = fB
hdr(ws, 15, ['Ativo', 'Acerto', 'Entradas'])
for i, (a, b, c_) in enumerate((('IDX (Ebinex)', 0.5422, 6132), ('Bitcoin', 0.5115, 5306), ('Ethereum', 0.4979, 5150), ('Solana', 0.4789, 4358))):
    r = 16 + i; put(ws, r, 1, a); put(ws, r, 2, b, PCT, font=fIn); put(ws, r, 3, c_, INT, font=fIn)
ws['A21'] = 'IDX por períodos de 30 dias (3 meses) — regra 4+ iguais (os 2 meses mais antigos não foram usados para descobrir a regra)'; ws['A21'].font = fB
hdr(ws, 22, ['Período', 'Acerto', 'Entradas', '$22 fixo', 'Por dia'])
for i, (a, b, c_, d_, e_) in enumerate((('09/07–08/08 (novo)', 0.5280, 5869, 4511, 146), ('08/08–07/09 (novo)', 0.5370, 5913, 6820, 220), ('07/09–07/10 (descoberta)', 0.5422, 6134, 8469, 273))):
    r = 23 + i; put(ws, r, 1, a); put(ws, r, 2, b, PCT, font=fIn); put(ws, r, 3, c_, INT, font=fIn); put(ws, r, 4, d_, USD, font=fIn); put(ws, r, 5, e_, USD, font=fIn)
note(ws, 27, 'Nos 2 meses mais antigos: 53,25% (IC 95% 52,1%–54,4%). 13 de 13 semanas completas acima do equilíbrio.', span=6)
ws['A29'] = 'Janelas de 90 dias do BTC (regra 4+ iguais)'; ws['A29'].font = fB
hdr(ws, 30, ['Bloco de 90 dias', 'Acerto BTC'])
for i, (a, b) in enumerate((('07/10/2025–05/01/2026', 0.4723), ('05/01/2026–05/04/2026', 0.4672), ('05/04/2026–04/07/2026', 0.4707), ('04/07/2026–02/10/2026', 0.5021))):
    put(ws, 31 + i, 1, a); put(ws, 31 + i, 2, b, PCT, font=fIn)

# =============== Forward test ===============
ws = sheet('Forward_Test', 'Forward test ao vivo (papel) — registro das operações', 'Instantâneo de dados/forward_log.json no momento em que a planilha foi gerada. Reexecute python3 dados/gera_planilha.py para atualizar.', [18, 11, 11, 11, 18, 12, 12, 16, 14, 12])
try: log = json.load(open('dados/forward_log.json')).get('trades', [])
except Exception: log = []
hdr(ws, 4, ['Hora do sinal', 'Direção', 'Sequência', 'Status', 'Hora da entrada', 'Preço entrada', 'Preço saída', '4ª vela fechou igual?', 'Resultado', 'P/L (US$)'])
tm = lambda ms: datetime.fromtimestamp(ms / 1000).strftime('%d/%m %H:%M:%S')
for i, t in enumerate(sorted(log, key=lambda x: x['sigT'])):
    r = 5 + i
    put(ws, r, 1, tm(t['sigT'] + 53000)); put(ws, r, 2, 'compra' if t['dir'] == 'G' else 'venda', align='center'); put(ws, r, 3, t.get('run'), INT)
    put(ws, r, 4, t['status']); put(ws, r, 5, tm(t['entryT'])); put(ws, r, 6, t.get('entryPrice')); put(ws, r, 7, t.get('exitPrice'))
    put(ws, r, 8, {True: 'sim', False: 'NÃO (virou)', None: '–'}.get(t.get('sinalConfirmado'), '–'), align='center')
    put(ws, r, 9, 'WIN' if t.get('win') else ('LOSS' if t['status'] == 'fechado' else '–'), align='center')
    put(ws, r, 10, f'=IF(D{r}="fechado",IF(I{r}="WIN",{ST1}*{PAYc},-{ST1}),0)', '$#,##0.00;($#,##0.00);-')
last = 5 + max(len(log), 1) - 1
ws.cell(last + 2, 1, 'Resumo').font = fB
put(ws, last + 3, 1, 'Operações fechadas'); put(ws, last + 3, 2, f'=COUNTIF(D5:D{last},"fechado")', INT)
put(ws, last + 4, 1, 'Wins'); put(ws, last + 4, 2, f'=COUNTIF(I5:I{last},"WIN")', INT)
put(ws, last + 5, 1, 'Acerto'); put(ws, last + 5, 2, f'=IF(B{last+3}=0,0,B{last+4}/B{last+3})', PCT)
put(ws, last + 6, 1, 'Resultado (US$)'); put(ws, last + 6, 2, f'=SUM(J5:J{last})', '$#,##0.00;($#,##0.00);-')
put(ws, last + 7, 1, 'Banca virtual'); put(ws, last + 7, 2, f'={BANCAc}+B{last+6}', '$#,##0.00')
put(ws, last + 8, 1, 'Equilíbrio'); put(ws, last + 8, 2, f'={BEc}', PCT)
note(ws, last + 10, 'P/L usa a entrada de 1% da aba Premissas. O motor registra a direção a ~7s do fim da 4ª vela; "4ª vela fechou igual?" mostra os casos em que a vela virou de cor depois do aviso.', span=10)
ws.freeze_panes = 'A5'

# =============== Fontes ===============
ws = sheet('Fontes_e_Arquivos', 'Fontes de dados e scripts', None, [42, 90])
hdr(ws, 3, ['Arquivo', 'O que é'])
files = [('dados/candles.json', 'IDX/USDT M1 da Ebinex: 524.448 velas, 07/10/2025–07/10/2026 (coletado pela conta da esposa).'), ('dados/candles_3meses_2026-10-07.json', 'Cópia com 3 meses de IDX.'),
         ('dados/candles_1mes_2026-10-07.json', 'Cópia com 1 mês de IDX.'), ('dados/candles_IDX_1ano_2026-10-07.json', 'Cópia de segurança do ano completo de IDX.'),
         ('dados/binance_BTCUSDT_1ano.json', 'BTCUSDT M1 público (Binance), 525.601 velas, 1 ano.'), ('dados/binance_ETHUSDT_1mes.json / binance_SOLUSDT_1mes.json', 'ETH e SOL, ~1 mês, públicos.'),
         ('dados/forward_log.json', 'Registro do forward test ao vivo (operações de papel).'), ('dados/quadrantes_1mes.csv', 'Cores das 6 velas de cada quadrante de 5 min, 1 mês.'),
         ('dados/estudo1.py … estudo10.py', 'Estudos de previsão de cor, continuação, tendência, busca de padrões e ano completo.'), ('dados/backtest*.py, mes_ilimitado.py', 'Backtests de Martingale (4x2 e Padrão 23).'),
         ('dados/janela*.py, ano_inicio.py, reentrada.py', 'Backtests de janela 08h–22h, dia de início aleatório e reentrada.'), ('live.mjs / serve.mjs / index.html', 'Painel local com forward test ao vivo (somente leitura).')]
for i, (a, b) in enumerate(files): put(ws, 4 + i, 1, a); put(ws, 4 + i, 2, b)
note(ws, 4 + len(files) + 1, 'Todos os resultados são backtests do passado, com as premissas da aba Premissas (entrada na abertura, doji como perda, sem limite da corretora). Não são previsão.', span=2)

# =============== Resumo (primeira aba) ===============
ws = sheet('Resumo', 'Resumo dos levantamentos — estratégias de velas M1 no IDX/USDT (Ebinex)', 'Gerado em ' + datetime.now().strftime('%d/%m/%Y %H:%M') + '. Números ligados às demais abas.', [58, 18, 18, 18])
ws.sheet_properties.tabColor = '1F3A5F'
ws['A4'] = 'Números-chave'; ws['A4'].font = fB
hdr(ws, 5, ['Indicador', '24 horas', '08h–22h', 'Onde'])
kk = [('Regra 1 (4+ velas iguais, IDX): acerto no ano', f"=Regra1_Mensal_IDX!D{REG1_TOT}", f"=Regra1_Mensal_IDX!I{REG1_TOT}", PCT, 'Regra1_Mensal_IDX'),
      ('Regra 1: resultado no ano com entrada de 1%', f"=Regra1_Mensal_IDX!E{REG1_TOT}", f"=Regra1_Mensal_IDX!J{REG1_TOT}", USD, 'Regra1_Mensal_IDX'),
      ('Regra 1: resultado no ano com entrada de 2%', f"=Regra1_Mensal_IDX!F{REG1_TOT}", f"=Regra1_Mensal_IDX!K{REG1_TOT}", USD, 'Regra1_Mensal_IDX'),
      ('Regra 1: meses positivos (de 13)', f"=Regra1_Mensal_IDX!E{REG1_TOT+1}", f"=Regra1_Mensal_IDX!J{REG1_TOT+1}", INT, 'Regra1_Mensal_IDX'),
      ('Mesma regra no Bitcoin real: acerto no ano', f"=Regra1_IDX_vs_BTC!G{BTC_TOT}", None, PCT, 'Regra1_IDX_vs_BTC'),
      ('Regra 2 (reversão após vela grande, IDX): acerto no ano', f"=Regra2_Reversao_IDX!D{REG2_TOT}", f"=Regra2_Reversao_IDX!I{REG2_TOT}", PCT, 'Regra2_Reversao_IDX'),
      ('Ponto de equilíbrio por entrada (payout 96%)', f'={BEc}', f'={BEc}', PCT, 'Premissas')]
for i, (a, b, c_, f_, o) in enumerate(kk):
    r = 6 + i; put(ws, r, 1, a); put(ws, r, 2, b, f_); put(ws, r, 3, c_, f_); put(ws, r, 4, o)
ws['A15'] = 'Conclusões'; ws['A15'].font = fB
concl = ['1. As estratégias de quadrante (4x2 e Padrão 23) NÃO têm vantagem: o win de 1ª fica abaixo do equilíbrio e o Martingale só concentra o risco em poucos ciclos de -$1.000 (aba Quadrantes_Martingale).',
         '2. A regra "4+ velas iguais, a próxima repete" funciona no IDX (~53–54%) em 11–12 dos 13 meses, mas NÃO no Bitcoin real (~48% no ano): o efeito é específico do índice da Ebinex.',
         '3. O efeito foi mais fraco de out/25 a mar/26 (~51,7%) e mais forte de abr a out/26 (~53,8%). Se voltar à fase fraca, a vantagem some.',
         '4. Com a banca de $2.000, entrada de 1% e só 08h–22h, nenhuma janela de 30 dias quebrou, mas a banca chegou a ~$427; com 2% há inícios que quebram (aba Banca_Inicio_Aleatorio).',
         '5. A regra 2 (reversão após vela grande) rende ~10x menos e perdeu força no teste fora da amostra.',
         '6. Todos os números são backtests do passado com entrada exata na abertura e doji como perda. A validação real é o forward test (aba Forward_Test) e, depois, a demo com registro das entradas.']
for i, t in enumerate(concl):
    c = ws.cell(16 + i, 1, t); c.font = fN; c.alignment = Alignment(wrap_text=True, vertical='top'); ws.merge_cells(start_row=16 + i, start_column=1, end_row=16 + i, end_column=4); ws.row_dimensions[16 + i].height = 44
ws['A23'] = 'Abas'; ws['A23'].font = fB
tabs = ['Premissas — parâmetros editáveis', 'Regra1_Mensal_IDX / Regra1_IDX_vs_BTC / Sequencia_e_Reentrada', 'Regra2_Reversao_IDX', 'Banca_Inicio_Aleatorio / Banca_Desde_1o_Dia / Diario_Regra1_08a22',
        'Quadrantes_Martingale / Estudos_Iniciais', 'Forward_Test — registro ao vivo (papel)', 'Fontes_e_Arquivos']
for i, t in enumerate(tabs): ws.cell(24 + i, 1, t).font = fN

order = ['Resumo', 'Premissas', 'Regra1_Mensal_IDX', 'Regra1_IDX_vs_BTC', 'Sequencia_e_Reentrada', 'Regra2_Reversao_IDX', 'Banca_Inicio_Aleatorio', 'Banca_Desde_1o_Dia', 'Diario_Regra1_08a22', 'Quadrantes_Martingale', 'Estudos_Iniciais', 'Forward_Test', 'Fontes_e_Arquivos']
wb._sheets = [wb[n] for n in order]
wb.save('Levantamentos_Estrategia_IDX.xlsx'); print('salvo')
