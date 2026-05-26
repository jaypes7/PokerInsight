# 05 — Especificação do Parser de HH (PokerStars PT-BR)

> **Documento crítico.** Erros aqui = stats erradas = produto morto.
> Toda mudança neste arquivo requer aprovação humana + atualização da bateria de **golden tests**.

---

## 1. Escopo

O parser deve processar arquivos `.txt` exportados pelo cliente PokerStars em **português brasileiro**, contendo uma ou mais mãos separadas por uma ou mais linhas em branco.

### Cobertura do MVP

- ✅ Torneios MTT e SnG (formato: `Torneio #...`)
- ✅ NL Hold'em
- ✅ Mesas 9-max, 6-max, heads-up (2-max)
- ✅ Variação de antes (a partir de Nível VII no exemplo)
- ✅ All-ins, side pots, uncalled bets
- ✅ Disconnects / sit out / time bank
- ✅ Showdown e mucked hands
- ⏳ Cash games (`Mão' (...) NL ...` sem torneio) — incluir, mesmo se features de UI vierem depois
- ❌ Variantes além de NLHE (out of scope MVP)

---

## 2. Arquitetura do parser

```
arquivo.txt
   │
   ▼
[FileSplitter]         separa mãos por linhas em branco; retorna iterator de blocos
   │
   ▼
[LineTokenizer]        converte cada linha em (line_no, raw, type, captures)
   │                   usando dispatch table de regex compiladas
   ▼
[HandAssembler]        consome tokens e monta uma estrutura intermediária (HandDraft)
   │                   detecta erros de invariantes (ex: balanço de fichas)
   ▼
[HandNormalizer]       traduz PT-BR → estrutura interna (action types, posições, ranks)
   │                   calcula derived fields (pot_before/after, position, etc.)
   ▼
[DomainHand]           objeto Pydantic v2 imutável que vai para o repositório
```

Cada estágio é **independente e testável**. O dispatcher de tokens é uma tabela; adicionar uma nova linha = uma entrada na tabela + um teste.

---

## 3. Estrutura geral de uma mão (PokerStars PT-BR)

Uma mão tem **8 seções**, sempre nesta ordem (algumas opcionais):

```
1. HEADER (1 linha)
   "Mão PokerStars #260820828710: Torneio #4000776344, $ 0.42+$ 0.08 USD Hold'em No Limit - Nível I (10/20) - 2026/05/15 19:01:22 ET"

2. TABLE (1 linha)
   "Mesa '4000776344 1' 9-max Lugar #1 é o botão"

3. SEATS (N linhas, uma por jogador)
   "Lugar 1: jaypes7 (1500 em fichas)"
   "Lugar 4: nagypapa (1500 em fichas) está sit out"

4. ANTES (opcional, N linhas)
   "jaypes7: coloca ante 25"

5. BLINDS (1-2 linhas)
   "corwil: paga o small blind 10"
   "Arte Pokera: paga o big blind 20"

6. HOLE_CARDS (1 cabeçalho + 1 linha para hero + ações pre-flop)
   "*** CARTAS DA MÃO ***"
   "jaypes7 recebe [Td Jc]"
   "<ações pré-flop>"

7. STREETS (0 a 3 seções: FLOP, TURN, RIVER)
   "*** FLOP *** [8h Qh Ad]"
   "<ações flop>"
   "*** TURN *** [8h Qh Ad] [2d]"
   "<ações turn>"
   "*** RIVER *** [8h Qh Ad 2d] [7s]"
   "<ações river>"

8. SHOWDOWN (opcional)
   "*** SHOW DOWN ***"
   "<linhas de mostra/esconde>"

9. SUMMARY
   "*** SUMÁRIO ***"
   "Total pote 140 | comissão 0"
   "Mesa [8h Qh Ad]"      ← board (se houve)
   "Lugar 1: jaypes7 (Botão) desistiu antes Flop (não apostou)"
   <...uma linha por jogador...>
```

