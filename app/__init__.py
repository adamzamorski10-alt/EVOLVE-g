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
from app.goals.routes import router as goals_router
from app.config import CORS_ORIGINS, APP_NAME, APP_VERSION, DEBUG, DISCORD_TOKEN
from app.database import create_db_and_tables
from app.decision_routes import router as decision_router
from app.today_routes import router as today_router
from app.legacy_routes import router as legacy_router
from app.meta.routes import router as meta_router
from app.notifications.discord_bot import bot as discord_bot
from app.notifications.routes import router as notifications_router
from app.nutrition.routes import router as nutrition_router
from app.plan.routes import router as plan_router
from app.recovery.routes import router as recovery_router
from app.training.routes import router as training_router
from app.training.evaluation_routes import router as training_evaluation_router

# Eager bootstrap for normal application runtime; Alembic imports the models without mutating the target DB.
if os.getenv("EVOLVE_ALEMBIC_CONTEXT") != "1":
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
app.include_router(goals_router)
app.include_router(decision_router)
app.include_router(today_router)

# Import fitness routes
from app.fitness.routes import router as fitness_router
from app.ai.routes import router as ai_router

app.include_router(fitness_router)
app.include_router(ai_router)
app.include_router(meta_router)
app.include_router(notifications_router)
app.include_router(nutrition_router)
app.include_router(plan_router)
app.include_router(recovery_router)
app.include_router(training_router)
app.include_router(training_evaluation_router)
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
html.evolve-dashboard-first #landingPage { display: none !important; }
html.evolve-dashboard-first #dashboardPage { display: flex !important; }
</style><script>document.documentElement.classList.add('evolve-dashboard-first');</script>"""

    evolve_shell_integration = """<script id="evolve-my-day-shell-integration">
