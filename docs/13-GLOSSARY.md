# 13 — Glossário (PT ↔ EN)

> Referência única para tradução de termos. Código usa **EN**; UI usa **PT-BR**. Quando o termo é universalmente conhecido em inglês (bluff, all-in), mantemos EN também em PT-BR.

## 1. Cartas (Cards)

| PT-BR (PokerStars) | Símbolo interno | Inglês | Notas |
|---|---|---|---|
| Ás | `A` | Ace | |
| Rei | `K` | King | |
| Dama | `Q` | Queen | "Dama" no client PT |
| Valete | `J` | Jack | |
| Dez | `T` | Ten | "10" pode aparecer; normalizar para `T` |
| Nove..Dois | `9..2` | Nine..Two | |
| Copas | `h` | Hearts | ♥ |
| Espadas | `s` | Spades | ♠ |
| Ouros | `d` | Diamonds | ♦ |
| Paus | `c` | Clubs | ♣ |

Representação interna: 2 chars (rank+suit), ex.: `Ah`, `Td`, `7c`.

## 2. Mãos (Hand rankings)

| PT-BR (PokerStars) | Constante interna | Inglês | Ordem |
|---|---|---|---|
| Royal Flush / Sequência Real | `ROYAL_FLUSH` | Royal Flush | 10 (top) |
| Sequência de Cor / Straight Flush | `STRAIGHT_FLUSH` | Straight Flush | 9 |
| Quadra | `FOUR_OF_A_KIND` | Four of a Kind | 8 |
| Full House | `FULL_HOUSE` | Full House | 7 |
| Flush | `FLUSH` | Flush | 6 |
| Sequência | `STRAIGHT` | Straight | 5 |
| Trinca | `THREE_OF_A_KIND` | Three of a Kind | 4 |
| Dois pares | `TWO_PAIR` | Two Pair | 3 |
| Par de X | `ONE_PAIR` | One Pair | 2 |
| Carta Alta | `HIGH_CARD` | High Card | 1 |

## 3. Ações (Actions)

| PT-BR (PokerStars) | Token interno | Inglês | Observações |
|---|---|---|---|
| desiste | `FOLD` | fold | |
| passa | `CHECK` | check | |
| iguala | `CALL` | call | |
| aposta | `BET` | bet | Sem preflop (apenas blind/ante) |
| aumenta X para Y | `RAISE` | raise | Y é o tamanho total |
| paga o small blind | `POST_SB` | post small blind | |
| paga o big blind | `POST_BB` | post big blind | |
| paga o ante | `POST_ANTE` | post ante | |
| paga small & big blinds | `POST_SB_BB` | post both blinds | Reentry/late |
| está ausente, dá fold | `FOLD_TIMEOUT` | sit-out fold | |
| está ausente | `SITTING_OUT` | sitting out | |
| volta da pausa | `RETURNS` | returns | |
| está sem fichas | `OUT_OF_CHIPS` | out of chips | |
| desconectou | `DISCONNECTED` | disconnected | |
| reconectou | `CONNECTED` | reconnected / is connected | |
| esgotou seu tempo | `TIMED_OUT` | timed out | |
| e está all-in | (sufixo) `ALLIN` | (is all-in) | Modificador, não ação |
| Mostra a [Xh Yh] | `SHOW` | shows | |
| não mostrou a mão | `MUCK` | mucks / didn't show | |
| recebeu N do pote | `COLLECTED` | collected from pot | |
| recebeu N do pote secundário | `COLLECTED_SIDE` | collected from side pot N | |
| Aposta não-igualada (N) devolvida para X | `UNCALLED` | uncalled bet | |
| ganha 2050 pontos | `WIN_POINTS` | wins points | Torneio reward |

## 4. Posições (Positions)

Derivadas (não vêm do arquivo, exceto BTN/SB/BB):

| Interno | PT-BR (UI) | Inglês | Aplica em |
|---|---|---|---|
| `BTN` | Botão | Button | Todas |
| `SB` | Small Blind | Small Blind | Todas (exceto HU onde BTN = SB) |
| `BB` | Big Blind | Big Blind | Todas |
| `UTG` | UTG | Under The Gun | 9-max, 6-max (1ª posição) |
| `UTG1` | UTG+1 | UTG+1 | 9-max |
| `UTG2` | UTG+2 / MP1 | UTG+2 / MP1 | 9-max |
| `MP` | MP | Middle Position | 6-max |
| `MP1` | MP1 | MP1 | 9-max |
| `MP2` | MP2 / LJ | LowJack | 9-max |
| `LJ` | LJ | LowJack | 9-max / 6-max raro |
| `HJ` | HJ | HiJack | 9-max, 6-max |
| `CO` | CO | Cutoff | Todas exceto HU |

## 5. Streets (Ruas)

| PT-BR (PokerStars) | Interno | Inglês |
|---|---|---|
| (não há header pré-flop, mas) `*** CARTAS DA MÃO ***` | `PREFLOP` | Preflop |
| `*** FLOP *** [Xx Yy Zz]` | `FLOP` | Flop |
| `*** TURN *** [Flop] [Tt]` | `TURN` | Turn |
| `*** RIVER *** [Flop+Turn] [Rr]` | `RIVER` | River |
| `*** SHOW DOWN ***` | `SHOWDOWN` | Showdown |
| `*** SUMÁRIO ***` | `SUMMARY` | Summary |