> ⚠️ Algumas linhas "ruidosas" podem aparecer **entre ações** em qualquer street:
> - `"<player>: está sit out"`
> - `"<player>: está sem ligação"` / `"<player>: está ligado"`
> - `"<player> voltou"`
> - `"<player> gastou o tempo"` / `"<player> gastou o tempo enquanto estava sem ligação"`
>
> O parser deve **registrar mas não falhar** com essas linhas. Elas viram eventos `connectivity` que vão para um campo `meta_events` na mão (não entram na contagem de ações).

---

## 4. Gramática formal (informal EBNF)

```ebnf
file        ::= hand ( blank_line+ hand )* blank_line*

hand        ::= header table seat_line+ ante_line* blind_line+ holecards_block
                street_block* showdown_block? summary_block

header      ::= "Mão PokerStars #" hand_id ":" SP game_spec SP "-" SP date_time SP timezone NL

game_spec   ::= tournament_spec | cash_spec

tournament_spec ::= "Torneio #" tourney_id "," SP buyin "+" SP fee SP currency SP variant_name
                    SP "-" SP "Nível" SP level_roman SP "(" small_blind "/" big_blind ")"

cash_spec   ::= "(" stakes ") " variant_name        (* a definir com fixture de cash *)

variant_name ::= "Hold'em No Limit"                (* MVP *)

table       ::= "Mesa '" table_name "' " max_players "-max Lugar #" seat_num " é o botão" NL

seat_line   ::= "Lugar " seat_num ":" SP username SP "(" chips SP "em fichas)" [ SP "está sit out" ] NL

ante_line   ::= username ":" SP "coloca ante" SP amount NL

blind_line  ::= username ":" SP "paga o" SP ("small blind" | "big blind") SP amount NL

holecards_block ::= "*** CARTAS DA MÃO ***" NL
                    ( username SP "recebe" SP "[" card SP card "]" NL )    (* hero only *)
                    action_line*

street_block ::= ("*** FLOP ***" | "*** TURN ***" | "*** RIVER ***")
                 SP board_so_far [ SP new_card ] NL
                 action_line*

showdown_block ::= "*** SHOW DOWN ***" NL
                   ( show_line | mucks_line | collect_line | uncalled_line | tourney_finish_line )+

summary_block ::= "*** SUMÁRIO ***" NL
                  "Total pote" SP amount SP "|" SP "comissão" SP rake NL
                  [ "Mesa [" board_cards "]" NL ]
                  summary_seat_line+

action_line ::= username ":" SP action_verb [ SP amount [ "para" SP amount ] ] [ SP "e está all-in" ] NL
              | uncalled_line
              | collect_line
              | connectivity_line                              (* ignorável para stats *)

action_verb ::= "desiste" | "passa" | "iguala" | "aposta" | "aumenta"

uncalled_line ::= "Aposta não-igualada" SP "(" amount ")" SP "voltou para" SP username NL

collect_line ::= username SP "recebeu" SP amount SP "do pote" NL

tourney_finish_line ::= username SP "terminou o torneio em" SP ord SP "lugar" NL
                      | username SP "Acabou o torneio em" SP ord SP "lugar e recebeu" SP "$" SP money NL
                      | username SP "ganhou o torneio e recebeu" SP "$" SP money SP "- parabéns!" NL

(* todos opcionais *)
connectivity_line ::= username SP "gastou o tempo" [ SP "enquanto estava sem ligação" ] NL
                   |  username SP "está sit out" NL
                   |  username SP "está sem ligação" NL
                   |  username SP "está ligado" NL
                   |  username SP "voltou" NL
```

> Em **regex** vamos usar versões mais permissivas + verificações posteriores (não construir um EBNF parser combinator).

---

## 5. Dicionário de tradução PT-BR → tokens internos

### 5.1 Action verbs