(function () {
  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[char];
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
        '<button class="nav-btn" id="nav-my-day" data-tab="my-day" onclick="showTab(\\'my-day\\')">🎯<span class="nav-tooltip">Mój dzień</span></button>' +
        '<button class="nav-btn" id="nav-training" data-tab="training" onclick="showTab(\\'training\\')">🏋️<span class="nav-tooltip">Trening</span></button>' +
        '<button class="nav-btn" id="nav-basketball" data-tab="basketball" onclick="showTab(\\'basketball\\')">🏀<span class="nav-tooltip">Koszykówka</span></button>' +
        '<button class="nav-btn" id="nav-diet" data-tab="diet" onclick="showTab(\\'diet\\')">🥗<span class="nav-tooltip">Dieta</span></button>' +
        '<button class="nav-btn" id="nav-recovery" data-tab="recovery" onclick="showTab(\\'recovery\\')">😴<span class="nav-tooltip">Recovery</span></button>' +
        '<button class="nav-btn" id="nav-progress" data-tab="progress" onclick="showTab(\\'progress\\')">📈<span class="nav-tooltip">Postępy</span></button>'
      );
    }

    var content = document.querySelector(".content");
    var legacyPanel = document.getElementById("tab-myday");
    if (!content) return;

    var section =
      '<div class="tab-panel" id="tab-my-day">' +
        '<div class="sec-head">' +
          '<div><div style="font-family:\\'Syne\\',sans-serif;font-size:26px;font-weight:700;">Mój dzień 🎯</div>' +
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
      var canStartTraining = Boolean(data.can_start || session.id);
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
          '<div class="item-card-head"><div class="item-card-title">' + (index + 1) + ". " + name + '</div><div class="tag">' + sets + " serie</div></div>" +
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

  (function () {
  var originalShowTab = window.showTab;
  if (typeof originalShowTab !== "function" || originalShowTab.__evolveNutritionWrapped) return;
  function wrappedShowTab(tab) {
    var result = originalShowTab.apply(this, arguments);
    if (tab === "diet" && typeof window.loadEvolveNutrition === "function") {
      window.loadEvolveNutrition();
    }
    return result;
  }
  wrappedShowTab.__evolveNutritionWrapped = true;
  window.showTab = wrappedShowTab;
})();

  function injectGoalsShell() {
    if (document.getElementById("goalsSummary")) return;
    var content = document.querySelector(".content");
    var profile = document.getElementById("nav-profile");
    if (!content) return;
    if (profile && !document.getElementById("nav-goals")) {
      profile.insertAdjacentHTML("beforebegin",
        '<button class="nav-btn" id="nav-goals" data-tab="goals" onclick="showTab(\\'goals\\')">🎯<span class="nav-tooltip">Cele</span></button>');
    }
    var legacy = document.getElementById("tab-goals");
    if (legacy) { legacy.id = "tab-goals-legacy"; legacy.style.display = "none"; }
    var section =
      '<div class="tab-panel" id="tab-goals">' +
        '<div class="sec-head"><div><div style="font-family:\\'Syne\\',sans-serif;font-size:26px;font-weight:700;">Cele 🎯</div><div style="font-size:13px;color:var(--muted);margin-top:4px;">Twoje cele, mierzalny postęp i terminy w jednym miejscu.</div></div><button class="btn btn-primary btn-sm" onclick="openEvolveGoalForm()">+ Nowy cel</button></div>' +
        '<div id="goalsStatus" class="alert alert-hidden" style="margin-bottom:16px;"></div>' +
        '<div id="goalsSummary" class="grid-2" style="margin-bottom:16px;"></div>' +
        '<div id="goalForm" class="card" style="padding:20px;margin-bottom:16px;display:none;"></div>' +
        '<div id="goalsList"></div>' +
        '<div id="goalDetail" style="margin-top:16px;"></div>' +
      '</div>';
    content.insertAdjacentHTML("afterbegin", section);
  }

  var goalsLoadSequence = 0;

  function goalEscape(value) { return escapeHtml(value == null ? "" : value); }
  function goalStatusLabel(status) {
    return status === "active" ? "Aktywny" : status === "completed" ? "Ukończony" : status === "cancelled" ? "Anulowany" : "Zarchiwizowany";
  }
  function goalCard(goal, progress) {
    var pct = progress && progress.progress_pct != null ? Math.max(0, Math.min(100, Number(progress.progress_pct))) : null;
    var metric = progress && progress.metric ? progress.metric.unit : "";
    var current = progress && progress.current_value != null ? progress.current_value : "—";
    var target = goal.target_value != null ? goal.target_value : "—";
    var bar = pct == null ? '<div style="font-size:12px;color:var(--muted);">Brak danych pomiarowych</div>' :
      '<div style="height:7px;background:var(--border);border-radius:99px;overflow:hidden;margin-top:10px;"><div style="height:100%;width:'+pct+'%;background:var(--cyan);border-radius:99px;"></div></div>';
    return '<div class="card" style="padding:20px;margin-bottom:12px;">' +
      '<div class="item-card-head"><div><div class="item-card-title">'+goalEscape(goal.title)+'</div><div class="item-card-meta">'+goalEscape(goal.goal_type)+' · '+goalStatusLabel(goal.status)+'</div></div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap;"><button class="btn btn-ghost btn-sm" onclick="loadEvolveGoalDetail(\\''+goal.id+'\\')">Szczegóły</button><button class="btn btn-ghost btn-sm" onclick="editEvolveGoal(\\''+goal.id+'\\')">Edytuj</button>' +
      (goal.status === "active" ? '<button class="btn btn-outline btn-sm" onclick="updateEvolveGoalStatus(\\''+goal.id+'\\',\\'completed\\')">Ukończ</button>' : '') +
      (goal.status !== "archived" ? '<button class="btn btn-ghost btn-sm" onclick="archiveEvolveGoal(\\''+goal.id+'\\')">Archiwizuj</button>' : '')+'</div></div>' +
      '<div style="margin-top:14px;display:flex;justify-content:space-between;gap:12px;font-size:13px;"><span>'+goalEscape(current)+' '+goalEscape(metric)+'</span><span>cel: '+goalEscape(target)+' '+goalEscape(metric)+'</span></div>'+bar+
      '<div style="margin-top:9px;font-size:12px;color:var(--muted);">'+(pct == null ? "Postęp oczekuje na dane." : "Postęp: "+pct+"%")+' · termin: '+goalEscape(goal.target_date || "bez terminu")+'</div></div>';
  }

  window.openEvolveGoalForm = function(existing) {
    var form = document.getElementById("goalForm");
    if (!form) return;
    var g = existing || {};
    form.style.display = "block";
    form.innerHTML =
      '<div style="font-weight:700;font-size:17px;margin-bottom:14px;">'+(existing ? "Edytuj cel" : "Nowy cel")+'</div>' +
      '<div class="grid-2">' +
      '<label>Tytuł<input id="goalTitle" class="input" maxlength="200" value="'+goalEscape(g.title)+'"></label>' +
      '<label>Typ<select id="goalType" class="input"><option value="performance">performance</option><option value="skill">skill</option><option value="strength">strength</option><option value="basketball">basketball</option><option value="body_composition">body_composition</option><option value="habit">habit</option><option value="custom">custom</option></select></label>' +
      '<label>Metryka<select id="goalMetric" class="input"><option value="">Brak metryki</option><option value="best_weight_kg">best_weight_kg</option><option value="best_reps_at_best_weight">best_reps_at_best_weight</option><option value="total_volume_kg">total_volume_kg</option><option value="sessions">sessions</option><option value="training_days">training_days</option><option value="average_rpe">average_rpe</option></select></label>' +
      '<label>Ćwiczenie (opcjonalnie)<input id="goalExercise" class="input" placeholder="np. squat" value="'+goalEscape((g.metadata||{}).exercise_key)+'"></label>' +
      '<label>Wartość bazowa<input id="goalBaseline" class="input" type="number" step="any" value="'+goalEscape(g.baseline_value)+'"></label>' +
      '<label>Wartość docelowa<input id="goalTarget" class="input" type="number" step="any" value="'+goalEscape(g.target_value)+'"></label>' +
      '<label>Data rozpoczęcia<input id="goalStart" class="input" type="date" value="'+goalEscape(g.start_date)+'"></label>' +
      '<label>Termin<input id="goalDeadline" class="input" type="date" value="'+goalEscape(g.target_date)+'"></label></div>' +
      '<div style="margin-top:14px;display:flex;gap:8px;"><button class="btn btn-primary btn-sm" onclick="saveEvolveGoal('+(existing ? "'"+existing.id+"'" : "null")+')">Zapisz</button><button class="btn btn-ghost btn-sm" onclick="closeEvolveGoalForm()">Anuluj</button></div>';
    if (existing) {
      document.getElementById("goalType").value = g.goal_type || "custom";
      document.getElementById("goalMetric").value = g.metric_key || "";
    }
  };
  window.closeEvolveGoalForm = function(){ var f=document.getElementById("goalForm"); if(f){f.style.display="none";f.innerHTML="";} };
  window.saveEvolveGoal = async function(id) {
    var token=localStorage.getItem("fitai_token"); if(!token) return;
    var metric=document.getElementById("goalMetric").value;
    var payload={title:document.getElementById("goalTitle").value,goal_type:document.getElementById("goalType").value,metric_key:metric||null,start_date:document.getElementById("goalStart").value||null,target_date:document.getElementById("goalDeadline").value||null,baseline_value:document.getElementById("goalBaseline").value===""?null:Number(document.getElementById("goalBaseline").value),target_value:document.getElementById("goalTarget").value===""?null:Number(document.getElementById("goalTarget").value),metadata:{exercise_key:document.getElementById("goalExercise").value.trim()}};
    var response=await fetch(id?"/app/goals/"+encodeURIComponent(id):"/app/goals",{method:id?"PATCH":"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(payload)});
    var body=await response.json(); if(!response.ok){showEvolveGoalError(body.detail||"Nie udało się zapisać celu");return;} closeEvolveGoalForm(); loadEvolveGoals();
  };
  function showEvolveGoalError(message){var s=document.getElementById("goalsStatus");if(s){s.className="alert alert-warn";s.textContent="⚠️ "+message;}}
  async function goalFetch(path, options){var token=localStorage.getItem("fitai_token");if(!token) throw new Error("Zaloguj się, aby zarządzać celami.");var response=await fetch(path,Object.assign({headers:{"Authorization":"Bearer "+token},cache:"no-store"},options||{}));var body=await response.json();if(!response.ok)throw new Error(body.detail||"Nie udało się pobrać danych celów.");return body;}
  window.loadEvolveGoals = async function(){
    injectGoalsShell(); var id=++goalsLoadSequence; var list=document.getElementById("goalsList"), summary=document.getElementById("goalsSummary"), status=document.getElementById("goalsStatus");
    if(!list)return; if(status){status.className="alert alert-hidden";status.textContent="";} list.innerHTML='<div class="spinner"></div>';
    try{
      var data=await goalFetch("/app/goals"); if(id!==goalsLoadSequence)return;
      var goals=data.goals||[], active=goals.filter(function(g){return g.status==="active";}), done=goals.filter(function(g){return g.status==="completed";}), archived=goals.filter(function(g){return g.status==="archived";}), cancelled=goals.filter(function(g){return g.status==="cancelled";});
      summary.innerHTML=progressMetricCard("AKTYWNE",active.length,"cele") + progressMetricCard("UKOŃCZONE",done.length,"cele") + progressMetricCard("ARCHIWUM",archived.length,"cele") + progressMetricCard("Z TERMINEM",active.filter(function(g){return g.target_date;}).length,"aktywne") + progressMetricCard("MIERZALNE",active.filter(function(g){return g.metric_key;}).length,"aktywne");
      var progress=await Promise.all(active.map(function(g){return goalFetch("/app/goals/"+encodeURIComponent(g.id)+"/progress").catch(function(){return null;});}));
      list.innerHTML=(active.concat(done).concat(cancelled).concat(archived)).map(function(g){var p=progress[active.indexOf(g)];return goalCard(g,p);}).join("") || '<div class="card" style="padding:28px;text-align:center;color:var(--muted);">Brak celów. Utwórz pierwszy cel, aby rozpocząć.</div>';
    }catch(e){showEvolveGoalError(e.message);list.innerHTML='<div class="card" style="padding:28px;text-align:center;color:var(--muted);">Nie udało się załadować celów.</div>';}
  };
  window.editEvolveGoal = async function(id){ try { var g=await goalFetch("/app/goals/"+encodeURIComponent(id)); openEvolveGoalForm(g); document.getElementById("goalForm").scrollIntoView({behavior:"smooth",block:"nearest"}); } catch(e) { showEvolveGoalError(e.message); } };
  window.loadEvolveGoalDetail = async function(id){
    var detail=document.getElementById("goalDetail");if(!detail)return;detail.innerHTML='<div class="spinner"></div>';
    try{var g=await goalFetch("/app/goals/"+encodeURIComponent(id)),p=await goalFetch("/app/goals/"+encodeURIComponent(id)+"/progress");
      detail.innerHTML='<div class="card" style="padding:20px;"><div class="sec-head"><div><div style="font-weight:700;font-size:18px;">'+goalEscape(g.title)+'</div><div style="font-size:12px;color:var(--muted);">'+goalStatusLabel(g.status)+' · '+goalEscape(g.description||"")+'</div></div><button class="btn btn-ghost btn-sm" onclick="document.getElementById(\\'goalDetail\\').innerHTML=\\'\\'">Zamknij</button></div><div style="margin-top:14px;">Aktualnie: <b>'+goalEscape(p.current_value==null?"—":p.current_value)+'</b> · Cel: <b>'+goalEscape(p.target_value==null?"—":p.target_value)+'</b> · Postęp: <b>'+goalEscape(p.progress_pct==null?"—":p.progress_pct+"%")+'</b></div><div style="margin-top:8px;color:var(--muted);">Trend: '+goalEscape(p.trend||"—")+' · Ostatnia aktualizacja: '+goalEscape(p.last_updated||"—")+' · Termin: '+goalEscape(p.deadline||"—")+'</div></div>';
      detail.scrollIntoView({behavior:"smooth",block:"nearest"});
    }catch(e){detail.innerHTML='<div class="alert alert-warn">'+goalEscape(e.message)+'</div>';}
  };
  window.updateEvolveGoalStatus = async function(id,status){try{await goalFetch("/app/goals/"+encodeURIComponent(id),{method:"PATCH",headers:{"Authorization":"Bearer "+localStorage.getItem("fitai_token"),"Content-Type":"application/json"},body:JSON.stringify({status:status})});loadEvolveGoals();}catch(e){showEvolveGoalError(e.message);}};
  window.archiveEvolveGoal = async function(id){if(!confirm("Zarchiwizować ten cel?"))return;try{await goalFetch("/app/goals/"+encodeURIComponent(id),{method:"DELETE"});loadEvolveGoals();}catch(e){showEvolveGoalError(e.message);}};

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
        '<div class="sec-head"><div><div style="font-family:\\'Syne\\',sans-serif;font-size:26px;font-weight:700;">Postępy 📈</div><div style="font-size:13px;color:var(--muted);margin-top:4px;">Wyniki, trendy, rekordy i regularność oparte wyłącznie na ukończonych treningach.</div></div><div id="progressUpdatedAt" style="font-size:12px;color:var(--muted);">—</div></div>' +
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
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveProgressExercise(\\'' + encodeURIComponent(item.exercise_key) + '\\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div><div class="tag">' + item.sessions + ' sesji</div></div><div class="item-card-meta">Ciężar ' + progressTrendLabel(item.weight.trend) + ' (' + wc + ') · Wolumen ' + progressTrendLabel(item.volume.trend) + ' · RPE ' + progressTrendLabel(item.rpe.trend) + '</div>' + progressSparkline(item.history) + '</button>';
      }).join("") || '<div style="color:var(--muted);">Brak danych do wyznaczenia trendów.</div>';

      document.getElementById("progressRecords").innerHTML = (records.exercises || []).map(function(item) {
        return '<div class="item-card" style="cursor:default;"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div></div><div class="item-card-meta">🏋️ ' + item.best_weight.value_kg + ' kg · 🔁 ' + item.best_reps.value + ' powt. przy ' + item.best_reps.weight_kg + ' kg · 📦 ' + item.best_session_volume.value_kg + ' kg/sesję</div></div>';
      }).join("") || '<div style="color:var(--muted);">Brak rekordów.</div>';

      document.getElementById("progressExercises").innerHTML = (progress.exercises || []).map(function(item) {
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveProgressExercise(\\'' + encodeURIComponent(item.exercise_key) + '\\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.exercise_name) + '</div><div class="tag">' + item.sessions + ' sesji</div></div><div class="item-card-meta">' + item.total_volume_kg + ' kg wolumenu · rekord ' + item.best_weight_kg + ' kg · śr. RPE ' + (item.average_rpe == null ? '—' : item.average_rpe) + '</div></button>';
      }).join("") || '<div style="padding:12px;color:var(--muted);">Brak ukończonych danych treningowych.</div>';

      document.getElementById("progressConsistency").innerHTML =
        progressMetricCard("DNI TRENINGOWE", consistency.training_days, "w analizowanym okresie") +
        progressMetricCard("SESJE / TYDZ.", consistency.average_sessions_per_week, "średnia") +
        progressMetricCard("BIEŻĄCA SERIA", consistency.current_streak_days + " dni", "kolejne dni treningowe") +
        progressMetricCard("NAJDŁUŻSZA SERIA", consistency.longest_streak_days + " dni", "kolejne dni treningowe");

      document.getElementById("progressHistory").innerHTML = (history.sessions || []).map(function(item) {
        return '<button class="item-card" style="width:100%;text-align:left;" onclick="loadEvolveSessionDetail(\\'' + item.session_id + '\\')"><div class="item-card-head"><div class="item-card-title">' + escapeHtml(item.session_date) + '</div><div class="tag">' + item.completion_pct + '%</div></div><div class="item-card-meta">' + item.completed_sets + '/' + item.planned_sets + ' serii · ' + item.exercise_count + ' ćwiczeń' + (item.final_rpe != null ? ' · RPE ' + item.final_rpe : '') + '</div></button>';
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
      detail.innerHTML='<div class="card" style="padding:18px;border:1px solid var(--border);"><div class="sec-head"><div><div style="font-weight:700;">'+escapeHtml(data.exercise_name||data.exercise_key)+'</div><div style="font-size:12px;color:var(--muted);">'+data.sessions+' sesji · rekord '+data.best_weight_kg+' kg · wolumen '+data.total_volume_kg+' kg</div></div><button class="btn btn-ghost btn-sm" onclick="document.getElementById(\\'progressExerciseDetail\\').innerHTML=\\'\\'">Zamknij</button></div>'+(rows||'<div style="color:var(--muted);">Brak historii.</div>')+'</div>';
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
      detail.innerHTML='<div class="card" style="padding:20px;margin-bottom:16px;"><div class="sec-head"><div><div style="font-weight:700;">Sesja '+escapeHtml(data.session_date)+'</div><div style="font-size:12px;color:var(--muted);">Ukończono: '+escapeHtml(data.completed_at||"—")+'</div></div><button class="btn btn-ghost btn-sm" onclick="document.getElementById(\\'progressSessionDetail\\').innerHTML=\\'\\'">Zamknij</button></div>'+body+'</div>';
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
      } else if (tab === "goals") {
        window.loadEvolveGoals();
      } else if (tab === "recovery") {
        window.loadEvolveRecovery();
      }
      return result;
    };
    window.__evolveMyDayRoutingHookInstalled = true;
  }

  function installHashRouting() {
    var raw = window.location.hash.replace("#", "");
    if (raw === "my-day" || raw === "training" || raw === "basketball" || raw === "diet" || raw === "recovery" || raw === "progress" || raw === "goals" || raw === "profile" || raw === "home") {
      if (typeof showTab === "function") showTab(raw);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    injectMyDayShell();
    injectProgressShell();
    injectGoalsShell();
    installMyDayRoutingHook();
    installHashRouting();
  });
  window.addEventListener("hashchange", installHashRouting);
})();
</script>"""

    recovery_shell_integration = """<script id="evolve-recovery-shell-integration">
