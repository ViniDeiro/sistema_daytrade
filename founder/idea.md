# Daytrader IDX — robô de sinais + painel de gestão da banca

- What it is: operação pessoal de day trade em opções binárias (IDX/USDT, vela M1) com (1) um robô de sinais ao vivo que opera em PAPEL (não envia ordens) pela regra "N velas iguais -> a próxima repete" e avisa por Telegram, e (2) um painel web (Vite/React/Supabase) para controlar banca, operações, aportes, projeção e impostos.
- Who it is for: o próprio fundador (uso pessoal). O painel já tem login por usuário e link público da banca, então poderia virar produto para outros traders.
- What it sells, at what price: nada é vendido hoje. Receita = resultado das entradas: entrada $40, payout 96% (ganha $38,40 / perde $40). Equilíbrio matemático = 51,02% de acerto.
- Where and how: corretora Ebinex, feed do gráfico lido via Playwright; sinais ~7s antes do fechamento da vela; Telegram para avisos.
- Budget and constraints: banca real de referência $2.400 (13/10/2026); regras de redução de entrada em $1.800 / $1.200 / $600; imposto day trade 20% do lucro líquido mensal; veredito marcado para 30/11/2026.

## Dados reais (forward ao vivo em papel, 09/10 a 30/10/2026)
- Todas as entradas: 2.159, acerto 48,72%.
- Entradas NOVAS desde o baseline (12/10 10h38): 1.853 entradas, 913 W / 932 L / 8 E, acerto 49,49%, resultado -$2.220,80 (stake $40).
- Meta de validação: >=53% em 30/11; <51% = reprovada.
- Filtro de força >=4,9 ATR (congelado em 29/10): 408 sinais fortes no histórico forward com 54,32%, MAS o corte foi escolhido olhando backtest e o forward 09/10–29/10 já tinha sido visto (não conta). Contagem limpa desde 29/10 10h05: apenas 16 entradas, 50,0%.
- Todas as variantes de banca (Soros, stop win/loss, janela de horário) rodam sobre os mesmos sinais.
- Painel: ~15 telas/componentes, RLS por dono, calculadora de imposto, projeção por valor esperado, link público da banca, backup JSON.
