# Critério de validação ao vivo (combinado em 13/10/2026; prazo alterado em 21/10/2026)

**Mudança em 21/10/2026:** as 2.000 entradas deixam de ser o ponto de decisão e passam a ser só um *checkpoint*. O veredito final é dado em **30/11/2026**, com todas as entradas novas até essa data (os mesmos limites de 53% / 51% valem).


Contagem: **entradas novas** a partir de 12/10/2026 10h38 (régua do painel e do Telegram), entrada de $40, empate devolvido.

| Em 30/11/2026 (todas as entradas novas até lá) | Veredito |
|---|---|
| acerto >= 53% | VALIDADA — a vantagem se confirma ao vivo |
| 51% a 53% | vantagem fraca / inconclusiva — seguir acompanhando, sem aumentar a entrada |
| < 51% | REPROVADA — sem vantagem sobre o equilíbrio (51,02%) |

Pontos intermediários (só para acompanhar, não decidem sozinhos): 100, 200, 300, 500, 1.000, 2.000, 3.000, 4.000, 5.000.
- 500 novas: alarme abaixo de ~49,3%; "vantagem clara" acima de ~55,5%.
- 1.000 novas: alarme abaixo de ~50,6%; "vantagem clara" acima de ~54,2%.
- Se em 1.000 novas o acerto estiver abaixo de ~50,6%, reavaliar antes do fim de novembro.

Calibração (probabilidade de ver >= 53% em 2.000 entradas): acerto real 53,8% -> 76%; 52% -> 18%; 51% -> 3,7%.
Voltar a operar com dinheiro: só depois de pelo menos 500 novas em >= 52% e sem alarme, e começando com entrada pequena.


## Plano de entrada e gatilhos de banca (combinado em 13/10/2026)

Referência: a **banca real**, que na data do combinado estava em **$2.400** (o painel foi ajustado para mostrar esse valor).

1. **$40 por entrada** até **1.000 entradas novas** (a contagem das novas começou em 12/10 10h38).
2. Banca abaixo de **$1.800** (−25%) -> reduzir a entrada para **$30**.
3. Banca abaixo de **$1.200** (−50%) -> reduzir a entrada para **$20** (ou parar).
4. Banca abaixo de **$600** -> **parar** e só voltar depois da validação (veredito de 30/11/2026, acerto >= 53%).
5. Marcos de 500 e 1.000: em 1.000 novas, se o acerto estiver abaixo de ~50,6%, parar para reavaliar.
6. A entrada só desce (não sobe de volta no meio do caminho). Aumentar só depois da validação.


## Filtro de força da sequência (combinado em 29/10/2026)

- **Regra congelada até 30/11/2026:** só sinais com **força >= 4,9** (movimento da sequência / ATR14, calculado na hora do sinal). Não mudar o corte nem o cálculo durante a observação.
- **Contagem limpa:** sinais fortes a partir de **29/10/2026 10h05** (o corte 4,9 saiu do ano 1 do backtest; o forward de 09/10 a 29/10 já foi visto e não conta para a validação).
- **Meta em 30/11:** acerto dos fortes **>= 53%** com pelo menos ~500 entradas fortes -> o filtro se confirma. Entre 51% e 53% -> fraco/inconclusivo. Abaixo de 51% -> reprovado.
- A validação da estratégia completa (todos os sinais) segue com o critério do topo deste arquivo, em 30/11/2026.
- Como acompanhar: `python3 -I dados/variantes.py` (bloco "FILTRO CONGELADO") e as bancas "só fortes" no painel.