(function () {
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[char];
    });
  }
  var recoveryLoadSequence = 0;
  function injectRecoveryShell() {
    if (document.getElementById("recoverySummary")) return;
    var content = document.querySelector(".content");
    if (!content) return;
    content.insertAdjacentHTML("afterbegin",
      '<div class="tab-panel" id="tab-recovery">' +
      '<div class="sec-head"><div><div style="font-family:\\'Syne\\',sans-serif;font-size:26px;font-weight:700;">Recovery 😴</div><div style="font-size:13px;color:var(--muted);margin-top:4px;">Dzisiejsza gotowość i wpływ recovery na trening.</div></div><div id="recoveryDate" style="font-size:12px;color:var(--muted);">—</div></div>' +
      '<div id="recoveryStatus" class="alert alert-hidden" style="margin-bottom:16px;"></div>' +
      '<div id="recoverySummary" class="grid-2" style="margin-bottom:16px;"></div>' +
      '<div class="card" style="padding:20px;margin-bottom:16px;"><div style="font-weight:700;">Sygnały recovery</div><div id="recoverySignals" style="margin-top:12px;"></div></div>' +
      '<div class="card" style="padding:20px;"><div style="font-weight:700;">Historia 14 dni</div><div id="recoveryTrend" style="margin-top:12px;"></div><div id="recoveryHistory" style="margin-top:12px;"></div></div>' +
      '<div class="card" style="padding:20px;"><div style="font-weight:700;">Wpływ na trening</div><div id="recoveryEffect" style="margin-top:8px;color:var(--muted);">—</div><div id="recoveryMessage" style="margin-top:8px;"></div></div>' +
      '</div>');
  }
  window.loadEvolveRecovery = async function () {
    injectRecoveryShell();
    var token = localStorage.getItem("fitai_token");
    var status = document.getElementById("recoveryStatus");
    if (!token) {
      if (status) { status.className = "alert alert-warn"; status.textContent = "Zaloguj się, aby zobaczyć Recovery."; }
      return;
    }
    var requestId = ++recoveryLoadSequence;
    ["recoverySummary","recoverySignals","recoveryHistory","recoveryTrend"].forEach(function(id){ var el=document.getElementById(id); if(el) el.innerHTML='<div class="spinner"></div>'; });
    try {
      var responses = await Promise.all([
        fetch("/app/recovery/today", {headers:{Authorization:"Bearer " + token}, cache:"no-store"}),
        fetch("/app/recovery/history?days=14", {headers:{Authorization:"Bearer " + token}, cache:"no-store"})
      ]);
      var response = responses[0], historyResponse = responses[1];
      var data = await response.json();
      var historyData = await historyResponse.json();
      if (requestId !== recoveryLoadSequence) return;
      if (!response.ok) throw new Error(data.detail || "Nie udało się pobrać Recovery.");
      if (!historyResponse.ok) throw new Error(historyData.detail || "Nie udało się pobrać historii Recovery.");
      document.getElementById("recoveryDate").textContent = data.date || "—";
      var score = data.readiness_score == null ? "—" : data.readiness_score + "/100";
      var label = data.status === "ready" ? "Gotowy" : data.status === "caution" ? "Uwaga" : data.status === "recovery" ? "Recovery" : "Za mało danych";
      document.getElementById("recoverySummary").innerHTML =
        '<div class="card" style="padding:20px;"><div style="font-size:10px;font-weight:700;text-transform:uppercase;color:var(--muted);">GOTOWOŚĆ</div><div style="font-size:30px;font-weight:700;margin-top:8px;">'+esc(score)+'</div><div style="font-size:12px;color:var(--muted);margin-top:4px;">'+esc(label)+'</div></div>' +
        '<div class="card" style="padding:20px;"><div style="font-size:10px;font-weight:700;text-transform:uppercase;color:var(--muted);">SYGNAŁY</div><div style="font-size:30px;font-weight:700;margin-top:8px;">'+esc(data.signal_count || 0)+'</div><div style="font-size:12px;color:var(--muted);margin-top:4px;">uwzględnionych dziś</div></div>';
      var labels=data.signal_labels||{}, signals=data.signals||{};
      document.getElementById("recoverySignals").innerHTML = Object.keys(signals).map(function(key){
        return '<div class="item-card" style="cursor:default;margin-bottom:8px;"><div class="item-card-head"><div class="item-card-title">'+esc(labels[key]||key)+'</div><div class="tag">'+esc(signals[key])+'/100</div></div></div>';
      }).join("") || '<div style="color:var(--muted);">Brak wystarczających danych. Uzupełnij dzisiejszy check-in.</div>';
      var trend = historyData.summary || {};
      document.getElementById("recoveryTrend").innerHTML =
        '<div class="grid-2">' +
        '<div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;">Średnia gotowość</div><div style="font-size:22px;font-weight:700;margin-top:4px;">'+esc(trend.average_readiness == null ? "—" : trend.average_readiness + "/100")+'</div></div>' +
        '<div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;">Dni z redukcją</div><div style="font-size:22px;font-weight:700;margin-top:4px;">'+esc(trend.constrained_days || 0)+'</div></div>' +
        '</div>';
      document.getElementById("recoveryHistory").innerHTML = (historyData.history || []).map(function(item){
        var score = item.readiness_score == null ? "—" : item.readiness_score + "/100";
        var effect = item.constraint === "reduce_volume_50" ? "−50%" : item.constraint === "reduce_volume_25" ? "−25%" : item.status === "ready" ? "pełna objętość" : "brak danych";
        return '<div class="item-card" style="cursor:default;margin-bottom:8px;"><div class="item-card-head"><div class="item-card-title">'+esc(item.date)+'</div><div class="tag">'+esc(score)+'</div></div><div class="item-card-meta">'+esc(effect)+'</div></div>';
      }).join("");
      document.getElementById("recoveryEffect").textContent = data.plan_effect || "Brak automatycznej zmiany planu.";
      document.getElementById("recoveryMessage").textContent = data.message || "";
      if (status) { status.className = "alert alert-hidden"; status.textContent = ""; }
    } catch (error) {
      if (requestId !== recoveryLoadSequence) return;
      if (status) { status.className = "alert alert-warn"; status.textContent = "⚠️ " + error.message; }
    }
  };
})();
</script>"""
    nutrition_shell_integration = """<script id="evolve-nutrition-shell-integration">

