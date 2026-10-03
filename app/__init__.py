"""
FitAI Backend API v2.0 — Modularized FastAPI Application

Struktura:
- app/config.py — Settings, constants
- app/database.py — SQLModel engine, session management
- app/models.py — SQLModel definitions
- app/schemas.py — Pydantic request/response models
- app/auth/ — JWT, password, dependencies, auth routes
- app/fitness/ — Macros, progression, XP
- app/ai/ — LLM integration
- app/health/ — Status checks
- app/utils/ — Helpers, exceptions
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth import _rate_limit_key
from app.auth.routes import router as auth_router
from app.assessment.routes import router as assessment_router
from app.health.routes import router as health_router
from app.config import CORS_ORIGINS, APP_NAME, APP_VERSION, DEBUG, DISCORD_TOKEN
from app.database import create_db_and_tables
from app.legacy_routes import router as legacy_router
from app.meta.routes import router as meta_router
from app.notifications.discord_bot import bot as discord_bot
from app.notifications.routes import router as notifications_router
from app.plan.routes import router as plan_router
from app.training.routes import router as training_router

# Eager bootstrap so older SQLite workspaces get missing columns before the first request.
create_db_and_tables()

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="FitAI Backend API v2.0 — Fitness, Nutrition, Progressive Overload",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
limiter = Limiter(key_func=_rate_limit_key)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(assessment_router)
app.include_router(health_router)

# Import fitness routes
from app.fitness.routes import router as fitness_router
from app.ai.routes import router as ai_router

app.include_router(fitness_router)
app.include_router(ai_router)
app.include_router(meta_router)
app.include_router(notifications_router)
app.include_router(plan_router)
app.include_router(training_router)
app.include_router(legacy_router)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """Handle SQLAlchemy errors with proper logging."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error — please try again later"},
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(request, exc):
    """Handle database connection errors."""
    return JSONResponse(
        status_code=503,
        content={"detail": "Database connection error — please try again"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Catch-all for unexpected errors."""
    if DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ════════════════════════════════════════════════════════════════════════════════
# STATIC FILES — Serve HTML, CSS, JS, and SPA fallback
# ════════════════════════════════════════════════════════════════════════════════

# Define static directory (parent of app/ module)
STATIC_DIR = Path(__file__).parent.parent

# Mount public static files (if /public directory exists)
public_dir = STATIC_DIR / "public"
if public_dir.exists():
    app.mount("/public", StaticFiles(directory=str(public_dir), html=True), name="public")


def _frontend_index_response(index_path: Path):
    """Serve the dashboard shell and inject the native EVOLVE Mój dzień integration."""
    from fastapi.responses import HTMLResponse

    html = index_path.read_text(encoding="utf-8")
    if not html.strip():
        fallback_path = STATIC_DIR / "fitai_dashboard.html"
        if fallback_path.exists():
            html = fallback_path.read_text(encoding="utf-8")

    dashboard_first_bootstrap = """<style id="evolve-dashboard-first-style">
html.evolve-dashboard-first #landing { display: none !important; }
html.evolve-dashboard-first #appContainer { display: flex !important; }
</style><script>document.documentElement.classList.add('evolve-dashboard-first');</script>"""

    evolve_shell_integration = """<script id="evolve-my-day-shell-integration">
(function () {
  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char];
    });
  }

  function injectMyDayShell() {
    if (document.getElementById("tab-my-day")) return;

    var sidebar = document.querySelector(".sidebar");
    var profile = document.getElementById("nav-profile");
    if (sidebar && profile) {
      var legacyMyDay = document.getElementById("nav-myday");
      var legacyPlan = document.getElementById("nav-plan");
      if (legacyMyDay) legacyMyDay.remove();
      if (legacyPlan) legacyPlan.remove();

      profile.insertAdjacentHTML("beforebegin",
        '<button class="nav-btn" id="nav-my-day" data-tab="my-day" onclick="showTab(\'my-day\')">🎯<span class="nav-tooltip">Mój dzień</span></button>' +
        '<button class="nav-btn" id="nav-training" data-tab="training" onclick="showTab(\'training\')">🏋️<span class="nav-tooltip">Trening</span></button>' +
        '<button class="nav-btn" id="nav-basketball" data-tab="basketball" onclick="showTab(\'basketball\')">🏀<span class="nav-tooltip">Koszykówka</span></button>' +
        '<button class="nav-btn" id="nav-diet" data-tab="diet" onclick="showTab(\'diet\')">🥗<span class="nav-tooltip">Dieta</span></button>' +
        '<button class="nav-btn" id="nav-recovery" data-tab="recovery" onclick="showTab(\'recovery\')">😴<span class="nav-tooltip">Recovery</span></button>' +
        '<button class="nav-btn" id="nav-progress" data-tab="progress" onclick="showTab(\'progress\')">📈<span class="nav-tooltip">Postępy</span></button>'
      );
    }

    var content = document.querySelector(".content");
    var legacyPanel = document.getElementById("tab-myday");
    if (!content) return;

    var section =
      '<div class="tab-panel" id="tab-my-day">' +
        '<div class="sec-head">' +
          '<div><div style="font-family:\'Syne\',sans-serif;font-size:26px;font-weight:700;">Mój dzień 🎯</div>' +
          '<div style="font-size:13px;color:var(--muted);margin-top:4px;">Dzisiejszy plan, wykonanie i stan sesji w jednym miejscu.</div></div>' +
          '<div style="font-size:12px;color:var(--muted);" id="myDayDate">—</div>' +
        '</div>' +
        '<div id="myDayStatus" class="alert alert-hidden" style="margin-bottom:16px;"></div>' +
        '<div class="grid-2" style="margin-bottom:16px;">' +
          '<div class="card" style="padding:20px;">' +
            '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);">DZISIAJ</div>' +
            '<div id="myDayWorkout" style="font-size:22px;font-weight:700;margin-top:8px;">Ładowanie…</div>' +
            '<div id="myDayPlanMeta" style="font-size:12px;color:var(--muted);margin-top:6px;">—</div>' +
            '<div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;">' +
              '<a id="myDayStartLink" class="btn btn-primary btn-sm" href="/app/training/session-ui">Rozpocznij trening</a>' +
              '<a class="btn btn-outline btn-sm" href="/app/training/dashboard">Analiza treningu</a>' +
            '</div>' +
          '</div>' +
          '<div class="card" style="padding:20px;">' +
            '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);">WYKONANIE</div>' +
            '<div id="myDaySessionProgress" style="font-size:28px;font-weight:700;color:var(--cyan);margin-top:8px;">0%</div>' +
            '<div id="myDaySessionMeta" style="font-size:12px;color:var(--muted);margin-top:4px;">Brak aktywnej sesji</div>' +
            '<div class="prog-bar"><div class="prog-fill" id="myDaySessionBar" style="width:0%"></div></div>' +
          '</div>' +
        '</div>' +
        '<div class="card" style="padding:20px;">' +
          '<div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;font-size:16px;">🏋️ Dzisiejszy trening</div><div id="myDayExerciseCount" style="font-size:12px;color:var(--muted);">—</div></div>' +
          '<div id="myDayExercises"><div class="spinner"></div></div>' +
        '</div>' +
      '</div>';

    content.insertAdjacentHTML("afterbegin", section);

    if (legacyPanel) legacyPanel.style.display = "none";
  }

  var myDayLoadSequence = 0;

  window.loadEvolveMyDay = async function () {
    var exercisesEl = document.getElementById("myDayExercises");
    if (!exercisesEl) return;
    var requestId = ++myDayLoadSequence;
    var statusEl = document.getElementById("myDayStatus");
    if (statusEl) {
      statusEl.className = "alert alert-hidden";
      statusEl.textContent = "";
    }
    exercisesEl.innerHTML = '<div class="spinner"></div>';

    var token = localStorage.getItem("fitai_token");
    if (!token) {
      document.getElementById("myDayWorkout").textContent = "Zaloguj się, aby zobaczyć dzisiejszy plan";
      document.getElementById("myDayPlanMeta").textContent = "Dane treningowe są chronione przez uwierzytelnienie.";
      exercisesEl.innerHTML = '<div style="padding:20px;color:var(--muted);text-align:center;">Brak aktywnej sesji użytkownika.</div>';
      return;
    }

    try {
      var response = await fetch("/app/training/today", {
        headers: {Authorization: "Bearer " + token},
        cache: "no-store"
      });
      var data = await response.json();
      if (requestId !== myDayLoadSequence) return;
      if (!response.ok) throw new Error(data.detail || "Nie udało się pobrać danych Mój dzień");

      document.getElementById("myDayDate").textContent = data.day_label ? data.day_label + ", " + data.date : (data.date || "—");
      document.getElementById("myDayWorkout").textContent = data.has_workout ? "Trening zaplanowany" : "Dzień bez treningu";
      document.getElementById("myDayPlanMeta").textContent = data.plan
        ? ((data.plan.source === "adaptive" ? "Plan adaptacyjny" : "Plan bazowy") + (data.plan.version ? " · wersja " + data.plan.version : ""))
        : (data.message || "Brak metadanych planu");

      var session = data.session || {};
      var pct = Math.max(0, Math.min(100, Number(session.completion_pct || 0)));
      document.getElementById("myDaySessionProgress").textContent = Math.round(pct) + "%";
      document.getElementById("myDaySessionMeta").textContent = session.id
        ? (session.completed_sets || 0) + " / " + (session.planned_sets || 0) + " serii"
        : "Brak aktywnej sesji";
      document.getElementById("myDaySessionBar").style.width = pct + "%";

      var startLink = document.getElementById("myDayStartLink");
      var canStartTraining = Boolean(data.has_workout || session.id);
      startLink.textContent = session.id ? "Wznów trening" : (data.has_workout ? "Rozpocznij trening" : "Brak treningu");
      if (canStartTraining) {
        startLink.href = "/app/training/session-ui";
        startLink.removeAttribute("aria-disabled");
        startLink.classList.remove("btn-ghost");
      } else {
        startLink.removeAttribute("href");
        startLink.setAttribute("aria-disabled", "true");
        startLink.classList.add("btn-ghost");
      }

      document.getElementById("myDayExerciseCount").textContent = (data.exercises || []).length + " ćwiczeń";
      if (!data.has_workout) {
        exercisesEl.innerHTML = '<div style="padding:20px;color:var(--muted);text-align:center;">Brak zaplanowanego treningu na dziś.</div>';
        return;
      }

      exercisesEl.innerHTML = (data.exercises || []).map(function (exercise, index) {
        var sets = Number(exercise.sets || 0);
        var reps = escapeHtml(exercise.reps || "—");
        var name = escapeHtml(exercise.exercise_name || exercise.name || ("Ćwiczenie " + (index + 1)));
        var weight = exercise.weight_kg != null ? escapeHtml(exercise.weight_kg + " kg") : "";
        return '<div class="item-card" style="cursor:default;">' +
          '<div class="item-card-head"><div class="item-card-title">' + (index + 1) + ". " + name + '</div><div class="tag">' + sets + " serie</div></div>' +
          '<div class="item-card-meta">' + reps + " powtórzeń" + (weight ? " · " + weight : "") + "</div></div>";
      }).join("");
    } catch (error) {
      if (requestId !== myDayLoadSequence) return;
      var statusEl = document.getElementById("myDayStatus");
      statusEl.className = "alert alert-warn";
      statusEl.textContent = "⚠️ " + error.message;
      document.getElementById("myDayWorkout").textContent = "Nie udało się pobrać planu";
      document.getElementById("myDayPlanMeta").textContent = "Spróbuj ponownie po chwili.";
      exercisesEl.innerHTML = '<div style="padding:20px;color:var(--muted);text-align:center;">Błąd ładowania danych.</div>';
    }
  };

  function injectProgressShell() {
    if (document.getElementById("progressSummary")) return;
    var content = document.querySelector(".content");
    if (!content) return;
    var legacyPanel = document.getElementById("tab-progress");
    if (legacyPanel) {
      legacyPanel.id = "tab-progress-legacy";
      legacyPanel.style.display = "none";
    }
    var section =
      '<div class="tab-panel" id="tab-progress">' +
        '<div class="sec-head"><div><div style="font-family:\'Syne\',sans-serif;font-size:26px;font-weight:700;">Postępy 📈</div><div style="font-size:13px;color:var(--muted);margin-top:4px;">Wyniki, trendy, rekordy i regularność oparte wyłącznie na ukończonych treningach.</div></div><div id="progressUpdatedAt" style="font-size:12px;color:var(--muted);">—</div></div>' +
        '<div id="progressStatus" class="alert alert-hidden" style="margin-bottom:16px;"></div>' +
        '<div id="progressSummary" class="grid-2" style="margin-bottom:16px;"></div>' +
        '<div class="grid-2" style="margin-bottom:16px;"><div class="card" style="padding:20px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;">📈 Trendy</div><div style="font-size:12px;color:var(--muted);">ostatnia sesja vs baza</div></div><div id="progressTrends"></div></div><div class="card" style="padding:20px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;">🏆 Rekordy</div></div><div id="progressRecords"></div></div></div>' +
        '<div class="card" style="padding:20px;margin-bottom:16px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;">🏋️ Ćwiczenia</div><div style="font-size:12px;color:var(--muted);">kliknij, aby zobaczyć drill-down</div></div><div id="progressExercises"></div><div id="progressExerciseDetail" style="margin-top:16px;"></div></div>' +
        '<div class="grid-2" style="margin-bottom:16px;"><div class="card" style="padding:20px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;">📅 Regularność</div></div><div id="progressConsistency"></div></div><div class="card" style="padding:20px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;">🗂️ Historia sesji</div></div><div id="progressHistory"></div></div></div>' +
        '<div id="progressSessionDetail"></div>' +
      '</div>';
    content.insertAdjacentHTML("afterbegin", section);
  }

  var progressLoadSequence = 0;

  function progressMetricCard(label, value, meta) {
    return '<div class="card" style="padding:20px;"><div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--muted);">' + escapeHtml(label) + '</div><div style="font-size:28px;font-weight:700;margin-top:8px;">' + escapeHtml(value) + '</div><div style="font-size:12px;color:var(--muted);margin-top:4px;">' + escapeHtml(meta || "") + '</div></div>';
  }

  function progressTrendLabel(value) {
    return value === "up" ? "↗ rośnie" : value === "down" ? "↘ spada" : value === "stable" ? "→ stabilnie" : "• nowa baza";
  }

  function progressSparkline(points) {
    var values = (points || []).map(function(point){ return Number(point.best_weight_kg || 0); }).reverse();
    if (values.length < 2) return '<div style="height:4px;"></div>';
    var max = Math.max.apply(null, values), min = Math.min.apply(null, values);
    var span = max - min || 1;
    var coords = values.map(function(value, index) {
      var x = 4 + (index * 92 / Math.max(1, values.length - 1));
      var y = 28 - ((value - min) / span * 24);
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    return '<svg viewBox="0 0 100 32" preserveAspectRatio="none" style="width:100%;height:38px;margin-top:8px;display:block;" aria-label="Trend ciężaru"><polyline points="' + coords + '" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"></polyline></svg>';
  }

  window.loadEvolveProgress = async function () {
    injectProgressShell();
    var requestId = ++progressLoadSequence;
    var token = localStorage.getItem("fitai_token");
    var status = document.getElementById("progressStatus");
    if (!token) {
      if (status) { status.className = "alert alert-warn"; status.textContent = "Zaloguj się, aby zobaczyć swoje postępy."; }
      return;
    }
    ["progressSummary","progressTrends","progressRecords","progressExercises","progressConsistency","progressHistory"].forEach(function(id) {
      var el=document.getElementById(id); if(el) el.innerHTML='<div class="spinner"></div>';
    });
    try {
      var headers = {Authorization: "Bearer " + token};
      var results = await Promise.all([
        fetch("/app/training/progress?limit=12", {headers:headers, cache:"no-store"}),
        fetch("/app/training/progress/trends?limit=12", {headers:headers, cache:"no-store"}),
        fetch("/app/training/progress/records?limit=52", {headers:headers, cache:"no-store"}),
        fetch("/app/training/progress/consistency?limit=52", {headers:headers, cache:"no-store"}),
        fetch("/app/training/sessions/history?limit=12", {headers:headers, cache:"no-store"})
      ]);
      var data = await Promise.all(results.map(function(response) { return response.json().then(function(body){ return {response:response, body:body}; }); }));
      if (requestId !== progressLoadSequence) return;
      var failed = data.find(function(item){ return !item.response.ok; });
      if (failed) throw new Error(failed.body.detail || "Nie udało się pobrać danych postępów");
      var progress=data[0].body, trends=data[1].body, records=data[2].body, consistency=data[3].body, history=data[4].body;
      document.getElementById("progressUpdatedAt").textContent = new Date().toLocaleTimeString("pl-PL",{hour:"2-digit",minute:"2-digit"});
      document.getElementById("progressSummary").innerHTML =
        progressMetricCard("SESJE", progress.period_sessions, "ukończone") +
        progressMetricCard("SERIE", progress.total_completed_sets, "ukończone") +
        progressMetricCard("WOLUMEN", progress.total_volume_kg + " kg", "łącznie") +
        progressMetricCard("ŚR. WYKONANIA", progress.average_session_completion_pct + "%", "na sesję");

      document.getElementById("progressTrends").innerHTML = (trends.exercises || []).map(function(item) {
        var wc=item.weight.change_pct == null ? "—" : (item.weight.change_pct > 0 ? "+" : "") + item.weight.change_pct + "%";
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveProgressExercise(\'' + encodeURIComponent(item.exercise_key) + '\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div><div class="tag">' + item.sessions + ' sesji</div></div><div class="item-card-meta">Ciężar ' + progressTrendLabel(item.weight.trend) + ' (' + wc + ') · Wolumen ' + progressTrendLabel(item.volume.trend) + ' · RPE ' + progressTrendLabel(item.rpe.trend) + '</div>' + progressSparkline(item.history) + '</button>';
      }).join("") || '<div style="color:var(--muted);">Brak danych do wyznaczenia trendów.</div>';

      document.getElementById("progressRecords").innerHTML = (records.exercises || []).map(function(item) {
        return '<div class="item-card" style="cursor:default;"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div></div><div class="item-card-meta">🏋️ ' + item.best_weight.value_kg + ' kg · 🔁 ' + item.best_reps.value + ' powt. przy ' + item.best_reps.weight_kg + ' kg · 📦 ' + item.best_session_volume.value_kg + ' kg/sesję</div></div>';
      }).join("") || '<div style="color:var(--muted);">Brak rekordów.</div>';

      document.getElementById("progressExercises").innerHTML = (progress.exercises || []).map(function(item) {
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveProgressExercise(\'' + encodeURIComponent(item.exercise_key) + '\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div><div class="tag">' + item.sessions + ' sesji</div></div><div class="item-card-meta">' + item.total_volume_kg + ' kg wolumenu · rekord ' + item.best_weight_kg + ' kg · śr. RPE ' + (item.average_rpe == null ? '—' : item.average_rpe) + '</div></button>';
      }).join("") || '<div style="padding:12px;color:var(--muted);">Brak ukończonych danych treningowych.</div>';

      document.getElementById("progressConsistency").innerHTML =
        progressMetricCard("DNI TRENINGOWE", consistency.training_days, "w analizowanym okresie") +
        progressMetricCard("SESJE / TYDZ.", consistency.average_sessions_per_week, "średnia") +
        progressMetricCard("BIEŻĄCA SERIA", consistency.current_streak_days + " dni", "kolejne dni treningowe") +
        progressMetricCard("NAJDŁUŻSZA SERIA", consistency.longest_streak_days + " dni", "kolejne dni treningowe");

      document.getElementById("progressHistory").innerHTML = (history.sessions || []).map(function(item) {
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveSessionDetail(\'' + item.session_id + '\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.session_date) + '</div><div class="tag">' + item.completion_pct + '%</div></div><div class="item-card-meta">' + item.completed_sets + '/' + item.planned_sets + ' serii · ' + item.exercise_count + ' ćwiczeń' + (item.final_rpe != null ? ' · RPE ' + item.final_rpe : '') + '</div></button>';
      }).join("") || '<div style="color:var(--muted);">Brak ukończonych sesji.</div>';
      if (status) { status.className = "alert alert-hidden"; status.textContent = ""; }
    } catch (error) {
      if (requestId !== progressLoadSequence) return;
      if (status) { status.className = "alert alert-warn"; status.textContent = "⚠️ " + error.message; }
    }
  };

  window.loadEvolveProgressExercise = async function (encodedKey) {
    var detail = document.getElementById("progressExerciseDetail");
    if (!detail) return;
    try {
      detail.innerHTML='<div class="spinner"></div>';
      var token=localStorage.getItem("fitai_token");
      var response=await fetch("/app/training/progress/exercises/" + encodeURIComponent(decodeURIComponent(encodedKey)) + "?limit=12",{headers:{Authorization:"Bearer "+token},cache:"no-store"});
      var data=await response.json();
      if(!response.ok) throw new Error(data.detail || "Nie udało się pobrać progresu ćwiczenia");
      var rows=(data.history||[]).map(function(row){return '<div class="item-card" style="cursor:default;"><div class="item-card-head"><div class="item-card-title">'+escapeHtml(row.session_date)+'</div><div class="tag">'+row.sets+' serii</div></div><div class="item-card-meta">'+row.best_weight_kg+' kg · '+row.best_reps_at_best_weight+' powt. · '+row.total_volume_kg+' kg wolumenu'+(row.average_rpe!=null?' · RPE '+row.average_rpe:'')+'</div></div>';}).join("");
      detail.innerHTML='<div class="card" style="padding:18px;border:1px solid var(--border);"><div class="sec-head"><div><div style="font-weight:700;">'+escapeHtml(data.exercise_name||data.exercise_key)+'</div><div style="font-size:12px;color:var(--muted);">'+data.sessions+' sesji · rekord '+data.best_weight_kg+' kg · wolumen '+data.total_volume_kg+' kg</div></div><button class="btn btn-ghost btn-sm" onclick="document.getElementById(\'progressExerciseDetail\').innerHTML=\'\'">Zamknij</button></div>'+(rows||'<div style="color:var(--muted);">Brak historii.</div>')+'</div>';
    } catch(error) { detail.innerHTML='<div class="alert alert-warn">'+escapeHtml(error.message)+'</div>'; }
  };

  window.loadEvolveSessionDetail = async function (sessionId) {
    var detail=document.getElementById("progressSessionDetail");
    if(!detail) return;
    detail.innerHTML='<div class="card" style="padding:20px;"><div class="spinner"></div></div>';
    try {
      var token=localStorage.getItem("fitai_token");
      var response=await fetch("/app/training/sessions/history/"+encodeURIComponent(sessionId),{headers:{Authorization:"Bearer "+token},cache:"no-store"});
      var data=await response.json();
      if(!response.ok) throw new Error(data.detail || "Nie udało się pobrać sesji");
      var grouped={};
      (data.sets||[]).forEach(function(item){(grouped[item.exercise_name] ||= []).push(item);});
      var body=Object.keys(grouped).map(function(name){return '<div style="margin-bottom:14px;"><div style="font-weight:700;margin-bottom:6px;">'+escapeHtml(name)+'</div>'+grouped[name].map(function(item){return '<div style="font-size:13px;color:var(--muted);padding:4px 0;">Seria '+item.set_number+': '+item.actual_reps+' × '+item.actual_weight_kg+' kg'+(item.actual_rpe!=null?' · RPE '+item.actual_rpe:'')+'</div>';}).join("")+'</div>';}).join("");
      detail.innerHTML='<div class="card" style="padding:20px;margin-bottom:16px;"><div class="sec-head"><div><div style="font-weight:700;">Sesja '+escapeHtml(data.session_date)+'</div><div style="font-size:12px;color:var(--muted);">Ukończono: '+escapeHtml(data.completed_at||"—")+'</div></div><button class="btn btn-ghost btn-sm" onclick="document.getElementById(\'progressSessionDetail\').innerHTML=\'\'">Zamknij</button></div>'+body+'</div>';
      detail.scrollIntoView({behavior:"smooth",block:"nearest"});
    } catch(error) { detail.innerHTML='<div class="alert alert-warn">'+escapeHtml(error.message)+'</div>'; }
  };

  function installMyDayRoutingHook() {
    if (window.__evolveMyDayRoutingHookInstalled) return;
    if (typeof window.showTab !== "function") return;
    var originalShowTab = window.showTab;
    window.showTab = function (tab) {
      var result = originalShowTab.apply(this, arguments);
      if (tab === "my-day") {
        window.loadEvolveMyDay();
      } else if (tab === "progress") {
        window.loadEvolveProgress();
      }
      return result;
    };
    window.__evolveMyDayRoutingHookInstalled = true;
  }

  function installHashRouting() {
    var raw = window.location.hash.replace("#", "");
    if (raw === "my-day" || raw === "training" || raw === "basketball" || raw === "diet" || raw === "recovery" || raw === "progress" || raw === "profile" || raw === "home") {
      if (typeof showTab === "function") showTab(raw);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    injectMyDayShell();
    injectProgressShell();
    installMyDayRoutingHook();
    installHashRouting();
  });
  window.addEventListener("hashchange", installHashRouting);
})();
</script>"""

    if 'id="evolve-my-day-shell-integration"' not in html:
        html = html.replace("</body>", evolve_shell_integration + "</body>", 1)

    if 'id="evolve-dashboard-first-style"' not in html:
        html = html.replace("</head>", dashboard_first_bootstrap + "</head>", 1)

    dashboard_boot = """<script id="evolve-dashboard-first-boot">
document.addEventListener('DOMContentLoaded', function () {
  if (typeof enterApp === 'function') enterApp();
});
</script>"""
    if 'id="evolve-dashboard-first-boot"' not in html:
        html = html.replace("</body>", dashboard_boot + "</body>", 1)

    return HTMLResponse(html, media_type="text/html")

# Root route — serve index.html for SPA
@app.get("/")
async def serve_root():
    """Serve main index.html for single-page app."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return _frontend_index_response(index_path)
    return JSONResponse({"error": "Frontend not found"}, status_code=404)


# Catch-all for SPA routing — serve index.html for any unmatched path
@app.get("/{path:path}")
async def serve_spa(path: str):
    """
    Fallback route for SPA routing. Serves index.html for any path
    that isn't matched by API routes or known static files.
    """
    # Skip API routes and known assets
    skip_paths = {".json", ".js", ".css", ".png", ".jpg", ".gif", ".svg", ".ico", ".woff", ".woff2"}
    if any(path.endswith(ext) for ext in skip_paths):
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    # For all other paths, serve index.html (SPA routing)
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return _frontend_index_response(index_path)
    
    return JSONResponse({"error": "Frontend not found"}, status_code=404)


# ─── Startup / Shutdown ───────────────────────────────────────────────────────

import asyncio

@app.on_event("startup")
async def on_startup():
    """Initialize database and start Discord bot (if token is configured)."""
    create_db_and_tables()
    print(f"[{APP_NAME}] Database initialized at startup")

    if DISCORD_TOKEN:
        async def _run_bot() -> None:
            try:
                await discord_bot.start(DISCORD_TOKEN)
            except Exception as exc:
                print(f"[{APP_NAME}] OSTRZEŻENIE: Bot Discord zakończył się błędem: {exc}")

        asyncio.create_task(_run_bot())
        print(f"[{APP_NAME}] Discord bot uruchomiony w tle.")
    else:
        print(f"[{APP_NAME}] OSTRZEŻENIE: DISCORD_TOKEN nie ustawiony — bot Discord nie startuje.")


@app.on_event("shutdown")
async def on_shutdown():
    """Graceful shutdown — zamknij połączenie bota Discord."""
    if DISCORD_TOKEN and not discord_bot.is_closed():
        await discord_bot.close()
        print(f"[{APP_NAME}] Discord bot zatrzymany.")