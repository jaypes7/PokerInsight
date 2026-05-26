#!/usr/bin/env python3
"""
PokerInsight — Orquestrador de Agentes
=======================================
Lê o TODO.md, encontra a próxima task pendente, monta o prompt
completo (com docs) e chama o agente (Codex ou Claude Code).

Uso:
  python scripts/orchestrate.py --dry-run          # ver prompt sem chamar nada
  python scripts/orchestrate.py                    # rodar próxima task (Codex)
  python scripts/orchestrate.py --agent claude     # usar Claude Code
  python scripts/orchestrate.py --task F1-PARSER-003
  python scripts/orchestrate.py --phase F0 --loop
  python scripts/orchestrate.py --status
"""

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── Caminhos ──────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
TODO_PATH  = ROOT / "TODO.md"
AGENTS_MD  = ROOT / "AGENTS.md"
DOCS_DIR   = ROOT / "docs"
PROMPT_FILE = ROOT / ".agent_prompt.md"

DOC_CHAR_LIMIT = 14_000   # chars máximos por doc injetado no prompt

# ── Tasks que exigem ação humana ──────────────────────────────────────────────
NEEDS_HUMAN = {
    "F5-DEPLOY-001",  # criar contas, colar env vars
    "F5-DEPLOY-002",  # approve manual no GitHub
    "F5-LAUNCH-001",  # lançamento beta
    "F5-LGPD-001",    # revisão jurídica
}

CONFIRM_BEFORE = {
    "F4-BILLING-001",
    "F4-BILLING-003",
    "F5-SEC-001",
    "F5-SEC-002",
}


# ── Modelo de dados ───────────────────────────────────────────────────────────
@dataclass
class Task:
    id: str
    title: str
    phase: str
    description: str
    docs: list[str]             = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    agent_hint: str             = "any"
    effort: str                 = "?"
    deps: list[str]             = field(default_factory=list)


# ── Parsing do TODO.md ────────────────────────────────────────────────────────
def parse_todo(phase_filter: str | None = None) -> list[Task]:
    content = TODO_PATH.read_text(encoding="utf-8")
    tasks: list[Task] = []

    pattern = re.compile(
        r"### (F\d+-\w+-\d+) — (.+?)\n(.*?)(?=\n### F|\n---|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        task_id = m.group(1)
        title   = m.group(2).strip()
        block   = m.group(3)

        # só tasks pendentes
        if not re.search(r"^- \[ \]", block, re.MULTILINE):
            continue

        phase = task_id.split("-")[0]
        if phase_filter and phase != phase_filter:
            continue

        def extract(pat: str) -> str:
            hit = re.search(pat, block, re.DOTALL)
            return hit.group(1).strip() if hit else ""

        desc_raw  = extract(r"Description: (.+?)(?=\n- (?:Docs|AC|Agent|\[))")
        docs_raw  = extract(r"Docs: (.+?)(?=\n- (?:AC|Agent|\[))")
        agent_raw = extract(r"Agent: (.+?) \|")
        effort_raw = extract(r"Effort: (\w+)")
        deps_raw  = extract(r"Deps: (.+?)$")

        docs = [d.strip() for d in docs_raw.split(",") if d.strip() not in ("", "—")]
        deps = [d.strip() for d in deps_raw.split(",") if d.strip() not in ("", "—")]
        ac   = re.findall(r"  - \[ \] (.+)", block)

        tasks.append(Task(
            id=task_id,
            title=title,
            phase=phase,
            description=desc_raw or title,
            docs=docs,
            acceptance_criteria=ac,
            agent_hint=agent_raw or "any",
            effort=effort_raw or "?",
            deps=deps,
        ))
    return tasks


def get_completed_ids() -> set[str]:
    content = TODO_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"### (F\d+-\w+-\d+) — .+?\n- \[x\]", content))


def find_next_task(tasks: list[Task], completed: set[str]) -> Task | None:
    for task in tasks:
        if all(dep in completed for dep in task.deps):
            return task
    return None


# ── Leitura de docs ───────────────────────────────────────────────────────────
def read_doc(ref: str) -> str:
    name = ref.strip().replace("`", "").removeprefix("docs/")
    for candidate in [DOCS_DIR / name, ROOT / name]:
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8")
            suffix = ""
            if len(text) > DOC_CHAR_LIMIT:
                text   = text[:DOC_CHAR_LIMIT]
                suffix = f"\n[... truncado — leia {candidate} para o conteúdo completo]"
            sep = "═" * 60
            return f"\n\n{sep}\n📄 {candidate.name}\n{sep}\n{text}{suffix}"
    return f"\n[⚠️  Doc não encontrado: {ref}]"