(function () {
  function nutritionEscape(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[char];
    });
  }
  var nutritionLoadSequence = 0;

  function injectNutritionShell() {
    if (document.getElementById("nutritionSummary")) return;
    var content = document.querySelector(".content");
    if (!content) return;
    var section =
      '<div class="tab-panel" id="tab-diet">' +
        '<div class="sec-head"><div><div style="font-family:\\'Syne\\',sans-serif;font-size:26px;font-weight:700;">Dieta 🥗</div>' +
        '<div style="font-size:13px;color:var(--muted);margin-top:4px;">Dzisiejsze spożycie, cele i reakcja systemu.</div></div>' +
        '<button class="btn btn-primary btn-sm" id="nutritionAddBtn" type="button">+ Dodaj posiłek</button></div>' +
        '<div id="nutritionStatus" class="alert alert-hidden" style="margin-bottom:16px;"></div>' +
        '<div id="nutritionSummary" class="grid-2" style="margin-bottom:16px;"></div>' +
        '<div id="nutritionResponse" class="card" style="padding:20px;margin-bottom:16px;"></div>' +
        '<div class="card" style="padding:20px;"><div class="sec-head" style="margin-bottom:12px;"><div style="font-weight:700;font-size:16px;">Dzisiejsze wpisy</div><div id="nutritionEntryCount" style="font-size:12px;color:var(--muted);">—</div></div>' +
        '<div id="nutritionEntries"><div class="spinner"></div></div></div>' +
      '</div>';
    content.insertAdjacentHTML("afterbegin", section);
    document.getElementById("nutritionAddBtn").addEventListener("click", function () {
      var name = window.prompt("Nazwa posiłku:");
      if (!name || !name.trim()) return;
      var kcal = Number(window.prompt("Kalorie (kcal):", "0"));
      var protein = Number(window.prompt("Białko (g):", "0"));
      if (!Number.isFinite(kcal) || kcal < 0 || !Number.isFinite(protein) || protein < 0) {
        window.alert("Podaj poprawne wartości.");
        return;
      }
      window.saveEvolveNutritionEntry({name:name.trim(), calories_kcal:kcal, protein_g:protein});
    });
  }

  window.loadEvolveNutrition = async function () {
    injectNutritionShell();
    var summaryEl = document.getElementById("nutritionSummary");
    var entriesEl = document.getElementById("nutritionEntries");
    var responseEl = document.getElementById("nutritionResponse");
    if (!summaryEl || !entriesEl || !responseEl) return;
    var requestId = ++nutritionLoadSequence;
    var token = localStorage.getItem("fitai_token");
    if (!token) {
      summaryEl.innerHTML = '<div class="card" style="padding:20px;">Zaloguj się, aby zobaczyć dietę.</div>';
      entriesEl.innerHTML = "";
      responseEl.innerHTML = "";
      return;
    }
    try {
      var headers = {Authorization: "Bearer " + token};
      var [todayResponse, responseSignal, adaptationResponse] = await Promise.all([
        fetch("/app/nutrition/today", {headers:headers, cache:"no-store"}),
        fetch("/app/nutrition/response?days=7", {headers:headers, cache:"no-store"}),
        fetch("/app/nutrition/adaptation?days=14", {headers:headers, cache:"no-store"})
      ]);
      var today = await todayResponse.json();
      var signal = await responseSignal.json();
      var adaptation = await adaptationResponse.json();
      if (requestId !== nutritionLoadSequence) return;
      if (!todayResponse.ok) throw new Error(today.detail || "Nie udało się pobrać diety.");
      if (!responseSignal.ok) throw new Error(signal.detail || "Nie udało się pobrać reakcji żywieniowej.");
      if (!adaptationResponse.ok) throw new Error(adaptation.detail || "Nie udało się pobrać propozycji adaptacji.");

      var totals = today.totals || {};
      var targets = today.targets || {};
      summaryEl.innerHTML =
        '<div class="card" style="padding:20px;"><div style="font-size:10px;font-weight:700;text-transform:uppercase;color:var(--muted);">KALORIE</div><div style="font-size:28px;font-weight:700;margin-top:8px;">' +
        nutritionEscape(totals.calories_kcal || 0) + ' / ' + nutritionEscape(targets.calories_kcal || 0) + ' kcal</div></div>' +
        '<div class="card" style="padding:20px;"><div style="font-size:10px;font-weight:700;text-transform:uppercase;color:var(--muted);">BIAŁKO</div><div style="font-size:28px;font-weight:700;margin-top:8px;">' +
        nutritionEscape(totals.protein_g || 0) + ' / ' + nutritionEscape(targets.protein_g || 0) + ' g</div></div>';
      document.getElementById("nutritionEntryCount").textContent = (today.entries || []).length + " wpisów";
      entriesEl.innerHTML = (today.entries || []).map(function (entry) {
        return '<div class="item-card" style="cursor:default;margin-bottom:8px;"><div class="item-card-head"><div class="item-card-title">' +
          nutritionEscape(entry.name) + '</div><button class="btn btn-ghost btn-sm" type="button" data-nutrition-delete="' + nutritionEscape(entry.id) + '">Usuń</button></div>' +
          '<div class="item-card-meta">' + nutritionEscape(entry.calories_kcal) + ' kcal · ' + nutritionEscape(entry.protein_g) + ' g białka</div></div>';
      }).join("") || '<div style="padding:20px;color:var(--muted);text-align:center;">Brak wpisów na dziś.</div>';

      responseEl.innerHTML = (signal.status === "insufficient_data"
        ? '<div style="font-weight:700;">Reakcja żywieniowa</div><div style="margin-top:8px;color:var(--muted);">' + nutritionEscape(signal.message) + '</div>'
        : '<div style="font-weight:700;">Reakcja żywieniowa</div><div style="margin-top:8px;">' + nutritionEscape(signal.message) + '</div>' +
          '<div style="margin-top:8px;color:var(--muted);">Średnio: ' + nutritionEscape(signal.averages.calories_kcal) + ' kcal · ' + nutritionEscape(signal.averages.protein_g) + ' g białka · ' + nutritionEscape(signal.logged_days) + ' dni danych</div>') +
        '<div style="border-top:1px solid var(--border);margin-top:16px;padding-top:16px;"><div style="font-weight:700;">Adaptacja celu</div>' +
        '<div style="margin-top:8px;color:var(--muted);">' + nutritionEscape(adaptation.reason || "Brak propozycji.") + '</div>' +
        '<div style="margin-top:8px;">' + nutritionEscape(adaptation.proposed_calories_kcal || today.targets.calories_kcal) + ' kcal · zmiana ' + nutritionEscape(adaptation.change_kcal || 0) + ' kcal</div>' +
        (adaptation.adaptation_allowed ? '<button class="btn btn-primary btn-sm" id="nutritionApplyAdaptation" type="button" style="margin-top:12px;">Zastosuj zmianę</button>' : '') +
        '</div>';
      var applyButton = document.getElementById("nutritionApplyAdaptation");
      if (applyButton) applyButton.addEventListener("click", async function () {
        applyButton.disabled = true;
        var applyResponse = await fetch("/app/nutrition/adaptation/apply?days=14", {method:"POST", headers:headers});
        var applyData = await applyResponse.json();
        if (!applyResponse.ok) {
          window.alert(applyData.detail || "Nie udało się zastosować zmiany.");
          applyButton.disabled = false;
          return;
        }
        window.loadEvolveNutrition();
      });

      Array.from(document.querySelectorAll("[data-nutrition-delete]")).forEach(function (button) {
        button.addEventListener("click", async function () {
          var deleteResponse = await fetch("/app/nutrition/entries/" + encodeURIComponent(button.getAttribute("data-nutrition-delete")), {
            method:"DELETE", headers:headers
          });
          if (!deleteResponse.ok) {
            var errorData = await deleteResponse.json();
            window.alert(errorData.detail || "Nie udało się usunąć wpisu.");
            return;
          }
          window.loadEvolveNutrition();
        });
      });
    } catch (error) {
      if (requestId !== nutritionLoadSequence) return;
      document.getElementById("nutritionStatus").className = "alert alert-warn";
      document.getElementById("nutritionStatus").textContent = "⚠️ " + error.message;
      entriesEl.innerHTML = '<div style="padding:20px;color:var(--muted);">Błąd ładowania danych.</div>';
    }
  };

  window.saveEvolveNutritionEntry = async function (payload) {
    var token = localStorage.getItem("fitai_token");
    if (!token) return;
    var response = await fetch("/app/nutrition/entries", {
      method:"POST",
      headers:{"Content-Type":"application/json", Authorization:"Bearer " + token},
      body:JSON.stringify(payload)
    });
    if (!response.ok) {
      var data = await response.json();
      window.alert(data.detail || "Nie udało się zapisać wpisu.");
      return;
    }
    window.loadEvolveNutrition();
  };
})();
</script>"""
    if 'id="evolve-my-day-shell-integration"' not in html:
        pos = html.rfind("</body>")
        if pos != -1:
            html = html[:pos] + evolve_shell_integration + html[pos:]
        else:
            html = html + evolve_shell_integration

    if 'id="evolve-recovery-shell-integration"' not in html:
        pos = html.rfind("</body>")
        if pos != -1:
            html = html[:pos] + recovery_shell_integration + html[pos:]
        else:
            html = html + recovery_shell_integration

    if 'id="evolve-nutrition-shell-integration"' not in html:
        pos = html.rfind("</body>")
        if pos != -1:
            html = html[:pos] + nutrition_shell_integration + html[pos:]
        else:
            html = html + nutrition_shell_integration

    if 'id="evolve-dashboard-first-style"' not in html:
        pos = html.find("</head>")
        if pos != -1:
            html = html[:pos] + dashboard_first_bootstrap + html[pos:]
        else:
            html = dashboard_first_bootstrap + html

    dashboard_boot = """<script id="evolve-dashboard-first-boot">
document.addEventListener('DOMContentLoaded', function () {
  // The landing page is legacy-only markup. The hosted EVOLVE experience is dashboard-first.
  var landing = document.getElementById('landingPage');
  var dashboard = document.getElementById('dashboardPage');
  if (landing) {
    landing.style.display = 'none';
    landing.setAttribute('aria-hidden', 'true');
  }
  if (dashboard) {
    dashboard.style.display = 'flex';
    dashboard.removeAttribute('aria-hidden');
  }
  // Keep the legacy initializer when available, but dashboard visibility must not depend on it.
  if (typeof initApp === 'function') initApp();
});
</script>"""
    if 'id="evolve-dashboard-first-boot"' not in html:
        pos = html.rfind("</body>")
        if pos != -1:
            html = html[:pos] + dashboard_boot + html[pos:]
        else:
            html = html + dashboard_boot

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