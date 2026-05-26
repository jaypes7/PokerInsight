# 👀 Acompanhamento — O Que a IA Está Fazendo

> Você não precisa entender o código. Só precisa saber **em qual fase estamos** e **o que testar** quando cada fase terminar.

---

## Como usar

1. Quando rodar `make next`, veja qual task aparece (ex: `F1-PARSER-003`)
2. Encontre ela aqui pelo número da fase
3. Leia a coluna **"O que você vai ver"** pra saber se funcionou
4. Marque o ✅ quando testar e aprovar

---

## 🏗️ FASE F0 — Construindo a Base
> A IA está montando a estrutura do projeto, configurando testes e CI.
> **Você não vai ver nada no browser ainda.** É trabalho de bastidor.

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F0-REPO-001 | Cria a estrutura de pastas do projeto | Pastas `apps/`, `docs/`, `packages/`, `infra/` aparecem no repositório | [ ] |
| F0-REPO-002 | Configura regras de commit | Mensagens de commit erradas são bloqueadas automaticamente | [ ] |
| F0-REPO-003 | Cria templates do GitHub | Aba "Issues" e "Pull Requests" do GitHub ganham formulários | [ ] |
| F0-INFRA-001 | Cria ambiente de desenvolvimento local | `make dev` sobe banco, Redis e storage no seu computador | [ ] |
| F0-INFRA-002 | Cria ambiente de testes | Testes conseguem rodar sem precisar de internet | [ ] |
| F0-CI-001 | Cria pipeline de testes automáticos (parte 1) | No GitHub, aparece uma aba "Actions" com checklist verde | [ ] |
| F0-CI-002 | Cria pipeline de testes automáticos (parte 2) | Testes de integração e segurança passam no GitHub | [ ] |
| F0-API-001 | Cria o esqueleto do servidor | Acessar `http://localhost:8000/healthz` retorna `{"status":"ok"}` | [ ] |
| F0-API-002 | Configura variáveis de ambiente | Servidor não sobe se alguma variável obrigatória estiver faltando | [ ] |
| F0-API-003 | Configura logs do servidor | Terminal mostra logs em JSON quando você faz uma requisição | [ ] |
| F0-API-004 | Conecta o servidor ao banco de dados | Servidor conecta no Supabase sem erro | [ ] |
| F0-API-005 | Configura migrações do banco | Comando `make migrate` cria as tabelas no banco | [ ] |
| F0-WEB-001 | Cria o esqueleto do site | `http://localhost:3000` abre uma página em branco sem erro | [ ] |
| F0-WEB-002 | Configura segurança do site | Site bloqueia ataques básicos (invisível pra você, mas importante) | [ ] |
| F0-DOCS-001 | Publica documentação interna | (opcional) Docs acessíveis via URL pública | [ ] |

---

## 📦 FASE F1 — Parser + Upload
> A IA está construindo o motor principal: a parte que lê os arquivos `.txt` de mãos e salva no banco.
> No final desta fase você consegue **enviar um arquivo e ver as mãos salvas**.

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F1-DB-001 | Cria tabelas de usuários no banco | Tabela `users` aparece no painel do Supabase | [ ] |
| F1-DB-002 | Cria tabelas de mãos de poker | Tabelas `hands`, `actions`, `sessions` aparecem no Supabase | [ ] |
| F1-DB-003 | Cria tabelas de assinatura e billing | Tabelas `subscriptions`, `webhook_events` aparecem no Supabase | [ ] |
| F1-DB-004 | Cria dados de teste | Testes conseguem criar usuários e mãos falsos | [ ] |
| F1-PARSER-001 | Cria a estrutura do parser | Pasta `app/parser/` criada com arquivos vazios | [ ] |
| F1-PARSER-002 | Separa arquivo em mãos individuais | Arquivo com 80 mãos é dividido em 80 pedaços | [ ] |
| F1-PARSER-003 | Reconhece cada tipo de linha do arquivo | Linhas como "desiste", "iguala", "aumenta" são identificadas | [ ] |
| F1-PARSER-004 | Monta cada mão completa | Cada mão tem: jogadores, ações, cartas, pote | [ ] |
| F1-PARSER-005 | Calcula posições e estatísticas | Cada mão sabe quem era BTN, SB, BB e se o herói fez VPIP | [ ] |
| F1-PARSER-006 | Valida se a mão faz sentido | Mãos com erro (fichas não batem) são sinalizadas | [ ] |
| F1-PARSER-007 | Cria 10 arquivos de teste padrão | Pasta `packages/hh-fixtures/` tem 10 arquivos `.txt` de exemplo | [ ] |
| F1-PARSER-008 | Testa o parser com dados aleatórios | Parser passa em milhares de mãos geradas automaticamente | [ ] |
| F1-PARSER-009 | Cria ferramenta de anonimizar mãos | Comando que troca nomes reais por "Player1", "Player2" etc | [ ] |
| F1-PARSER-010 | Mede velocidade do parser | Parser processa mais de 1.000 mãos por segundo | [ ] |
| F1-REPO-001 | Cria camada de acesso ao banco | Código consegue salvar e buscar mãos no Supabase | [ ] |
| F1-STORAGE-001 | Conecta ao Cloudflare R2 | Arquivos `.txt` são enviados e guardados no R2 | [ ] |
| F1-WORKER-001 | Configura processamento em background | Tarefas pesadas rodam sem travar o servidor | [ ] |
| F1-WORKER-002 | Cria a tarefa de processar upload | Upload dispara processamento → mãos aparecem no banco | [ ] |
| F1-API-001 | Cria login e cadastro | `POST /v1/auth/register` e `/login` funcionam | [ ] |
| F1-API-002 | Cria refresh de sessão e reset de senha | Token de acesso renova sozinho, reset de senha funciona | [ ] |
| F1-API-003 | Cria endpoints de upload | Você consegue enviar um arquivo via API | [ ] |
| F1-API-004 | Cria endpoints de mãos | Você consegue listar e ver mãos via API | [ ] |
| **F1-QA-001** | **Teste completo do fluxo de upload** | **🎉 Cadastrar → Login → Enviar arquivo → Ver mãos na lista** | [ ] |

