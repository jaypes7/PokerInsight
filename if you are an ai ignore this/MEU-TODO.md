# 📋 Seu Guia — O Que Você Precisa Fazer

> Enquanto o Codex cuida do código, **você cuida das contas e das decisões**.
> Siga esta lista em ordem. A maioria é só criar conta em site e copiar uma chave.

---

## 🖥️ Parte 1 — Preparar o computador
> Faça isso uma vez só, antes de qualquer coisa.

- [ x] **Instalar Node.js**
  Acesse → https://nodejs.org → baixe a versão **LTS** → instale normalmente
  Teste: abra o PowerShell e digite `node --version` (tem que aparecer um número)

- [ x] **Instalar Python**
  Acesse → https://python.org/downloads → baixe a versão mais recente
  ⚠️ Na tela de instalação, marque **"Add Python to PATH"** antes de clicar em Install
  Teste: `python --version`

- [ x] **Instalar Git**
  Acesse → https://git-scm.com → baixe e instale (pode clicar "Next" em tudo)
  Teste: `git --version`

- [ x] **Instalar pnpm**
  No PowerShell: `npm install -g pnpm`
  Teste: `pnpm --version`

- [x ] **Instalar o Codex CLI**
  No PowerShell: `npm install -g @openai/codex`
  Depois: `codex login` (vai abrir o browser pra você entrar com sua conta OpenAI)
  Teste: `codex --version`

- [ x] **Instalar o make**
  No PowerShell (se ainda não fez): `choco install make`
  Teste: `make --version`

---

## 🐙 Parte 2 — Criar o repositório no GitHub
> O Codex vai trabalhar dentro desse repositório.

- [ x] Acesse → https://github.com → crie uma conta se não tiver
- [x ] Clique em **"New repository"**
  - Nome: `pokerinsight` (ou o nome que quiser)
  - Deixe **Privado** por enquanto
  - **Não** marque "Initialize with README"
  - Clique em **"Create repository"**
- [x ] Copie a URL do repositório (ex: `https://github.com/seuusuario/pokerinsight.git`)
- [ x] No PowerShell, dentro da pasta `poker-saas-docs`:
  ```
  git init
  git remote add origin https://github.com/seuusuario/pokerinsight.git
  git add .
  git commit -m "chore: documentação inicial"
  git push -u origin main
  ```

---

## 🗄️ Parte 3 — Criar o banco de dados (Supabase)
> Faça isso antes da fase F1 começar.

- [x ] Acesse → https://supabase.com → crie uma conta
- [ x] Clique em **"New project"**
  - Organization: a que aparecer
  - Name: `pokerinsight`
  - Database Password: crie uma senha forte e **salve em algum lugar seguro**
  - Region: escolha **East US (North Virginia)** — mais próximo do BR disponível
  - Clique em **"Create new project"** e aguarde ~2 minutos
- [ ] Quando terminar, vá em **Settings → Database → Connection string → URI**
  - Copie a string que começa com `postgresql://...`
  - Guarde ela — vai precisar depois
- [ ] Vá em **Settings → API**
  - Copie o **service_role key** (o secreto, não o anon)
  - Guarde também

---

## ⚡ Parte 4 — Criar o Redis (Upstash)
> Cache do sistema. É grátis e leva 2 minutos.

- [x ] Acesse → https://upstash.com → crie uma conta (pode entrar com GitHub)
- [ x] Clique em **"Create Database"**
  - Name: `pokerinsight`
  - Type: **Regional**
  - Region: **US-East-1**
  - Clique em **"Create"**
- [ ] Na página do banco criado, copie a **"UPSTASH_REDIS_REST_URL"** e o **"UPSTASH_REDIS_REST_TOKEN"**
  - Guarde os dois

---

## 🗃️ Parte 5 — Criar o storage de arquivos (Cloudflare R2)
> Aqui ficam guardados os arquivos de mão (.txt) enviados pelos usuários.

- [ x] Acesse → https://cloudflare.com → crie uma conta
- [ x] No menu lateral: **R2 Object Storage → Create bucket**
  - Name: `pokerinsight`
  - Clique em **"Create bucket"**
- [ ] Vá em **R2 → Manage R2 API Tokens → Create API Token**
  - Permissions: **Object Read & Write**
  - Clique em **"Create API Token"**
  - Copie o **Access Key ID** e o **Secret Access Key** — aparecem só uma vez!
- [ ] Copie também o **Account ID** que fica no canto direito da tela de R2

---

## 📧 Parte 6 — Criar o serviço de e-mail (Resend)
> Para enviar e-mails de confirmação de conta, reset de senha, etc.

- [ ] Acesse → https://resend.com → crie uma conta
- [ ] Vá em **API Keys → Create API Key**
  - Name: `pokerinsight`
  - Clique em **"Add"**
  - Copie a chave que começa com `re_...` — aparece só uma vez!

---

## 💳 Parte 7 — Criar a conta de pagamentos (Stripe)
> Para cobrar pelo plano Pro. Começa em modo de teste, sem dinheiro de verdade.

- [ ] Acesse → https://stripe.com → crie uma conta
- [ ] No painel, no topo, confirme que está em **"Test mode"** (tem um toggle)
- [ ] Vá em **Developers → API Keys**
  - Copie a **Publishable key** (começa com `pk_test_...`)
  - Copie a **Secret key** (começa com `sk_test_...`)
  - Guarde os dois