# ── Construção do prompt ──────────────────────────────────────────────────────
def build_prompt(task: Task) -> str:
    agents_ctx = AGENTS_MD.read_text(encoding="utf-8")[:3_000] if AGENTS_MD.exists() else ""
    docs_ctx   = "".join(read_doc(d) for d in task.docs if d)

    ac_text = (
        "\n".join(f"  - [ ] {ac}" for ac in task.acceptance_criteria)
        if task.acceptance_criteria
        else "  Siga a descrição e as convenções do AGENTS.md."
    )

    task_id_lower = task.id.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", task.title.lower())[:45].strip("-")
    docs_section = docs_ctx or "(sem docs específicos — use README.md e AGENTS.md)"

    return f"""\
Você é um agente de desenvolvimento sênior no projeto PokerInsight.
Siga as convenções do AGENTS.md rigorosamente. Não pule etapas.

{'━'*50}
TASK : {task.id} — {task.title}
Fase : {task.phase}  |  Esforço: {task.effort}  |  Agente sugerido: {task.agent_hint}
{'━'*50}

## Descrição
{task.description}

## Critérios de Aceitação (todos precisam estar verdes)
{ac_text}

## Convenções obrigatórias (AGENTS.md — primeiros 3 mil chars)
{agents_ctx}
[Leia AGENTS.md completo para mais detalhes]

## Documentação de referência
{docs_section}

{'━'*50}
## PASSOS OBRIGATÓRIOS — execute nessa ordem

1. Leia os documentos acima antes de escrever qualquer código.
2. Implemente a task.
3. Escreva testes cobrindo os critérios de aceitação (≥85% em código novo).
4. Rode os testes: `pytest apps/api/tests/unit -q`  (ou `make test-unit`)
   Se falharem, corrija antes de continuar.
5. Se houver mudança de schema: crie migration Alembic + teste upgrade/downgrade.
6. Faça commit no formato Conventional Commits:

   feat({task_id_lower}): {slug}

   Refs: {task.id}
   - descreva o que foi feito
   - teste: descreva o que foi testado

7. Informe ao final: o que foi feito, quais testes criados, bloqueios se houver.

FOCO: implemente APENAS {task.id}. Não avance para outras tasks.
Não deixe print/console.log de debug. Não faça commit com testes falhando.
"""


# ── Chamada do agente ─────────────────────────────────────────────────────────
def call_agent(prompt: str, agent: str, dry_run: bool) -> bool:
    # Sempre salva o prompt completo em arquivo para consulta
    PROMPT_FILE.write_text(prompt, encoding="utf-8")

    if dry_run:
        print("\n" + "━" * 60)
        print("DRY RUN — primeiros 3000 chars do prompt:")
        print("━" * 60)
        print(prompt[:3_000])
        if len(prompt) > 3_000:
            print(f"\n... [{len(prompt) - 3_000} chars omitidos]")
        print(f"\n📏 Tamanho total : {len(prompt):,} chars")
        print(f"💾 Arquivo completo: {PROMPT_FILE}")
        return True

    # Verifica se o CLI está no PATH
    if not shutil.which(agent):
        msgs = {
            "codex":  "npm install -g @openai/codex   &&   codex login",
            "claude": "npm install -g @anthropic-ai/claude-code   &&   claude login",
        }
        print(f"\n❌ '{agent}' não encontrado no PATH.")
        print(f"   Instale com: {msgs.get(agent, 'verifique a documentação')}")
        return False

    # Instrução curta que pede ao agente para ler o arquivo de prompt
    instruction = f"Read the file {PROMPT_FILE} and follow all instructions in it."

    if agent == "codex":
        cmd = ["codex", instruction]
    else:  # claude
        cmd = ["claude", instruction]

    print(f"\n🤖 Chamando {agent.upper()}...")
    print(f"📄 Prompt completo em: {PROMPT_FILE}\n")

    # shell=True necessário no Windows para resolver .cmd do npm
    is_windows = sys.platform == "win32"
    result = subprocess.run(cmd, cwd=ROOT, shell=is_windows)
    return result.returncode == 0


# ── Testes locais ─────────────────────────────────────────────────────────────
def run_tests() -> bool:
    test_dir = ROOT / "apps" / "api" / "tests" / "unit"
    if not test_dir.exists():
        print("⚠️  Pasta de testes não existe ainda — pulando validação.")
        return True
    print("\n🔍 Rodando testes unitários...")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short", "-x"],
        cwd=ROOT,
    )
    return r.returncode == 0