---

## 📊 FASE F2 — Estatísticas
> A IA está calculando as métricas de poker (VPIP, PFR, 3-Bet, etc.).
> No final desta fase as estatísticas aparecem via API.

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F2-STATS-001 | Cria estrutura de estatísticas | Pasta `app/stats/` criada | [ ] |
| F2-STATS-002 | Calcula VPIP e PFR | API retorna VPIP e PFR corretos | [ ] |
| F2-STATS-003 | Calcula 3-Bet% e Fold to 3-Bet% | API retorna essas métricas | [ ] |
| F2-STATS-004 | Calcula AF (Aggression Factor) | API retorna o AF | [ ] |
| F2-STATS-005 | Calcula WTSD% e W$SD% | API retorna essas métricas | [ ] |
| F2-STATS-006 | Filtra por data, tipo de jogo, etc. | Stats mudam quando você filtra por período | [ ] |
| F2-STATS-007 | Quebra stats por posição | Você vê VPIP separado por BTN, BB, UTG, etc. | [ ] |
| F2-STATS-008 | Coloca stats em cache | Segunda consulta retorna em menos de 100ms | [ ] |
| F2-API-001 | Cria endpoint `/v1/stats` | `GET /v1/stats` retorna todas as 7 métricas | [ ] |
| F2-API-002 | Cria endpoint de bankroll | `GET /v1/stats/bankroll` retorna gráfico de ganhos | [ ] |
| F2-WORKER-001 | Recalcula stats automaticamente à noite | Stats ficam atualizadas mesmo sem o usuário pedir | [ ] |

---

## 🖥️ FASE F3 — Interface Visual
> A IA está construindo o site que os usuários vão usar.
> **Esta é a fase mais visível** — você vai ver o produto tomando forma!

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F3-FRONT-001 | Cria sistema de autenticação no site | Login e logout funcionam no browser | [ ] |
| F3-FRONT-002 | Cria páginas de login, cadastro e senha | Formulários bonitos em português | [ ] |
| F3-FRONT-003 | Cria menu lateral e navegação | Site tem menu com Dashboard, Upload, Mãos, Stats, etc. | [ ] |
| F3-FRONT-004 | Cria página de upload com progresso | Drag & drop de arquivo com barra de progresso ao vivo | [ ] |
| F3-FRONT-005 | Cria lista de mãos com filtros | Tabela com todas as mãos, filtrável por data e tipo | [ ] |
| F3-FRONT-006 | Cria visualizador de mão (replayer) | Clicar em uma mão mostra as cartas e ações street a street | [ ] |
| F3-FRONT-007 | Cria dashboard de estatísticas | Cards com VPIP, PFR e os outros + gráficos | [ ] |
| F3-FRONT-008 | Cria gráfico de bankroll | Linha mostrando evolução dos ganhos ao longo do tempo | [ ] |
| F3-FRONT-009 | Cria página de configurações | Trocar senha, deletar conta, exportar dados | [ ] |
| **F3-QA-001** | **Testes completos da interface** | **🎉 Fluxo completo funciona no browser sem erros** | [ ] |

---

## 💳 FASE F4 — Pagamentos
> A IA está integrando o Stripe para cobrar pelo plano Pro.
> No final desta fase o sistema de assinatura funciona de verdade.

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F4-BILLING-001 | Configura produtos no Stripe | Plano Pro aparece no painel do Stripe | [ ] |
| F4-BILLING-002 | Cria fluxo de compra | Botão "Assinar Pro" leva para o checkout do Stripe | [ ] |
| F4-BILLING-003 | Cria recebimento de eventos do Stripe | Sistema atualiza o plano automaticamente após pagamento | [ ] |
| F4-BILLING-004 | Cria portal de gerenciamento | Usuário consegue cancelar a assinatura sozinho | [ ] |
| F4-BILLING-005 | Cria limites por plano | Usuário free vê aviso ao atingir 5.000 mãos | [ ] |
| F4-FRONT-001 | Cria páginas de planos e assinatura | Página `/planos` mostra Free vs Pro com preços | [ ] |
| **F4-QA-001** | **Teste completo de pagamento** | **🎉 Assinar → Pagar (cartão de teste) → Virar Pro** | [ ] |

