# 06 — Especificação de estatísticas de poker

> Fórmulas exatas das 7 estatísticas core do MVP + roadmap. Todas devem ter teste com cenários numéricos no `tests/stats/`.

---

## 1. Terminologia universal

- **Mão (hand)**: uma rodada completa, do dealing ao showdown/folding.
- **Oportunidade**: jogador estava elegível para fazer a ação (não foi forçado por blind, não estava fora da mão).
- **Voluntário**: o jogador colocou fichas por escolha (não obrigado por blind).
- **Sample size**: número de mãos no denominador. Toda stat deve vir junto com seu sample.

---

## 2. As 7 stats do MVP

### 2.1 VPIP — Voluntarily Put $ In Pot

**Definição**: percentual de mãos em que o jogador voluntariamente colocou dinheiro no pote pré-flop.

**Numerador**: # mãos onde o jogador fez **call**, **bet** ou **raise** pré-flop (excluindo blind e ante obrigatórios; **walk** não conta para o BB).

**Denominador**: # mãos onde o jogador teve **oportunidade pré-flop**.
- Oportunidade = jogador foi dealt-in e teve chance de agir
- Mãos onde o jogador **só postou BB e ninguém limpou** (walk) → ele NÃO teve oportunidade voluntária → exclui do denominador? **Convenção PokerInsight**: incluímos no denominador mas não no numerador (consistente com PT4 e HM3). Isso reflete uma realidade tight-passive.
  
  > Há divergência na literatura. Documentar nossa escolha e calcular a stat consistentemente.

**Fórmula**:
```
VPIP = 100 * voluntary_preflop_money / opportunities_preflop
```

**Exemplo**: 100 mãos, em 25 fez call/bet/raise pré (não considerando o BB obrigatório). VPIP = 25%.

**Sample mínimo recomendado para significância**: 500 mãos (mostrar warning abaixo disso).

---

### 2.2 PFR — Pre-Flop Raise

**Definição**: percentual de mãos em que o jogador fez raise (ou re-raise) pré-flop.

**Numerador**: # mãos onde o jogador fez **bet/raise** pré-flop. (Open-raise, isolations, 3-bet, 4-bet, etc.)

**Denominador**: mesmo de VPIP (oportunidades pré-flop).

**Fórmula**:
```
PFR = 100 * preflop_raise_or_better / opportunities_preflop
```

> `PFR ≤ VPIP` sempre (raise é um subconjunto de "put $ in pot"). Validar como invariante.

---

### 2.3 3-Bet% (Three Bet)

**Definição**: percentual de mãos em que o jogador 3-betou pré-flop quando teve oportunidade.

**Numerador**: # mãos onde o jogador re-raised pré-flop após exatamente UM raise prévio (i.e., raise = 3-bet).
- O big blind também pode 3-betar.
- All-in pré que vem por cima de um raise conta como 3-bet.

**Denominador**: # mãos onde houve **um raise pré-flop antes do jogador agir** E o jogador ainda estava na mão para reagir.

**Fórmula**:
```
3-Bet% = 100 * 3bet_actions / 3bet_opportunities
```

**Detalhes**:
- "**Bet**" no big blind funciona como contribuição mas não como raise; o cold-call de open não é 3-bet, é uma chamada.
- 4-bet, 5-bet, etc. NÃO contam para 3-bet (têm stats próprias em V2).

---

### 2.4 Fold to 3-Bet%

**Definição**: percentual de vezes que o jogador (sendo o **open-raiser original**) folda quando enfrenta um 3-bet pré.

**Numerador**: # mãos onde o jogador abriu o pote pré-flop, foi 3-betado, e foldou.

**Denominador**: # mãos onde o jogador abriu o pote pré-flop e enfrentou 3-bet.

**Fórmula**:
```
Fold_to_3bet = 100 * fold_after_being_3bet / faced_3bet_after_open
```

> Note: jogador pode call/4bet/fold após levar 3-bet. Aqui contamos só fold.

---

### 2.5 AF — Aggression Factor (post-flop)

**Definição**: razão entre ações agressivas (bet + raise) e ações passivas (call) **pós-flop**.

**Fórmula**:
```
AF = (post_flop_bets + post_flop_raises) / post_flop_calls
```

- **NÃO inclui** check ou fold no denominador.
- Pode ser infinito se calls = 0 (representar como `∞` ou `>20` no UI quando sample pequeno).
- Convenção: separar AF por street (flop/turn/river) em V2; no MVP é agregado.

**Interpretação**:
- AF < 1: passivo
- 1 ≤ AF < 2: equilibrado
- AF ≥ 2: agressivo

---

### 2.6 WTSD% — Went to ShowDown

**Definição**: percentual de mãos onde o jogador chegou ao showdown, dado que viu o flop.

**Numerador**: # mãos onde o jogador viu o river E mostrou (ou seria forçado a mostrar, i.e., chegou ao showdown).

**Denominador**: # mãos onde o jogador viu o flop.

**Fórmula**:
```
WTSD = 100 * went_to_showdown / saw_flop
```

---

### 2.7 W$SD% — Won Money at ShowDown

**Definição**: percentual de showdowns em que o jogador ganhou (ao menos algum dinheiro do pote, contando ties como ganho).

**Numerador**: # showdowns em que o jogador foi pago em algum pote (main ou side).

**Denominador**: # showdowns onde o jogador esteve.

**Fórmula**:
```
W$SD = 100 * showdowns_won / showdowns_total
```

---

## 3. Cálculos derivados

### 3.1 Win-rate