| PT-BR | Token interno | Notas |
|-------|---------------|-------|
| `desiste` | `FOLD` | sem amount |
| `passa` | `CHECK` | sem amount |
| `iguala N` | `CALL` | amount obrigatório |
| `aposta N` | `BET` | amount obrigatório, contexto = primeira a colocar chips nessa street |
| `aumenta N1 para N2` | `RAISE` | `raise_by=N1`, `raise_to=N2` |
| `e está all-in` | flag `is_all_in=True` | aparece no final de qualquer linha de aposta/raise/call |
| `paga o small blind N` | `POST_BLIND` (sb) | |
| `paga o big blind N` | `POST_BLIND` (bb) | |
| `coloca ante N` | `POST_ANTE` | |
| `Aposta não-igualada (N) voltou para X` | `UNCALLED_RETURN` | refund |
| `X recebeu N do pote` | `COLLECT` | pode aparecer duas vezes em split pot |
| `mostra [c1 c2] (descrição)` | `SHOWS` | parse cartas e tipo de mão |
| `esconde a mão` / `escondeu as cartas [c1 c2]` | `MUCKS` | cartas podem aparecer ou não |
| `não mostra a mão` | `MUCKS` | sem cartas |

### 5.2 Hand rankings (PT-BR → EN)

| PT-BR | EN |
|-------|----|
| `Carta Alta X` | `HIGH_CARD` |
| `par de X` | `ONE_PAIR` |
| `dois pares, X e Y` | `TWO_PAIR` |
| `trinca, X` ou `trinca de X` | `THREE_OF_A_KIND` |
| `Sequência, X a Y` | `STRAIGHT` |
| `Flush, X carta mais alta` | `FLUSH` |
| `Full House, X com Y` | `FULL_HOUSE` |
| `Quadra, X` | `FOUR_OF_A_KIND` |
| `Straight Flush, X a Y` | `STRAIGHT_FLUSH` |
| `Royal Flush` | `ROYAL_FLUSH` |

> Tabela de tradução cobre o que observamos. **Se aparecer outra string**, o parser registra `UNKNOWN_TOKEN` em `import_errors` e **não** quebra a mão.

### 5.3 Card values (PT-BR ↔ EN ↔ rank)

| PT-BR | EN | rank char |
|-------|----|-----------| 
| Ás | Ace | `A` |
| Rei | King | `K` |
| Dama | Queen | `Q` |
| Valete | Jack | `J` |
| Dez | Ten | `T` |
| Nove | Nine | `9` |
| Oito | Eight | `8` |
| Sete | Seven | `7` |
| Seis | Six | `6` |
| Cinco | Five | `5` |
| Quatro | Four | `4` |
| Três | Three | `3` |
| Dois | Two | `2` |

Suits no formato bruto já são em inglês (`h` `d` `c` `s`).

### 5.4 Posições / outros

| PT-BR | Interno |
|-------|---------|
| `Botão` | `BTN` |
| `small blind` | `SB` |
| `big blind` | `BB` |
| `está sit out` | `sit_out=True` |
| `está sem ligação` | evento conectividade |
| `está ligado` | evento conectividade |
| `voltou` | evento conectividade |
| `gastou o tempo` | timeout (não conta como fold automático) |

### 5.5 Nível roman → small/big blind

Já vem nas duas formas: `"Nível VII (100/200)"`. O parser captura o roman E os números entre parênteses. Em caso de divergência, **prevalece o número** com warning.

---

## 6. Regex de referência (compiladas uma vez, módulo `parsers/pokerstars_ptbr/patterns.py`)

> ⚠️ Estas regex são o ponto de verdade. Cada uma DEVE ter teste em `tests/parsers/test_patterns.py` com **strings exatas observadas** e variações maliciosas.