# ── Marcar task como concluída ────────────────────────────────────────────────
def mark_done(task_id: str) -> None:
    content = TODO_PATH.read_text(encoding="utf-8")
    pattern = rf"(### {re.escape(task_id)} — .+?\n)(- \[ \])"
    updated, n = re.subn(pattern, r"\1- [x]", content, count=1)
    if n:
        TODO_PATH.write_text(updated, encoding="utf-8")
        print(f"✅ {task_id} marcada como [x] no TODO.md")
    else:
        print(f"⚠️  Não consegui marcar {task_id}. Marque [x] no TODO.md manualmente.")


# ── Status ────────────────────────────────────────────────────────────────────
def print_status(tasks: list[Task], completed: set[str]) -> None:
    done  = sum(1 for t in tasks if t.id in completed)
    print(f"\n📊 Progresso: {done}/{len(tasks)} tasks concluídas")
    phases: dict[str, list[int]] = {}
    for t in tasks:
        phases.setdefault(t.phase, [0, 0])
        phases[t.phase][1] += 1
        if t.id in completed:
            phases[t.phase][0] += 1
    for phase, (d, tot) in sorted(phases.items()):
        bar = "█" * d + "░" * (tot - d)
        print(f"   {phase}: [{bar}] {d}/{tot}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Orquestrador de agentes PokerInsight")
    parser.add_argument("--agent",     choices=["codex", "claude"], default="codex")
    parser.add_argument("--phase",     metavar="FASE", help="F0, F1, F2 ...")
    parser.add_argument("--task",      metavar="ID",   help="ex: F1-PARSER-003")
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--loop",      action="store_true")
    parser.add_argument("--max-tasks", type=int, default=1)
    parser.add_argument("--status",    action="store_true")
    args = parser.parse_args()

    if not TODO_PATH.exists():
        sys.exit(f"❌ TODO.md não encontrado em {TODO_PATH}\n   Rode a partir da raiz do repositório.")

    all_tasks = parse_todo()

    if args.status:
        print_status(all_tasks, get_completed_ids())
        return

    tasks       = parse_todo(args.phase)
    max_tasks   = args.max_tasks if args.loop else 1
    tasks_run   = 0

    while tasks_run < max_tasks:
        completed = get_completed_ids()

        if args.task:
            task = next((t for t in tasks if t.id == args.task), None)
            if not task:
                msg = "já concluída" if args.task in completed else "não encontrada no TODO.md"
                sys.exit(f"❌ Task {args.task} {msg}.")
        else:
            task = find_next_task(tasks, completed)

        if not task:
            print(f"\n🎉 Todas as tasks {'da fase ' + args.phase if args.phase else ''} concluídas!")
            print_status(all_tasks, get_completed_ids())
            break

        print(f"\n{'━'*60}")
        print(f"📋 {task.id} — {task.title}")
        print(f"   Esforço: {task.effort}  |  Agente: {task.agent_hint}")
        if task.docs: print(f"   Docs : {', '.join(task.docs)}")
        if task.deps: print(f"   Deps : {', '.join(task.deps)}")
        print("━" * 60)

        if task.id in NEEDS_HUMAN:
            print(f"\n🧑  AÇÃO HUMANA NECESSÁRIA: {task.id}")
            print("    Esta task precisa ser feita por você:")
            for ac in task.acceptance_criteria:
                print(f"    • {ac}")
            print(f"\n    Depois de concluir, marque [x] no TODO.md e rode novamente.")
            break

        if task.id in CONFIRM_BEFORE and not args.dry_run:
            resp = input(f"\n⚠️  {task.id} envolve billing/segurança. Confirma? [s/N] ").strip().lower()
            if resp != "s":
                print("Abortado.")
                break

        prompt  = build_prompt(task)
        success = call_agent(prompt, args.agent, args.dry_run)

        if not args.dry_run:
            if success and run_tests():
                mark_done(task.id)
                tasks_run += 1
                print(f"\n✅ {task.id} concluída!")
            else:
                print(f"\n❌ Falha em {task.id}. Corrija e rode novamente.")
                break
        else:
            tasks_run += 1
            if not args.loop:
                break

        if args.task:
            break

    if tasks_run:
        print_status(all_tasks, get_completed_ids())


if __name__ == "__main__":
    main()