---

## 🚀 Parte 8 — Configurar o deploy do Frontend (Vercel)
> O site que os usuários vão acessar.

- [ ] Acesse → https://vercel.com → crie uma conta (pode entrar com GitHub)
- [ ] Clique em **"Add New Project"**
  - Conecte o GitHub e selecione o repositório `pokerinsight`
  - Em **"Root Directory"**, coloque: `apps/web`
  - Clique em **"Deploy"**
- [ ] Quando terminar, vá em **Settings → Domains**
  - Anote a URL gerada (algo como `pokerinsight.vercel.app`) — é o seu site!

---

## 🛤️ Parte 9 — Configurar o deploy do Backend (Railway)
> O servidor que processa as mãos e calcula as estatísticas.

- [ x] Acesse → https://railway.app → crie uma conta (pode entrar com GitHub)
- [ x] Clique em **"New Project" → "Deploy from GitHub repo"**
  - Selecione `pokerinsight`
- [x ] Vai criar um serviço automaticamente. Clique nele.
- [ ] Vá em **Settings → Networking → Generate Domain**
  - Anote a URL gerada (ex: `pokerinsight-production.up.railway.app`)
- [ ] Agora vá em **Variables** e adicione uma por uma as variáveis abaixo.
  Cole os valores que você foi guardando nos passos anteriores:

```
DATABASE_URL          → a string do Supabase (postgresql://...)
REDIS_URL             → a URL do Upstash
R2_ACCOUNT_ID         → o Account ID do Cloudflare
R2_ACCESS_KEY_ID      → o Access Key do R2
R2_SECRET_ACCESS_KEY  → o Secret Key do R2
R2_BUCKET_NAME        → pokerinsight
RESEND_API_KEY        → a chave do Resend (re_...)
STRIPE_SECRET_KEY     → a chave secreta do Stripe (sk_test_...)
APP_ENV               → production
API_URL               → a URL do Railway (https://pokerinsight-xxx.up.railway.app)
APP_URL               → a URL da Vercel (https://pokerinsight.vercel.app)
```

- [ ] Também adicione na **Vercel** (Settings → Environment Variables):
```
NEXT_PUBLIC_API_URL              → a URL do Railway
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY → a chave pública do Stripe (pk_test_...)
```

---

## 🔑 Parte 10 — Gerar as chaves de segurança JWT
> Necessário para o sistema de login funcionar.

- [ ] No PowerShell, dentro da pasta do projeto:
  ```
  make gen-jwt-keys
  ```
  Isso vai criar dois arquivos: `jwt_private.pem` e `jwt_public.pem`
- [ ] Abra cada arquivo com o bloco de notas e copie o conteúdo
- [ ] Cole no Railway como variáveis:
  ```
  JWT_PRIVATE_KEY → conteúdo do jwt_private.pem
  JWT_PUBLIC_KEY  → conteúdo do jwt_public.pem
  ```
- [ ] ⚠️ **Delete os dois arquivos .pem do seu computador depois** — eles não podem ficar salvos nem no repositório

---

## ✅ Parte 11 — Verificar se tudo está funcionando

- [ ] Acesse a URL da Vercel — o site deve aparecer
- [ ] Acesse `[URL do Railway]/healthz` — deve aparecer `{"status":"ok"}`
- [ ] Tente criar uma conta no site
- [ ] Tente fazer upload de um arquivo de mão

---

## 📱 Parte 12 — Lançamento

- [ ] Troque o Stripe de **Test mode** para **Live mode** (no painel do Stripe)
  - Vai precisar preencher dados bancários para receber pagamentos
  - Atualize as chaves no Railway (`sk_live_...` e `pk_live_...`)
- [ ] Configure um domínio próprio na Vercel (ex: `app.pokerinsight.com.br`)
- [ ] Mande o link para os primeiros usuários beta testarem

---

## 🗝️ Cofre de Senhas
> Guarde todos os dados abaixo em um gerenciador de senhas (Bitwarden, 1Password, etc.)

| O que é | Onde fica | Já salvei? |
|---|---|---|
| Senha do banco (Supabase) | Supabase → Settings | [ ] |
| DATABASE_URL | Supabase → Settings → Database | [ ] |
| Supabase service_role key | Supabase → Settings → API | [ ] |
| Upstash Redis URL + Token | Upstash → painel do DB | [ ] |
| Cloudflare Account ID | Cloudflare → R2 | [ ] |
| R2 Access Key ID | Cloudflare → R2 → API Tokens | [ ] |
| R2 Secret Access Key | Cloudflare → R2 → API Tokens | [ ] |
| Resend API Key | Resend → API Keys | [ ] |
| Stripe Secret Key (test) | Stripe → Developers → API Keys | [ ] |
| Stripe Publishable Key (test) | Stripe → Developers → API Keys | [ ] |
| JWT Private Key | gerado localmente | [ ] |
| JWT Public Key | gerado localmente | [ ] |

---

## ❓ Quando o Codex travar e pedir ajuda

Se aparecer uma mensagem pedindo algo que você não entende, manda o texto aqui pro Claude que a gente resolve.

As situações mais comuns são:
- **"Permission denied"** → rode o PowerShell como Administrador
- **"port already in use"** → rode `make dev-down` e tente de novo
- **"module not found"** → rode `make install` dentro da pasta do projeto
- **Qualquer erro vermelho que não vai embora** → copia e cola aqui