```python
import re

# Sentinels
HAND_SEPARATOR = re.compile(r"^\s*$")
SECTION_FLOP   = re.compile(r"^\*\*\* FLOP \*\*\* \[(?P<board>(?:[2-9TJQKA][hdcs] ?){3})\]\s*$")
SECTION_TURN   = re.compile(r"^\*\*\* TURN \*\*\* \[(?P<prev>(?:[2-9TJQKA][hdcs] ?){3})\] \[(?P<card>[2-9TJQKA][hdcs])\]\s*$")
SECTION_RIVER  = re.compile(r"^\*\*\* RIVER \*\*\* \[(?P<prev>(?:[2-9TJQKA][hdcs] ?){4})\] \[(?P<card>[2-9TJQKA][hdcs])\]\s*$")
SECTION_HOLE   = re.compile(r"^\*\*\* CARTAS DA MÃO \*\*\*\s*$")
SECTION_SHOWDOWN = re.compile(r"^\*\*\* SHOW DOWN \*\*\*\s*$")
SECTION_SUMMARY  = re.compile(r"^\*\*\* SUMÁRIO \*\*\*\s*$")

# Header (torneio)
HEADER_TOURNEY = re.compile(
    r"^Mão PokerStars #(?P<hand_id>\d+): "
    r"Torneio #(?P<tournament_id>\d+), "
    r"\$ ?(?P<buyin>\d+\.\d+)\+\$ ?(?P<fee>\d+\.\d+) "
    r"(?P<currency>[A-Z]{3}) "
    r"(?P<variant>Hold'em No Limit) - "
    r"Nível (?P<level>[IVXLCDM]+) "
    r"\((?P<sb>\d+)/(?P<bb>\d+)\) - "
    r"(?P<date>\d{4}/\d{2}/\d{2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2}) "
    r"(?P<tz>\S+)\s*$"
)

# Mesa
TABLE = re.compile(
    r"^Mesa '(?P<table>[^']+)' "
    r"(?P<max>\d+)-max "
    r"Lugar #(?P<button_seat>\d+) é o botão\s*$"
)

# Seat list
SEAT = re.compile(
    r"^Lugar (?P<seat>\d+): (?P<name>.+?) \((?P<chips>\d+) em fichas\)(?P<sitout> está sit out)?\s*$"
)

# Antes
ANTE = re.compile(r"^(?P<name>.+?): coloca ante (?P<amount>\d+)\s*$")

# Blinds
BLIND = re.compile(r"^(?P<name>.+?): paga o (?P<kind>small blind|big blind) (?P<amount>\d+)\s*$")

# Hero hole cards
HERO_CARDS = re.compile(r"^(?P<name>.+?) recebe \[(?P<c1>[2-9TJQKA][hdcs]) (?P<c2>[2-9TJQKA][hdcs])\]\s*$")

# Ações
ACTION_FOLD  = re.compile(r"^(?P<name>.+?): desiste\s*$")
ACTION_CHECK = re.compile(r"^(?P<name>.+?): passa\s*$")
ACTION_CALL  = re.compile(r"^(?P<name>.+?): iguala (?P<amount>\d+)(?P<allin> e está all-in)?\s*$")
ACTION_BET   = re.compile(r"^(?P<name>.+?): aposta (?P<amount>\d+)(?P<allin> e está all-in)?\s*$")
ACTION_RAISE = re.compile(
    r"^(?P<name>.+?): aumenta (?P<by>\d+) para (?P<to>\d+)(?P<allin> e está all-in)?\s*$"
)

UNCALLED = re.compile(r"^Aposta não-igualada \((?P<amount>\d+)\) voltou para (?P<name>.+?)\s*$")
COLLECT  = re.compile(r"^(?P<name>.+?) recebeu (?P<amount>\d+) do pote\s*$")

SHOWS = re.compile(
    r"^(?P<name>.+?): mostra \[(?P<c1>[2-9TJQKA][hdcs]) (?P<c2>[2-9TJQKA][hdcs])\] "
    r"\((?P<desc>.+)\)\s*$"
)
MUCKS_HIDDEN = re.compile(r"^(?P<name>.+?): não mostra a mão\s*$")
MUCKS_REVEAL = re.compile(
    r"^(?P<name>.+?): (?:esconde a mão|escondeu as cartas \[(?P<c1>[2-9TJQKA][hdcs]) (?P<c2>[2-9TJQKA][hdcs])\])\s*$"
)

# Eventos de conectividade (ignorar nas stats, mas registrar)
CONN_SIT_OUT  = re.compile(r"^(?P<name>.+?) está sit out\s*$")
CONN_DISCONN  = re.compile(r"^(?P<name>.+?) está sem ligação\s*$")
CONN_RECONN   = re.compile(r"^(?P<name>.+?) está ligado\s*$")
CONN_RETURNED = re.compile(r"^(?P<name>.+?) voltou\s*$")
CONN_TIMEOUT  = re.compile(r"^(?P<name>.+?) gastou o tempo( enquanto estava sem ligação)?\s*$")

# Tournament finish
FINISH_PLACE = re.compile(r"^(?P<name>.+?) terminou o torneio em (?P<place>\d+)º lugar\s*$")
FINISH_PAID  = re.compile(
    r"^(?P<name>.+?) Acabou o torneio em (?P<place>\d+)º lugar e recebeu \$ ?(?P<amount>\d+\.\d+)\.?\s*$"
)
FINISH_WIN   = re.compile(
    r"^(?P<name>.+?) ganhou o torneio e recebeu \$ ?(?P<amount>\d+\.\d+) - parabéns!\s*$"
)

# Summary
SUM_TOTAL = re.compile(r"^Total pote (?P<pot>\d+) \| comissão (?P<rake>\d+)\s*$")
SUM_BOARD = re.compile(r"^Mesa \[(?P<board>(?:[2-9TJQKA][hdcs] ?){3,5})\]\s*$")
SUM_SEAT  = re.compile(
    r"^Lugar (?P<seat>\d+): (?P<name>.+?)"
    r"(?: \((?P<role>Botão|small blind|big blind)\))?"
    r"(?: \((?P<role2>Botão|small blind|big blind)\))?"
    r"(?P<outcome>.+)\s*$"
)
```