**Tournaments**: ROI% = `(sum_payouts - sum_buyins_with_fees) / sum_buyins_with_fees * 100`.
**Cash games**: BB/100 = `net_profit_in_BB / hands * 100`.

### 3.2 ITM% (In The Money)

Para torneios: `# torneios onde pagou ≥ buy-in / # torneios jogados * 100`.

### 3.3 Net por sessão

Soma do `hero_net_cents` por sessão.

---

## 4. Como detectar eventos no parser

Para cada mão, ao processar as ações, computar e armazenar em `actions` ou `hands` os seguintes flags:

| Flag | Definição |
|------|-----------|
| `hero_saw_flop` | hero não foldou pré-flop |
| `hero_saw_turn` | hero ainda na mão depois do flop |
| `hero_saw_river` | idem turn |
| `hero_went_to_showdown` | hero chegou ao river e a mão foi a showdown |
| `hero_won_at_showdown` | hero recebeu algum pote no showdown |
| `hero_vpip` | hero contribuiu voluntariamente no pré |
| `hero_pfr` | hero fez bet/raise pré |
| `hero_3bet` | hero fez 3-bet pré |
| `hero_faced_3bet` | hero abriu o pote pré e levou 3-bet |
| `hero_folded_to_3bet` | hero foldou após faced_3bet |
| `hero_postflop_bets` | contagem |
| `hero_postflop_raises` | contagem |
| `hero_postflop_calls` | contagem |

Persistir esses flags **denormalizados** na tabela `hands` (várias colunas booleanas/inteiras) para queries de agregação rápidas (sem JOIN com `actions`):

```sql
ALTER TABLE hands ADD COLUMN h_saw_flop BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_saw_turn BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_saw_river BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_went_to_sd BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_won_at_sd BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_vpip BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_pfr BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_three_bet BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_faced_three_bet BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_folded_to_three_bet BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_pf_open BOOLEAN DEFAULT false;
ALTER TABLE hands ADD COLUMN h_postflop_bets SMALLINT DEFAULT 0;
ALTER TABLE hands ADD COLUMN h_postflop_raises SMALLINT DEFAULT 0;
ALTER TABLE hands ADD COLUMN h_postflop_calls SMALLINT DEFAULT 0;
```

Com isso, calcular VPIP de um usuário é:
```sql
SELECT
  100.0 * SUM(h_vpip)::float / NULLIF(COUNT(*),0) AS vpip,
  COUNT(*) AS sample
FROM hands
WHERE user_id = $1
  AND played_at >= $2 AND played_at < $3;
```

Latência alvo: <50ms para até 1M mãos por usuário (com índices).

---

## 5. Filtros aplicáveis

Toda stat respeita filtros do usuário:
- Date range (`played_at`)
- Buy-in range (`buy_in_cents`)
- Game type (`game_type`)
- Table size (`table_max_players`)
- Posição (`hero_position`)
- Session ID

Implementação: query builder cuida de adicionar WHERE clauses; chave de cache (`stats_snapshots.scope_hash`) inclui filtros.

---

## 6. Estratégia de cache

1. **L1**: Redis com chave `stats:user:<id>:scope:<hash>`, TTL 1h.
2. **L2**: Postgres `stats_snapshots` com `computed_at`; reaproveitado em todas as réplicas.

Invalidação:
- Ao final de cada import bem sucedido, **flush** das chaves do usuário em Redis e DELETE em `stats_snapshots`.
- Pode demorar ~30s para o usuário ver dados novos refletidos.

---

## 7. Testes obrigatórios

Para cada stat, criar `tests/stats/test_<stat>.py` com:

1. **Caso trivial**: 1 mão, valor esperado.
2. **Caso composto**: 10 mãos mistas, valor esperado.
3. **Edge cases**:
   - Walk no BB
   - Hero não dealt (sit out) — não conta
   - All-in pré
   - Side pot dividido
4. **Property test**: VPIP ≥ PFR sempre; W$SD ∈ [0,100]; AF ≥ 0.
5. **Performance**: 1M mãos sintéticas, query < 200ms.

---

## 8. Roadmap V2 de stats

- **C-Bet%** (continuation bet flop) e **Fold to C-Bet%**
- **4-Bet%** / **5-Bet%**
- **Steal%** (BTN/CO open quando fold-around até lá) e **Fold to Steal%**
- **Squeeze%**
- **AF por street** (flop/turn/river separados)
- **All-in EV** (sklansky bucks)
- **Total Aggression Frequency (AFq)** — alternativa ao AF
- **Win-rate by hole-card ranking** (e.g., AA, KK, AK)
- **Position-based table** (matriz 13x13 com cores)

---

## 9. Decisões de produto sobre UI das stats

- Mostrar valor com 1 casa decimal (`23.4%`).
- Sample size **sempre visível**.
- Tooltip com fórmula + link para este doc.
- Cor (não vital): verde se dentro do "saudável" para o tipo de jogo; sem julgamentos morais; meramente informativo.
- "Saudável" por enquanto é fixo por tabela conhecida; pode virar dinâmico via dados agregados anônimos em V2.

| Stat | 6-max NL micro | 9-max NL micro |
|------|---------------|----------------|
| VPIP | 22-28% | 16-22% |
| PFR  | 16-22% | 12-18% |
| 3-Bet% | 4-8% | 3-6% |
| Fold to 3-Bet% | 50-65% | 55-70% |
| AF | 1.5-3.0 | 1.5-3.0 |
| WTSD% | 25-32% | 22-30% |
| W$SD% | 48-55% | 48-55% |

Estes são **referenciais**, não verdade absoluta.