## 6. Tipos de Jogo

| PT-BR | Interno | Inglês |
|---|---|---|
| Torneio | `tournament` | Tournament (MTT/SNG) |
| Cash / Anel | `cash` | Cash Game / Ring |
| Sit & Go | `sng` | Sit & Go (subset de tournament no MVP) |
| Spin & Go | `spin` | Spin & Go (out of scope MVP) |
| Hold'em No Limit | `nlhe` | No Limit Hold'em |
| Hold'em Pot Limit | `plhe` | Pot Limit Hold'em (não MVP) |
| Omaha PL | `plo` | Pot Limit Omaha (não MVP) |

## 7. Métricas (Stats)

| Sigla | Nome PT-BR | Nome EN |
|---|---|---|
| VPIP | Voluntária no Pote | Voluntarily Put $ In Pot |
| PFR | Aumento Pré-Flop | Pre-Flop Raise |
| 3-Bet% | 3-Bet% | 3-Bet Percentage |
| Fold to 3-Bet% | Fold ao 3-Bet% | Fold to 3-Bet |
| AF | Fator de Agressão | Aggression Factor |
| WTSD% | Foi ao Showdown% | Went To ShowDown |
| W$SD% | Ganhou no Showdown% | Won $ at ShowDown |
| C-Bet% | Continuação Aposta% | Continuation Bet (v2) |
| Steal% | Roubo de Blind% | Steal Attempt (v2) |
| BB/100 | BB/100 | Big Blinds per 100 hands |
| ROI | ROI | Return on Investment |

## 8. Pote (Pot)

| PT-BR | Interno | EN |
|---|---|---|
| Pote principal | `main_pot` | Main pot |
| Pote secundário N | `side_pot_N` | Side pot N |
| Pote total | `pot_total` | Total pot |
| Aposta não-igualada | `uncalled_bet` | Uncalled bet |
| Rake | `rake` | Rake (cash only) |
| Lixo | n/a | Mucked |

## 9. Conta / Billing

| PT-BR (UI) | Interno | EN |
|---|---|---|
| Plano Grátis | `free` | Free plan |
| Plano Pro | `pro` | Pro plan |
| Assinatura | `subscription` | Subscription |
| Período atual | `current_period` | Current period |
| Cancelar no fim do período | `cancel_at_period_end` | |
| Inadimplente | `past_due` | Past due |
| Cobrança | `invoice` | Invoice |
| Portal do Cliente | `customer_portal` | Customer Portal |

## 10. Termos Gerais (Poker)

| PT-BR (aceito) | EN | Notas |
|---|---|---|
| Mão | Hand | Mão de poker; também usado para "hole cards" no contexto |
| Hole cards / cartas iniciais | Hole cards | "cartas iniciais" em PT formal |
| Board / mesa comunitária | Board | |
| Flop, Turn, River | Flop, Turn, River | Universal |
| Open, Open-Raise | Open / open-raise | Manter EN |
| Limp | Limp | Manter EN |
| Call / Iguala | Call | |
| Bluff / Blefe | Bluff | Ambos aceitos |
| Value bet | Value bet | Manter EN |
| All-in / Tudo | All-in | Manter EN |
| Showdown | Showdown | Manter EN |
| Stack | Stack | Manter EN |
| Effective stack | Effective stack | Manter EN |
| ICM | ICM | Independent Chip Model |
| Bubble / Bolha | Bubble | Ambos |
| Heads-up / Mano a mano | Heads-up (HU) | EN preferido |

## 11. Técnicos (Software)

| Termo | Definição rápida |
|---|---|
| HH | Hand History — arquivo texto exportado pelo site de poker |
| Hero | O usuário (jogador focal). No PokerStars, é o nome da conta logada. |
| Villain | Qualquer outro jogador. |
| Idempotency | Mesma operação repetida produz mesmo resultado. |
| RLS | Row Level Security (Postgres). |
| RBAC | Role-Based Access Control. |
| SSE | Server-Sent Events. |
| RSC | React Server Components. |
| LGPD | Lei Geral de Proteção de Dados (Brasil). |
| PII | Personally Identifiable Information. |
| OTel | OpenTelemetry. |
| PITR | Point-in-Time Recovery (DB). |
| MRR / ARR | Monthly / Annual Recurring Revenue. |
| NSM | North Star Metric. |
| ADR | Architecture Decision Record. |

## 12. Convenções de UI (PT-BR)

- Texto de botões: imperativo curto ("Enviar", "Cancelar", "Salvar alterações").
- Erros: mensagem clara em PT-BR + código (`HAND_NOT_FOUND`) escondido em "detalhes".
- Datas: formato `dd/mm/aaaa HH:mm` (UTC-3 BRT por padrão; toggle para UTC nas configs).
- Números: separador de milhar `.`; decimal `,` (padrão BR). Em logs/JSON da API: ponto decimal sempre.
- Moeda: `R$ 1.234,56`. Cents armazenados como BIGINT no DB.