> 🧪 **Atenção**: em fixtures observamos a linha de summary com **dois roles entre parênteses** em mãos heads-up: `"Lugar 1: jaypes7 (Botão) (small blind) desistiu antes Flop"`. O regex acima captura isso via `role` e `role2`.

> 🧪 **Atenção**: usernames podem conter espaços (`Arte Pokera`) e símbolos. Sempre `+?` (não-guloso) para o nome.

---

## 7. Algoritmo do parser (pseudocódigo)

```python
def parse_file(text: str, parser_version: str) -> Iterable[HandDraft]:
    blocks = split_blocks(text)
    for raw_hand in blocks:
        try:
            yield parse_hand(raw_hand, parser_version)
        except ParseError as e:
            emit_error(raw_hand, e)


def parse_hand(raw_hand: str, parser_version: str) -> HandDraft:
    lines = raw_hand.splitlines()
    state = ParserState()

    state.header = parse_header(lines[0])
    state.table  = parse_table(lines[1])

    cursor = 2
    while cursor < len(lines) and SEAT.match(lines[cursor]):
        state.add_seat(parse_seat(lines[cursor])); cursor += 1

    # antes (opcional)
    while cursor < len(lines) and ANTE.match(lines[cursor]):
        state.add_ante(parse_ante(lines[cursor])); cursor += 1

    # blinds
    while cursor < len(lines) and BLIND.match(lines[cursor]):
        state.add_blind(parse_blind(lines[cursor])); cursor += 1

    # *** CARTAS DA MÃO ***
    assert_section(SECTION_HOLE, lines[cursor]); cursor += 1

    # hero cards (1 linha)
    state.hero_cards = parse_hero_cards(lines[cursor]); cursor += 1
    state.street = 'preflop'

    # ações preflop + street blocks
    cursor = parse_action_loop(state, lines, cursor)

    # showdown opcional
    if cursor < len(lines) and SECTION_SHOWDOWN.match(lines[cursor]):
        cursor += 1
        cursor = parse_showdown(state, lines, cursor)

    # summary obrigatório
    assert_section(SECTION_SUMMARY, lines[cursor]); cursor += 1
    cursor = parse_summary(state, lines, cursor)

    validate_invariants(state)  # ver §9
    return state.to_hand_draft(parser_version)
```

