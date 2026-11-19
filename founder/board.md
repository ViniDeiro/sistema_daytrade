# Parecer da diretoria — Daytrader IDX (robô + painel)
Voto: 2 PASS (Offers 3/10, Monopoly 2/10), 1 FUND IF (Product 3/10). Nota média 2,7/10.

## Riscos levantados por mais de um membro
1. Sem vantagem comprovada: 49,49% em 1.853 entradas novas vs equilíbrio 51,02% (EV -$1,20/entrada, -$2.220,80 no total).
2. Filtro >=4,9 ATR contaminado: corte escolhido vendo dados; amostra limpa = 16 entradas (50,0%), sem informação estatística.
3. Variantes de banca (Soros, stops, janelas) não criam vantagem em cima de EV negativo.
4. Painel sem núcleo provado; produtizar agora vende uma promessa sem prova.

## Condições (checklist)
- [ ] Não mexer no filtro até 30/11; juntar >=800–1.000 entradas limpas pós 29/10 (>=53%, limite inferior do IC > 51,02%).
- [ ] Dinheiro real = zero até o veredito.
- [ ] Regra de parada escrita: se 30/11 < 51%, encerrar a estratégia.
- [ ] Congelar variantes; manter só fixo $40 como base.
- [ ] Bot como fonte da verdade: gravar trades de papel no Supabase; Operações só para fills reais.
- [ ] Sem novas telas/produto antes do veredito; esconder Projeção, Impostos e link público até banca positiva.
