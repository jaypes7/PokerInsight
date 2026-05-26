import { Activity, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center gap-8 px-6 py-10">
        <div className="max-w-2xl">
          <p className="mb-3 text-sm font-semibold uppercase tracking-normal text-teal-700">
            PokerInsight
          </p>
          <h1 className="text-4xl font-semibold text-slate-950 sm:text-5xl">
            Base pronta para analisar HHs PokerStars PT-BR.
          </h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-700">
            Skeleton do MVP com API, web, CI e ambiente local preparados para as
            proximas fases.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <Activity
              className="mb-4 h-6 w-6 text-teal-700"
              aria-hidden="true"
            />
            <h2 className="text-lg font-semibold text-slate-950">
              API observavel
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Healthcheck, readiness, versionamento, request id e logs
              estruturados.
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <Upload className="mb-4 h-6 w-6 text-teal-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-slate-950">
              Pronta para imports
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Postgres, Redis e MinIO sobem localmente para suportar parser e
              storage.
            </p>
          </div>
        </div>

        <div>
          <Button>Comecar</Button>
        </div>
      </section>
    </main>
  );
}