`parse_action_loop` itera consumindo ações; quando encontra `*** FLOP ***` / `TURN` / `RIVER` muda `state.street`. Ignora linhas de conectividade (registra em `state.meta_events`).

---

## 8. Mapeamento para estrutura interna (HandDraft)

```python
@dataclass(frozen=True)
class HandDraft:
    site: str = "pokerstars"
    site_hand_id: str
    site_tournament_id: str | None
    site_table_name: str
    game_type: Literal["tournament","cash"]
    variant: Literal["nlhe"]
    table_max_players: int
    button_seat: int
    hero_username: str
    hero_seat: int | None
    played_at: datetime  # UTC; converter ET → UTC
    buy_in_cents: int | None
    fee_cents: int | None
    currency: str
    level_name: str | None
    small_blind: int
    big_blind: int
    ante: int
    seats: list[PlayerDraft]
    actions: list[ActionDraft]
    board: list[str]
    pots: list[PotDraft]
    rake: int
    meta_events: list[MetaEvent]
    raw_text: str
```

### Conversão de timezone

O HH tem timestamps em **ET** (`19:01:22 ET`). Converter para UTC usando `zoneinfo.ZoneInfo("America/New_York")`. Documentar que ET = America/New_York (com DST automático). Persistir como `TIMESTAMPTZ` em UTC; coluna `timezone_at_play` guarda `"ET"`.

### Mapeamento de posição

A posição é **derivada** a partir do `button_seat` e do número de jogadores ativos. Algoritmo:

1. Calcular ordem de jogadores: começa pelo SB (seat após o button), depois BB, depois UTG, etc., em ordem horária.
2. Em 9-max: `SB, BB, UTG, UTG+1, UTG+2, MP, MP+1, CO, BTN`.
3. Em 6-max: `SB, BB, UTG, MP/LJ, HJ/CO, BTN`. Convenção: `SB, BB, UTG, MP, CO, BTN`.
4. Em HU: `BTN/SB, BB`. (No HU, o BTN posta o SB.)

Jogadores em `sit_out` que NÃO postam blinds **não recebem posição** (ficam fora da mão).

### Conversão de fichas → cents (torneios vs cash)

- **Torneio**: as "fichas" do HH são chips do torneio (não dinheiro). Armazenar como `small_blind` etc. em "chips" diretamente (`BIGINT`).
- **Cash**: linhas como `"paga o small blind 0.10"` (BR-PT real costuma trazer formato `$0.10` ou `0,10`). **Conversão**: multiplicar por 100 e arredondar com `Decimal`. Sem cash no exemplo, validar com fixtures novas.

### Cálculo do pot_before / pot_after

O pot evolui linearmente conforme as ações. Algoritmo:

```python
pot = sum(ante for ante in antes) + sum(blind for blind in blinds)
for action in actions_in_order:
    action.pot_before = pot
    if action.type in (BET, RAISE, CALL, POST_ANTE, POST_BLIND):
        pot += action.amount_contributed_to_pot
    elif action.type == UNCALLED_RETURN:
        pot -= action.amount
    action.pot_after = pot
```

Para **RAISE**, `amount_contributed_to_pot = raise_to - prev_committed_by_player_this_street`.

### Cálculo de side pots

Side pots aparecem quando ≥1 jogador all-in com stack menor que outros vivos. Algoritmo padrão:

