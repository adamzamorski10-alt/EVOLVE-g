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
      startLink.textContent = session.id ? "Wznów trening" : (data.has_workout ? "Rozpocznij trening" : "Brak treningu");
      if (data.has_workout || session.id) {
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

  function installMyDayRoutingHook() {
    if (window.__evolveMyDayRoutingHookInstalled) return;
    if (typeof window.showTab !== "function") return;
    var originalShowTab = window.showTab;
    window.showTab = function (tab) {
      var result = originalShowTab.apply(this, arguments);
      if (tab === "my-day") {
        window.loadEvolveMyDay();
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