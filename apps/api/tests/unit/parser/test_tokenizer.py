from app.parser.tokenizer import PATTERNS, tokenize


def test_all_reference_patterns_have_positive_fixture_examples() -> None:
    examples = {
        "section_hole": "*** CARTAS DA MÃO ***",
        "section_flop": "*** FLOP *** [2h 7d Ks]",
        "section_turn": "*** TURN *** [2h 7d Ks] [3c]",
        "section_river": "*** RIVER *** [2h 7d Ks 3c] [9s]",
        "section_showdown": "*** SHOW DOWN ***",
        "section_summary": "*** SUMÁRIO ***",
        "header_tourney": (
            "Mão PokerStars #260820828710: Torneio #4000776344, $ 0.42+$ 0.08 USD "
            "Hold'em No Limit - Nível I (10/20) - 2026/05/15 19:01:22 ET"
        ),
        "table": "Mesa '4000776344 1' 9-max Lugar #1 é o botão",
        "seat": "Lugar 1: Arte Pokera (1500 em fichas)",
        "ante": "Hero: coloca ante 25",
        "blind": "Hero: paga o small blind 10",
        "hero_cards": "Hero recebe [Td Jc]",
        "action_fold": "Hero: desiste",
        "action_check": "Hero: passa",
        "action_call": "Hero: iguala 20 e está all-in",
        "action_bet": "Hero: aposta 20 e está all-in",
        "action_raise": "Hero: aumenta 40 para 60 e está all-in",
        "uncalled": "Aposta não-igualada (10) voltou para Hero",
        "collect": "Hero recebeu 20 do pote",
        "shows": "Hero: mostra [Ah Ad] (par de Ás)",
        "mucks_hidden": "Hero: não mostra a mão",
        "mucks_reveal": "Hero: escondeu as cartas [Ah Ad]",
        "conn_sit_out": "Hero está sit out",
        "conn_disconn": "Hero está sem ligação",
        "conn_reconn": "Hero está ligado",
        "conn_returned": "Hero voltou",
        "conn_timeout": "Hero gastou o tempo enquanto estava sem ligação",
        "finish_place": "Hero terminou o torneio em 2º lugar",
        "finish_paid": "Hero Acabou o torneio em 2º lugar e recebeu $ 1.00.",
        "finish_win": "Hero ganhou o torneio e recebeu $ 1.00 - parabéns!",
        "sum_total": "Total pote 20 | comissão 0",
        "sum_board": "Mesa [2h 7d Ks 3c 9s]",
        "sum_seat": "Lugar 1: Hero (Botão) (small blind) mostrou [Ah Ad] e ganhou",
    }
    pattern_names = {name for name, _pattern in PATTERNS}
    assert set(examples) == pattern_names
    for kind, line in examples.items():
        assert tokenize(line).kind == kind


def test_unknown_line_token_does_not_raise() -> None:
    token = tokenize("linha inventada sem significado")
    assert token.kind == "unknown"