1. Para cada street, agregar o total contribuído por jogador.
2. Pegar o menor stack em jogo entre quem chegou ao showdown / all-in.
3. Main pot = (esse stack) × N_jogadores_envolvidos.
4. Side pot N+1 = repetir com próximo menor.
5. Winners: o parser pode confiar nas linhas `recebeu ... do pote` do SHOWDOWN/SUMMARY, mas **deve validar** que a soma confere.

> ⚠️ Em alguns HH vimos linhas de "recebeu" sem indicação de qual pote. Estratégia: se houver múltiplas linhas `recebeu N do pote` para um mesmo jogador, somar. Se houver múltiplos jogadores ganhando, presumimos split em ordem (main → side1 → side2 ...).

---

## 9. Invariantes que o parser DEVE validar

Após montar a `HandDraft`, antes de retornar:

1. **Balanço de fichas**: soma de `(starting_stack - tudo que jogou) + (collected)` por jogador deve igualar `(stack final esperado)`. Usar como sanity check.
2. **Pot total**: `pot_total_from_summary == sum(amounts contribuídos) - sum(uncalled returns)`.
3. **Soma de coletados ≤ pot total**.
4. **Board**: o turn card é igual ao do flop + 1; idem river. Comparar contra summary `Mesa [...]`.
5. **Hero deve aparecer no SEATS**.
6. **Button seat ∈ seats**.
7. **Datas válidas** (ano entre 2000-2100).
8. **Sem duplicação de jogador no SEATS** (mesmo username dois seats = erro grave).
9. **Pelo menos 1 ação preflop** (mesmo que seja apenas fold/walk).
10. **Cartas únicas** no deck inteiro (board ∪ hole_cards de todos os mostrados).

Falha de qualquer invariante → `ParseError` com código (`CHIPS_IMBALANCE`, `POT_MISMATCH`, etc.) → linha vira `import_error` mas processamento continua com próxima mão.

---

## 10. Encoding e BOM

O arquivo do exemplo começa com `\ufeff` (BOM UTF-8). Estratégia: abrir com `encoding="utf-8-sig"` para descartar BOM automaticamente. Fallback: tentar `cp1252` se UTF-8 falhar (PokerStars histórico).

---

## 11. Performance esperada

Meta: **>1.000 mãos/segundo** em CPU única em arquivo médio (servidor t3.small).

Estratégias:
- Regex compiladas em nível de módulo
- Sem alocação de listas dispensáveis: usar iteradores
- Batch write no DB: 1.000 mãos por transação
- Parse pode rodar em **paralelo** (process pool) entre arquivos diferentes

Benchmark obrigatório: `make bench-parser` mede em fixture de 10k mãos.

---

## 12. Versionamento do parser

Cada `HandDraft` carrega `parser_version` (ex.: `"1.0.0"`). Banco persiste esse valor. Útil para:
- Reparse seletivo de mãos antigas quando bug é corrigido
- Análise de qual versão produziu qual dado

Bump em SemVer:
- **PATCH**: bugfix sem mudança de estrutura
- **MINOR**: novo token suportado, novo campo, retrocompatível
- **MAJOR**: mudança quebrando estrutura armazenada

---

## 13. Estratégia de testes

### 13.1 Golden tests

Para cada caso da §3 montar fixture mínima em `apps/api/tests/golden/`:
- `01_walk_bb.txt` — mão com walk no BB (todo mundo fold)
- `02_preflop_steal.txt` — raise + fold around
- `03_showdown_simple.txt` — vai até showdown, sem all-in
- `04_allin_with_uncalled.txt` — all-in com retorno de aposta não-igualada
- `05_multiway_sidepot.txt` — 3+ jogadores até showdown com side pot
- `06_split_pot.txt` — empate
- `07_disconnect_timeout.txt` — eventos de conectividade no meio
- `08_antes_present.txt` — antes (nível >= VII)
- `09_heads_up.txt` — 2-max
- `10_tournament_finish.txt` — última mão de torneio (com prêmio)

