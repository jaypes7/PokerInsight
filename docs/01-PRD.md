# 01 — Product Requirements Document (PRD)

> **Audience**: humanos e agentes de IA precisando entender o **porquê** de cada feature.
> **Versão**: 0.1 (pré-MVP). Atualize a cada decisão de produto.

---

## 1. Problema

Jogadores de poker online (especialmente brasileiros, em micro-stakes na PokerStars) querem:

1. **Entender seu jogo** — onde estão perdendo dinheiro (leaks), quais posições têm pior winrate, contra quais oponentes.
2. **Acompanhar resultados ao longo do tempo** — gráfico de bankroll, ITM%, ROI por buy-in.
3. **Revisar mãos importantes** — replayer com decisões, para estudo solo ou com coach.
4. **Ter HUD ou stats agregadas sem instalar software pesado** — o ecossistema atual (PokerTracker 4, Hold'em Manager 3) é caro (USD 60-120+), Windows-first, e tem bugs com HH em PT-BR.

### Insights de mercado

- Mercado BR de poker online tem dezenas de milhares de jogadores ativos, especialmente em micro-stakes.
- A maioria não paga PT4/HM3 pelo preço/curva de aprendizado.
- Não existe alternativa SaaS web acessível **com parser nativo de PT-BR**.

---

## 2. Personas

### Persona 1 — "João Recreativo" (alvo do MVP)
- 28 anos, joga 2-3 noites por semana, 4-6 mesas em paralelo
- Buy-ins de $0.10 a $5.00, ~5k mãos/mês
- Quer saber: "estou no positivo este mês?", "como é meu winrate por posição?"
- Tem orçamento de até R$ 20-30/mês

### Persona 2 — "Maria Grinder" (próxima fase)
- 32 anos, semi-pro, 8-16 mesas, 50k+ mãos/mês
- Buy-ins de $2 a $50
- Quer: HUD em tempo real, leak finder profundo, range vs range
- Top-out R$ 80-150/mês se valer

### Persona 3 — "Coach Pedro" (V2)
- Coach que quer ver dashboards dos alunos
- Quer compartilhamento de mãos via link e comentários

---

## 3. Princípios de produto

1. **Privacidade absoluta.** O HH é dado sensível. Ninguém vê os dados de outro usuário, nunca.
2. **Importação simples.** Drag-and-drop ou upload de pasta. Sem instalação.
3. **Honestidade nas métricas.** Se uma stat tem amostra pequena, mostrar IC ou warning.
4. **Mobile-friendly.** Dashboard funciona em iPhone SE.
5. **Performance é UX.** Importar 50k mãos: <10 minutos. Abrir dashboard: <1s.
6. **Acessível em PT-BR primeiro.** Toda string da UI em português correto, sem traduções automáticas ruins.

---

## 4. Escopo do MVP (F1–F4)

### Dentro do escopo

- Cadastro/login com e-mail+senha e Google OAuth
- Upload manual de arquivos `.txt` de HH (PokerStars PT-BR)
- Parser para torneios e cash games NL Hold'em 9-max, 6-max e Heads-up (HU)
- Persistência completa: mãos, ações, board, pot, prize
- Cálculo de 7 estatísticas core: VPIP, PFR, 3-Bet%, Fold to 3-Bet%, AF (Aggression Factor), WTSD%, W$SD%
- Dashboard com gráfico de evolução de bankroll (torneios)
- Filtros: por data, buy-in, tipo de jogo, posição
- Lista de mãos importantes (biggest pots, all-ins)
- Replayer básico de mão (street por street)
- Planos free (até 5k mãos/mês) e Pro (ilimitado)
- Cobrança Stripe BR (cartão e Pix via Stripe BR)
- LGPD: política, opt-in, deleção total da conta sob demanda

### Fora do escopo do MVP (entram em V2+)

- HUD em tempo real (overlay sobre o cliente do PokerStars) — complexidade alta
- Suporte a outras salas (GGPoker, Partypoker, ACR, WPN) — arquitetura permite, mas não implementado
- Variantes além de NL Hold'em (Omaha, Stud)
- Sit & Go / Spin & Go avançado
- Range analysis vs range
- Hand sharing público com comentários
- Mobile app nativo (PWA é suficiente no início)
- Importação automática via watch-folder (requer client local)
- Coaching mode (compartilhar dashboard com terceiro)

---

## 5. User stories e critérios de aceite (MVP)

### US-001 — Cadastro
**Como** novo usuário, **quero** criar conta com e-mail e senha **para** começar a usar o produto.

**AC:**
- Validação: e-mail formato válido, senha mínimo 12 chars com 1 número e 1 letra maiúscula
- Confirmação por e-mail (link com expiração de 24h)
- Após confirmar, redirecionado para onboarding (tela de upload de HH)
- Bloqueio após 5 tentativas falhas de login em 15 min (rate limit por IP+email)

### US-002 — Upload de HH
**Como** usuário logado, **quero** fazer upload de um ou múltiplos arquivos `.txt` **para** que sejam analisados.

**AC:**
- Suporta arrastar-e-soltar e seletor de arquivo
- Suporta múltiplos arquivos (até 100 por vez)
- Tamanho máximo por arquivo: 50MB (free) / 200MB (pro)
- Quota total free: 5.000 mãos por janela de 30 dias
- Indicador de progresso em tempo real (status: enfileirado → parseando → importado / com erro)
- Detecta automaticamente arquivos já importados (hash do conteúdo) e ignora
- Mostra resumo: X mãos importadas, Y duplicadas, Z com erro (com link para detalhes)
- Não bloqueia a UI: parsing em background via Celery

### US-003 — Visualizar stats principais
**Como** usuário com dados importados, **quero** ver minhas 7 stats principais **para** entender meu jogo.

**AC:**
- Card por stat: valor numérico grande, "amostra: N mãos", warning se N<500
- Tooltip explica a fórmula
- Comparação implícita com benchmark de win-rate (texto: "VPIP saudável para 6-max NL2 fica entre 22-28%")
- Aplica filtros ativos

### US-004 — Filtros
**Como** usuário, **quero** filtrar minhas mãos **para** ver stats só do contexto que me interessa.

**AC:**
- Filtros: data (range), buy-in (range), tipo de jogo (MTT/SnG/Cash), número de jogadores na mesa (HU/6-max/9-max), posição (BTN/CO/MP/UTG/SB/BB)
- Combinação aditiva (AND)
- URL refletindo o estado dos filtros (compartilhável dentro do app, não público)
- "Limpar filtros" volta ao estado base

### US-005 — Replayer
**Como** usuário, **quero** revisar uma mão street por street **para** estudar minhas decisões.

**AC:**
- Mostra mesa, jogadores e stacks na pré-flop
- Botões: anterior / próximo / play (auto-avança 2s por ação)
- Cartas do hero sempre visíveis; cartas de oponentes só se houve showdown
- Animação da ação (chips deslizando para o pote)
- Indicador de pot odds (chip e %) ao tomar decisão do hero
- Atalhos de teclado: ← →  espaço

### US-006 — Gráfico de bankroll
**Como** usuário, **quero** ver a evolução do meu bankroll de torneios **para** acompanhar resultados.

**AC:**
- Eixo X: data ou número da mão; Eixo Y: lucro/prejuízo cumulativo em USD
- Toggle entre "all time", "este mês", "últimos 7 dias"
- Tooltip ao hover mostra: data, lucro do dia, torneios jogados
- Funciona em mobile (touch)

### US-007 — Assinar plano Pro
**Como** usuário free batendo o limite, **quero** assinar Pro **para** importar quantas mãos quiser.

**AC:**
- Página /pricing com comparativo claro free vs pro
- Stripe Checkout (cartão e Pix)
- Webhook do Stripe atualiza status do usuário
- E-mail de boas-vindas ao Pro
- Recibo enviado por e-mail (compliance fiscal BR)
- Cancelamento self-service na conta

### US-008 — Exportar / deletar dados (LGPD)
**Como** usuário, **quero** poder baixar todos os meus dados e/ou deletar minha conta **para** exercer meus direitos LGPD.

**AC:**
- Botão "Exportar meus dados" em Configurações → gera ZIP em background, e-mail com link de download (válido 7 dias)
- ZIP contém: perfil em JSON, mãos em JSON, arquivos HH originais em `.txt`
- Botão "Deletar minha conta" com confirmação textual (digitar "DELETAR")
- Deleção: soft delete imediato (acesso bloqueado), purga física após 30 dias (window para reverter via suporte)
- E-mail de confirmação de deleção

---

## 6. Métricas de sucesso (North-Star + apoio)

| Métrica | Definição | Meta MVP (90 dias após launch) |
|---------|-----------|-------------------------------|
| **NSM**: Mãos analisadas / usuário ativo / semana | Engajamento real | >2.000 |
| Usuários cadastrados | total | 500 |
| Usuários ativos semanais (WAU) | abriu dashboard nos últimos 7d | 150 |
| Conversão free → pro | % WAU que tem assinatura ativa | 5% |
| Churn mensal | % de pro que cancelam | <8% |
| Latência p95 do dashboard | tempo até interativo | <1.5s |
| Erros de parsing | mãos falhando / total importadas | <0.1% |

---

## 7. Restrições

- **Idioma do HH**: somente PT-BR no MVP. Suporte EN entra em V2.
- **Variante**: somente NL Hold'em.
- **Hardware do usuário**: web (Chrome/Safari/Firefox últimas 2 versões), sem PWA offline.
- **LGPD**: dados em data center com adequação à LGPD (preferência BR/região conforme).
- **Termos do PokerStars**: o usuário concorda que tem direito de exportar e analisar seus próprios HH (é permitido pelo Terms of Service do Stars, mas ferramentas terceiras NÃO podem fazer scraping ou client-side overlay no MVP).

---

## 8. Decisões abertas (precisa do humano)

| Decisão | Status | Quem decide |
|---------|--------|-------------|
| Preço final Pro mensal (proposta: R$ 19,90) | aberto | fundador |
| Logo e nome final (PokerInsight é provisório) | aberto | fundador |
| Provedor de hosting (Fly.io vs Hetzner vs AWS) | aberto | tech lead |
| Política de retenção: HH originais ficam guardados após parsing? | aberto | jurídico + tech |
| Free trial Pro (7 dias) ou só freemium? | aberto | growth |