---

## 🚀 FASE F5 — Lançamento
> A IA está configurando monitoramento, segurança final e colocando no ar.
> No final desta fase o produto está **ao vivo na internet**.

| # | O que a IA está fazendo | O que você vai ver quando terminar | ✅ |
|---|---|---|---|
| F5-OBS-001 | Configura rastreamento de erros e performance | Dashboard no Grafana mostrando métricas em tempo real | [ ] |
| F5-OBS-002 | Configura Sentry | Erros do site aparecem no painel do Sentry | [ ] |
| F5-OBS-003 | Cria dashboards de monitoramento | Gráficos de uso, erros, velocidade do sistema | [ ] |
| F5-OBS-004 | Configura alertas automáticos | Você recebe aviso no Slack/email se o site cair | [ ] |
| F5-SEC-001 | Revisão de segurança | Site passa na verificação do Mozilla Observatory | [ ] |
| F5-SEC-002 | Teste de invasão interno | Nenhum dado de um usuário fica visível para outro | [ ] |
| F5-PERF-001 | Teste de carga | Sistema aguenta 100 usuários simultâneos sem travar | [ ] |
| F5-PERF-002 | Otimização de banco de dados | Consultas pesadas ficam abaixo de 500ms | [ ] |
| F5-LGPD-001 | Páginas de privacidade e termos | `/privacidade` e `/termos` no ar em português | [ ] |
| F5-LGPD-002 | Exportação e exclusão de dados | Usuário consegue baixar ou deletar todos os próprios dados | [ ] |
| **F5-DEPLOY-001** | **🧑 VOCÊ: criar contas e colar variáveis** | **Siga o MEU-TODO.md partes 3 a 10** | [ ] |
| **F5-DEPLOY-002** | **Primeiro deploy em produção** | **🎉 `https://app.pokerinsight.com.br` está no ar!** | [ ] |
| F5-DEPLOY-003 | Teste de recuperação de desastre | Simula falha do banco e confirma que recupera em <1h | [ ] |
| F5-LAUNCH-001 | **🧑 VOCÊ: beta fechado** | Mandar link para 30-50 pessoas testarem | [ ] |
| F5-LAUNCH-002 | Documentação para usuários | Página de ajuda em português com guias de uso | [ ] |
| **F5-LAUNCH-003** | **Checklist final de lançamento** | **🎉 Produto lançado ao público!** | [ ] |

---

## 📍 Onde estamos agora

```
[ ] F0 — Base         (0/15)
[ ] F1 — Parser       (0/23)
[ ] F2 — Stats        (0/11)
[ ] F3 — Interface    (0/10)
[ ] F4 — Pagamentos   (0/7)
[ ] F5 — Lançamento   (0/16)
```

Atualize manualmente conforme as fases forem concluindo.

---

## 🧪 Como testar cada fase (sem saber programar)

### Ao final da F1
1. Abra `http://localhost:3000` (se ainda estiver local) ou a URL da Vercel
2. Crie uma conta
3. Vá em Upload
4. Envie o arquivo de mãos do PokerStars (aquele `.txt`)
5. Aguarde a barra de progresso terminar
6. Vá em "Mãos" — as mãos devem aparecer listadas

### Ao final da F3
Repita o teste acima e também:
1. Clique em uma mão — deve abrir o replayer mostrando as cartas
2. Vá em "Stats" — deve mostrar VPIP, PFR e outros números
3. Troque o filtro de data — os números devem mudar

### Ao final da F4
1. Vá em "Planos"
2. Clique em "Assinar Pro"
3. Use o cartão de teste do Stripe: `4242 4242 4242 4242`, qualquer data futura, qualquer CVC
4. Após pagar, seu plano deve mudar para Pro

### Ao final da F5
1. Acesse a URL de produção (não localhost)
2. Repita todos os testes acima
3. Se tudo funcionar: parabéns, o produto está no ar 🎉

---

## ❓ Dúvidas frequentes

**"A IA travou e não está avançando, o que faço?"**
Copia o erro que apareceu no terminal e manda aqui no Claude.

**"Não sei se a task terminou"**
Rode `make status` no terminal — mostra o progresso atual.

**"A IA fez algo errado"**
Rode `make dry --task F0-REPO-001` (com o ID da task) para ver o que ela recebeu como instrução. Manda o output aqui se não entender.

**"Quero ver o que a IA está fazendo agora"**
O arquivo `.agent_prompt.md` na pasta do projeto tem o contexto completo que foi passado para ela.