Cada um vem com `.expected.json` (a estrutura esperada). Teste:

```python
def test_golden(name):
    raw = (FIXTURES / f"{name}.txt").read_text(encoding="utf-8-sig")
    expected = json.loads((FIXTURES / f"{name}.expected.json").read_text())
    actual = parse_hand(raw, parser_version="1.0.0").model_dump()
    assert_jsonish_equal(actual, expected)
```

### 13.2 Property-based (Hypothesis)

Gera mãos aleatórias respeitando a gramática (ações válidas dada a sequência) e verifica que o parser:
- nunca crasha em entrada bem formada
- nunca aceita silenciosamente entrada malformada
- preserva invariantes

### 13.3 Fuzz testing

Mutação aleatória de fixtures válidas: trocar 1 char, remover 1 linha, duplicar linha. O parser deve sempre **falhar com erro registrado** e nunca crashar/loop infinito.

### 13.4 Regression tests

Toda vez que um usuário reporta uma mão que parseia errado:
1. Adicionar mão (anonimizada) em `fixtures/regression/`
2. Adicionar teste com a expectativa correta
3. Corrigir o bug
4. Commit incluindo a fixture

---

## 14. Anonimização de fixtures

Como vamos comitar HH em `packages/hh-fixtures/`, **anonimizar**:

- Substituir usernames reais por `Player1`, `Player2`, ...
- Manter "hero" como `Hero`
- Truncar IDs de torneio para um valor sintético consistente
- Manter datas (não há PII em data, mas se quiser, deslocar tudo em N dias mantendo deltas)

Script: `scripts/anonymize_hh.py FILE.txt > FILE.anonymized.txt`.

---

## 15. Erros conhecidos e edge cases

Lista a manter conforme aparecerem. Iniciar com:

1. **Username com espaço**: `Arte Pokera`. Regex `+?` resolve.
2. **Re-entrada de jogador**: `nagypapa voltou` no meio do flop após `sit out`. Não conta como ação.
3. **Dupla anotação em HU summary**: `(Botão) (small blind)`. Capturar ambos.
4. **`TheJazzNata gastou o tempo`** sem desistir imediatamente — outra linha `: desiste` virá em seguida. Não confundir timeout com fold automático.
5. **Ações pós-button shift**: em algumas mãos a numeração do seat pula (assento vazio). Algoritmo de posição precisa caminhar por **seats ativos**, não por número absoluto.
6. **Side pot com split**: dois jogadores empatam o side, três disputam o main. Validar com fixture dedicada.
7. **Acabou e ganhou linhas no SHOWDOWN**: `"corwil terminou o torneio em 9º lugar"` aparece após `recebeu ... do pote`. Tratar como linha de status.
8. **Pote 0**: walks com BB recebendo SB pequeno. Pode acontecer no início do torneio.

---

## 16. Saídas de erro

Códigos padronizados em `import_errors.error_code`:

| Code | Significado |
|------|-------------|
| `UNKNOWN_LINE` | Linha não bate com nenhum regex conhecido na posição esperada |
| `MISSING_HEADER` | Bloco começou sem `Mão PokerStars #` |
| `MISSING_SUMMARY` | Faltou `*** SUMÁRIO ***` |
| `CHIPS_IMBALANCE` | Balanço de fichas falhou |
| `POT_MISMATCH` | `Total pote` ≠ soma calculada |
| `CARD_DUPLICATE` | Carta apareceu 2x no deck |
| `BAD_TIMESTAMP` | Data não parseou |
| `BAD_ENCODING` | Arquivo não é UTF-8 nem CP1252 |
| `UNSUPPORTED_VARIANT` | Algo além de NLHE |
| `INTERNAL_ERROR` | Exceção não esperada (com stacktrace) |

Para todo erro, gravar `line_start`, `line_end`, `raw_excerpt` (até 2000 chars).
