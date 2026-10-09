"""Plan Routes — weekly plan generation, current plan, and swaps."""

import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.legacy_routes import _is_profile_ready_for_plan
from app.plan.deterministic import _normalize_weekday, build_deterministic_plan
from app.plan.progress_evidence import build_planning_progress_evidence
from app.training.history import list_completed_training_history
from app.training.progress import build_progress_evidence
from app.plan.rolling import build_rolling_horizon
from app.models import AssessmentDB, UserDB
from app.schemas import PlanGenerateRequest, PlanSwapRequest, TrainingAvailabilityRequest, WeeklyPlanSaveRequest

router = APIRouter(prefix="/app/plan", tags=["plan"])


@router.get("/availability", tags=["plan"])
def get_training_availability(user: UserDB = Depends(get_current_user)):
    """Return the current user's optional weekly training-day availability."""
    return user.get_dict("training_availability_json")


@router.put("/availability", tags=["plan"])
def set_training_availability(
    payload: TrainingAvailabilityRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Persist validated weekly availability; changes invalidate plan provenance."""
    normalized = [_normalize_weekday(day) for day in payload.days]
    if any(day is None for day in normalized):
        raise HTTPException(
            status_code=422,
            detail="Podaj prawidłowe dni tygodnia po polsku, np. Środa lub Sobota.",
        )
    canonical_days = list(dict.fromkeys(day for day in normalized if day is not None))
    if not canonical_days:
        raise HTTPException(status_code=422, detail="Wybierz co najmniej jeden dzień dostępności.")

    canonical_windows = {}
    for raw_day, window in payload.windows.items():
        day = _normalize_weekday(raw_day)
        if day is None or day not in canonical_days:
            raise HTTPException(
                status_code=422,
                detail="Okna godzinowe mogą dotyczyć wyłącznie prawidłowych, zaznaczonych dni.",
            )
        canonical_windows[day] = window.model_dump()
    user.set_dict(
        "training_availability_json",
        {
            "days": canonical_days,
            "windows": canonical_windows,
            "session_duration_minutes": payload.session_duration_minutes,
        },
    )
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user.get_dict("training_availability_json")


def _profile_inputs(user: UserDB) -> dict:
    return {
        "goal": user.goal,
        "frequency": user.frequency,
        "sports": user.get_list("sports_json"),
        "training_focus": user.get_list("training_focus_json"),
        "improvement_areas": user.get_list("improvement_areas_json"),
        "available_equipment": user.get_list("available_equipment_json"),
        "avoid_exercises": user.get_list("avoid_exercises_json"),
        "sport_focus": user.sport_focus,
        "sport_specialization": user.sport_specialization,
        "sport_training_days": user.get_list("sport_training_days_json"),
        "training_availability": user.get_dict("training_availability_json"),
    }


def _assessment_inputs(assessment: AssessmentDB | None) -> dict | None:
    if assessment is None:
        return None
    return {
        "id": assessment.id,
        "version": assessment.assessment_version,
        "training_level": assessment.training_level,
        "training_experience_years": assessment.training_experience_years,
        "sessions_per_week": assessment.sessions_per_week,
        "availability_hours_per_week": assessment.availability_hours_per_week,
        "recovery_score": assessment.recovery_score,
        "basketball_level": assessment.basketball_level,
        "shooting_pct": assessment.shooting_pct,
        "free_throw_pct": assessment.free_throw_pct,
        "sprint_30m_seconds": assessment.sprint_30m_seconds,
        "vertical_jump_cm": assessment.vertical_jump_cm,
        "metrics": assessment.data(),
    }


def _fingerprint(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _planning_progress_fingerprint(progress_evidence: list[dict]) -> str:
    """Hash only stable evidence fields; exclude non-JSON temporal snapshots."""
    stable = [
        {
            "status": item.get("status"),
            "sufficient_data": item.get("sufficient_data"),
            "exercise_key": item.get("exercise_key"),
            "reason_codes": item.get("reason_codes") or [],
            "material_change": bool(item.get("material_change")),
            "changes": item.get("changes") or {},
        }
        for item in progress_evidence
        if isinstance(item, dict)
    ]
    return _fingerprint(stable)


def _planning_progress_evidence(session: Session, user_id: str) -> list[dict]:
    """Build user-scoped, read-only progress evidence for the planner."""
    history = list_completed_training_history(session, user_id, limit=100)
    exercise_keys = sorted({
        str(exercise.get("exercise_key"))
        for item in history
        for exercise in item.get("exercises", [])
        if exercise.get("exercise_key")
    })
    return [
        build_planning_progress_evidence(
            build_progress_evidence(history, exercise_key=exercise_key)
        )
        for exercise_key in exercise_keys
    ]


@router.get("/readiness", tags=["plan"])
def planning_readiness(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Explain exactly which core-loop inputs are ready for plan generation."""
    missing_profile = []
    if not user.name: missing_profile.append("name")
    if not user.goal: missing_profile.append("goal")
    if not user.frequency: missing_profile.append("frequency")
    if not user.weight: missing_profile.append("weight")
    if not user.target_weight: missing_profile.append("target_weight")
    assessment = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc())
    ).first()
    profile_inputs = _profile_inputs(user)
    assessment_inputs = _assessment_inputs(assessment)
    current_plan = user.get_dict("weekly_plan_json") if user.weekly_plan_json else {}
    provenance = current_plan.get("_evolve_core", {}) if isinstance(current_plan, dict) else {}
    planning_progress = _planning_progress_evidence(session, user.id)
    progress_fingerprint = _planning_progress_fingerprint(planning_progress)
    profile_stale = bool(provenance.get("profile_fingerprint")) and provenance.get("profile_fingerprint") != _fingerprint(profile_inputs)
    assessment_stale = bool(provenance.get("assessment_fingerprint")) and provenance.get("assessment_fingerprint") != _fingerprint(assessment_inputs)
    progress_stale = bool(provenance.get("progress_fingerprint")) and provenance.get("progress_fingerprint") != progress_fingerprint
    plan_stale = bool(user.weekly_plan_json) and (profile_stale or assessment_stale or progress_stale)
    assessment_ready = assessment is not None
    return {
        "ready": not missing_profile and assessment_ready,
        "profile_ready": not missing_profile,
        "missing_profile": missing_profile,
        "assessment_ready": assessment_ready,
        "assessment_version": assessment.assessment_version if assessment else None,
        "assessment_id": assessment.id if assessment else None,
        "plan_exists": bool(user.weekly_plan_json),
        "plan_stale": plan_stale,
        "profile_stale": profile_stale,
        "assessment_stale": assessment_stale,
        "progress_stale": progress_stale,
        "personalization_level": "assessed" if assessment else "profile_only",
        "next": "complete_profile" if missing_profile else ("complete_assessment" if not assessment else ("regenerate_plan" if plan_stale else "generate_plan")),
    }


@router.get("/ui", response_class=HTMLResponse)
def plan_ui():
    return HTMLResponse("""<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVOLVE · Planowanie</title><style>
body{margin:0;background:#090b10;color:#f5f7fb;font:15px system-ui;padding:32px}main{width:min(900px,100%);margin:auto}
.card{background:#121620;border:1px solid #283041;border-radius:18px;padding:22px;margin-bottom:16px}h1{margin:0 0 8px}.muted{color:#aeb7c8}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media(max-width:700px){.grid{grid-template-columns:1fr}}
.k{font-size:12px;color:#8f9aae;text-transform:uppercase}.v{font-size:24px;font-weight:800;margin-top:4px}
button,a{border-radius:10px;padding:11px 14px;font-weight:800;text-decoration:none;display:inline-block}button{border:0;background:#8b5cf6;color:white;cursor:pointer}a{border:1px solid #30394a;color:#ddd}
#out{white-space:pre-wrap;color:#cbd3e1}.day{border-top:1px solid #293143;padding:14px 0}.ex{display:flex;justify-content:space-between;gap:12px;padding:6px 0;color:#cbd3e1}
</style></head><body><main><div class="card"><div class="k">EVOLVE · CORE LOOP</div><h1>Planowanie treningu</h1><p class="muted">Profil → Assessment → Plan. Generator pozostaje deterministyczny; assessment jest zapisywany jako wersjonowany punkt odniesienia.</p></div>
<div class="card"><div class="grid"><div><div class="k">Profil</div><div class="v" id="profile">—</div></div><div><div class="k">Assessment</div><div class="v" id="assessment">—</div></div><div><div class="k">Plan</div><div class="v" id="plan">—</div></div></div><div style="margin-top:18px;display:flex;gap:10px;flex-wrap:wrap"><button id="generate">Wygeneruj plan</button><a href="/app/assessment/ui">Assessment</a><a href="/app/training/today-ui">Mój dzień</a></div><div id="out"></div></div>
<div class="card"><strong>Dostępność treningowa</strong><p class="muted">Wybierz dni, w których realnie możesz trenować. Plan nie będzie umieszczał sesji poza zaznaczonymi dniami. Jeśli wcześniej nie zapisano dostępności, nie obowiązują dodatkowe ograniczenia.</p><div id="availabilityDays" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0"></div><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><button id="saveAvailability" type="button">Zapisz dostępność</button><span id="availabilityStatus" class="muted" role="status" aria-live="polite"></span></div></div>
<div class="card"><strong>Aktualny plan tygodniowy</strong><div id="days" class="muted" style="margin-top:12px">Ładowanie…</div></div>
<div class="card"><strong>Najbliższe 14 dni</strong><p class="muted">Datowany widok planu. Ukończenie jest potwierdzane wyłącznie przez historię rzeczywistych sesji.</p><div id="rollingStatus" class="muted">Ładowanie horyzontu…</div><div id="rollingHorizon"></div><div style="margin-top:14px"><a href="/app/training/session-ui">Otwórz wykonanie treningu</a></div></div></main>
<script>
const token=localStorage.getItem("fitai_token"), H=()=>({Authorization:"Bearer "+token}), out=document.getElementById("out");
async function api(path,opt={}){return fetch(path,{...opt,headers:{...H(),...(opt.headers||{})}})}
const WEEKDAYS=["Poniedziałek","Wtorek","Środa","Czwartek","Piątek","Sobota","Niedziela"];
function renderAvailability(days){const el=document.getElementById("availabilityDays");el.innerHTML=WEEKDAYS.map(day=>'<label style="display:flex;align-items:center;gap:8px;padding:10px;border:1px solid #30394a;border-radius:10px"><input type="checkbox" name="availabilityDay" value="'+day+'" '+(days.includes(day)?'checked':'')+' style="accent-color:#8b5cf6;width:18px;height:18px"> '+day+'</label>').join("")}
async function loadAvailability(){const status=document.getElementById("availabilityStatus");try{const r=await api("/app/plan/availability"),data=await r.json();if(!r.ok)throw new Error(data.detail||"Nie udało się pobrać dostępności");const days=Array.isArray(data.days)&&data.days.length?data.days:WEEKDAYS;renderAvailability(days);status.textContent=Array.isArray(data.days)&&data.days.length?"Zapisana dostępność":"Nie ustawiono ograniczeń — wszystkie dni są dostępne."}catch(error){status.textContent="Błąd ładowania: "+error.message}}
document.getElementById("saveAvailability").onclick=async()=>{const status=document.getElementById("availabilityStatus"),days=Array.from(document.querySelectorAll('input[name="availabilityDay"]:checked')).map(el=>el.value);if(!days.length){status.textContent="Zaznacz co najmniej jeden dzień.";return}const button=document.getElementById("saveAvailability");button.disabled=true;status.textContent="Zapisywanie…";try{const r=await api("/app/plan/availability",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({days})}),data=await r.json();if(!r.ok)throw new Error(data.detail||"Nie udało się zapisać dostępności");renderAvailability(data.days||days);status.textContent="Dostępność zapisana. Istniejący plan może wymagać ponownego wygenerowania.";await load()}catch(error){status.textContent="Błąd zapisu: "+error.message}finally{button.disabled=false}};
async function load(){if(!token){out.textContent="Zaloguj się, aby korzystać z planowania.";return}
 const rr=await api("/app/plan/readiness"), r=await rr.json(); document.getElementById("profile").textContent=r.profile_ready?"GOTOWY":"UZUPEŁNIJ"; document.getElementById("assessment").textContent=r.assessment_ready?"v"+r.assessment_version:"BRAK";
 const p=await (await api("/app/plan/current")).json(); document.getElementById("plan").textContent=p.days?.length? "GOTOWY":"BRAK"; render(p);
 await loadRolling();
 await loadAvailability();
}
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(ch){if(ch==="&")return "&amp;";if(ch==="<")return "&lt;";if(ch===">")return "&gt;";if(ch.charCodeAt(0)===34)return "&quot;";return "&#39;"})}
function render(p){const el=document.getElementById("days"); if(!p.days?.length){el.textContent="Brak planu. Wygeneruj pierwszy plan.";return} el.innerHTML=p.days.map(d=>'<div class="day"><b>'+esc(d.day)+'</b> · '+esc(d.workout?.title||'Trening')+'<div>'+((d.workout?.exercises||[]).map(e=>'<div class="ex"><span>'+esc(e.name)+'</span><span>'+(Number(e.sets)||0)+' × '+(Number(e.reps)||0)+(e.weight_kg?' · '+esc(e.weight_kg)+' kg':'')+'</span></div>').join(''))+'</div></div>').join('')}
async function loadRolling(){const status=document.getElementById("rollingStatus"),el=document.getElementById("rollingHorizon");try{const response=await api("/app/plan/rolling?horizon_days=14"),data=await response.json();if(!response.ok)throw new Error(data.detail||"Nie udało się pobrać horyzontu");status.textContent="Okres: "+data.horizon_start+" — "+data.horizon_end+" · "+(data.sufficient_data?"dane dostępne":"brak wystarczających danych")+" · plan: "+((data.effective_plan?.source==="adaptive"?"adaptacyjny v"+data.effective_plan.version:"bazowy")+(data.effective_plan?.stale?" · plan nieaktualny — odśwież go przed treningiem":""));const upcoming=data.upcoming_sessions||[],plannedDays=data.planned_days||upcoming,completed=data.completed_sessions||[];const rows=plannedDays.map(item=>'<div class="day"><b>'+esc(item.scheduled_date)+'</b> · '+esc(item.day||"Trening")+' <span class="muted">· '+esc(item.status==="rest"?"odpoczynek":item.status==="completed"?"ukończono":"zaplanowany")+'</span><div style="margin-top:5px;font-weight:700">'+esc(item.workout?.title||(item.day_type==="rest"?"Regeneracja / odpoczynek":"Sesja treningowa"))+'</div>'+((item.workout?.exercises||[]).map(e=>'<div class="ex"><span>'+esc(e.name)+'</span><span>'+(Number(e.sets)||0)+' × '+(Number(e.reps)||0)+'</span></div>').join(''))+'</div>').join("");const done=completed.map(item=>'<div class="day"><b>'+esc(item.session_date||"")+'</b> · <span style="color:#86efac">Ukończono</span><div>'+esc(item.session_name||item.title||"Zarejestrowana sesja")+'</div></div>').join("");el.innerHTML=(plannedDays.length?rows:'<p class="muted">Brak zaplanowanych dni w tym horyzoncie.</p>')+(done?'<h3>Historia ukończonych sesji</h3>'+done:"");}catch(error){status.textContent="Nie udało się załadować horyzontu: "+error.message;el.textContent=""}}
document.getElementById("generate").onclick=async()=>{const r=await api("/app/plan/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({force:true})});const d=await r.json();out.textContent=r.ok?"Plan wygenerowany. Personalizacja: "+(d.personalization_level||"profile_only"):"Błąd: "+(d.detail||"nie udało się wygenerować");if(r.ok){render(d.plan);document.getElementById("plan").textContent="GOTOWY";await loadRolling()}};
load();
</script></body></html>""")



@router.get("/rolling", tags=["plan"])
def app_get_rolling_plan(
    horizon_days: int = 14,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return a fresh user-scoped rolling view; never treat planned items as completed."""
    # Resolve the same applied adaptive plan used by canonical execution, but do not
    # spread today's transient recovery-volume constraint across future scheduled days.
    from app.training.routes import _base_plan_is_stale, _effective_plan, _load_base_plan

    base_plan = _load_base_plan(user)
    effective_plan, plan_meta = _effective_plan(user, session, apply_recovery=False)
    completed_history = list_completed_training_history(session, user.id, limit=100)
    result = build_rolling_horizon(
        effective_plan if isinstance(effective_plan, dict) else None,
        horizon_start=datetime.now().date(),
        horizon_days=horizon_days,
        completed_sessions=completed_history,
    )
    result["effective_plan"] = {
        "source": plan_meta.get("source", "base"),
        "version": plan_meta.get("version", 0),
        "stale": _base_plan_is_stale(user, session, base_plan),
    }
    return result


@router.post("/generate", tags=["plan"])
def app_generate_plan(
    payload: PlanGenerateRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not _is_profile_ready_for_plan(user):
        raise HTTPException(status_code=400, detail="Najpierw uzupełnij pełny profil.")

    assessment = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc(), AssessmentDB.created_at.desc())
    ).first()
    if assessment is None:
        raise HTTPException(status_code=400, detail="Najpierw wykonaj assessment początkowy.")

    profile_inputs = _profile_inputs(user)
    assessment_inputs = _assessment_inputs(assessment)
    current = user.get_dict("weekly_plan_json") if user.weekly_plan_json else {}
    current_provenance = current.get("_evolve_core", {}) if isinstance(current, dict) else {}
    planning_progress = _planning_progress_evidence(session, user.id)
    progress_fingerprint = _planning_progress_fingerprint(planning_progress)
    stale = (
        current_provenance.get("profile_fingerprint") != _fingerprint(profile_inputs)
        or current_provenance.get("assessment_fingerprint") != _fingerprint(assessment_inputs)
        or current_provenance.get("progress_fingerprint") != progress_fingerprint
    )
    reused_existing = bool(user.weekly_plan_json) and not payload.force and not stale

    if not reused_existing:
        plan = build_deterministic_plan(user, assessment, planning_progress)
        completed_history = list_completed_training_history(session, user.id, limit=100)
        plan["rolling_plan"] = build_rolling_horizon(
            plan,
            horizon_start=datetime.now().date(),
            completed_sessions=completed_history,
        )
        plan["generated_at"] = datetime.now().isoformat()
        plan["_evolve_core"] = {
            "schema_version": 2,
            "planning_source": "deterministic-v2",
            "profile_inputs": profile_inputs,
            "profile_fingerprint": _fingerprint(profile_inputs),
            "assessment_id": assessment.id,
            "assessment_version": assessment.assessment_version,
            "assessment_inputs": assessment_inputs,
            "assessment_fingerprint": _fingerprint(assessment_inputs),
            "progress_fingerprint": progress_fingerprint,
            "progress_evidence_count": len(planning_progress),
        }
        user.set_dict("weekly_plan_json", plan)
        user.updated_at = datetime.now()
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error — please try again later") from exc

    return {
        "status": "ok",
        "plan": user.get_dict("weekly_plan_json"),
        "personalization_level": "assessed",
        "reused_existing": reused_existing,
    }


@router.get("/current", tags=["plan"])
def app_get_plan(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    GET /app/plan

    Zwraca tygodniowy plan użytkownika.
    Gwarantuje klucze: days, diet, training, generated_at, weekly_goal
    — nawet gdy plan jest pusty — żeby frontend nigdy nie dostał KeyError.
    """
    _EMPTY: dict = {
        "days": [],
        "diet": "",
        "training": "",
        "generated_at": None,
        "weekly_goal": None,
        "source": "empty",
    }

    try:
        if not user.weekly_plan_json:
            print(f"[FitAI][app_get_plan] user_id={user.id} — brak weekly_plan_json, zwracam pustą strukturę")
            return _EMPTY

        raw = user.get_dict("weekly_plan_json")
        if not raw or not isinstance(raw, dict):
            print(f"[FitAI][app_get_plan] user_id={user.id} — weekly_plan_json jest null/pusty po deserializacji")
            return _EMPTY

        diet_by_day: dict = {}
        training_by_day: dict = {}

        for day_entry in raw.get("days", []):
            day_name = day_entry.get("day", "")
            if not day_name:
                continue
            diet_by_day[day_name] = day_entry.get("meals", [])
            training_by_day[day_name] = {
                "title": day_entry.get("workout", {}).get("title", ""),
                "focus": day_entry.get("workout", {}).get("focus", ""),
                "exercises": day_entry.get("workout", {}).get("exercises", []),
                "day_type": day_entry.get("day_type", ""),
                "macros": day_entry.get("macros", {}),
                "is_sport_session": day_entry.get("is_sport_session", False),
            }

        result = {
            **raw,
            "diet": diet_by_day if diet_by_day else {},
            "training": training_by_day if training_by_day else {},
            "source": "database",
        }
        result.setdefault("days", [])
        result.setdefault("generated_at", None)
        result.setdefault("weekly_goal", None)

        print(f"[FitAI][app_get_plan] user_id={user.id} — OK, dni={len(raw.get('days', []))}")
        return result

    except json.JSONDecodeError as exc:
        print(f"[FitAI][app_get_plan] ERROR user_id={user.id} — Uszkodzony JSON: {exc}")
        return {**_EMPTY, "error_hint": "corrupted_plan_json", "source": "error"}
    except SQLAlchemyError as exc:
        print(f"[FitAI][app_get_plan] DB ERROR user_id={user.id} — {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Database error — please try again later") from exc
    except Exception as exc:
        print(f"[FitAI][app_get_plan] ERROR user_id={user.id} — {type(exc).__name__}: {exc}")
        return {**_EMPTY, "source": "error"}


@router.put("/current", tags=["plan"])
def app_save_plan(
    payload: WeeklyPlanSaveRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not isinstance(payload.plan, dict):
        raise HTTPException(status_code=422, detail="plan musi być obiektem JSON")

    plan = dict(payload.plan)
    plan.setdefault("days", [])
    plan.setdefault("diet", {})
    plan.setdefault("training", {})
    plan.setdefault("generated_at", datetime.now().isoformat())
    plan["source"] = "user_saved"

    try:
        db_user = session.get(UserDB, user.id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
        db_user.set_dict("weekly_plan_json", plan)
        db_user.updated_at = datetime.now()
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return {"status": "ok", "plan": db_user.get_dict("weekly_plan_json")}
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error — please try again later") from exc


@router.post("/swap", tags=["plan"])
def app_swap_plan_item(
    payload: PlanSwapRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        if not user.weekly_plan_json:
            raise HTTPException(status_code=404, detail="Plan nie został jeszcze wygenerowany")
        plan = user.get_dict("weekly_plan_json")
        days = plan.get("days", [])
        if not (0 <= payload.day_index < len(days)):
            raise HTTPException(status_code=400, detail="Niepoprawny day_index")
        day = days[payload.day_index]
        section = (payload.section or "").strip().lower()

        if section == "meal":
            items = day.get("meals", [])
            if not (0 <= payload.item_index < len(items)):
                raise HTTPException(status_code=400, detail="Niepoprawny item_index dla meal")
            item = items[payload.item_index]
            alts = item.get("alternatives", [])
            if not (0 <= payload.alternative_index < len(alts)):
                raise HTTPException(status_code=400, detail="Niepoprawny alternative_index")
            current = {"name": item["name"], "kcal": item["kcal"]}
            selected = alts[payload.alternative_index]
            item.update({"name": selected["name"], "kcal": selected["kcal"]})
            item["alternatives"] = [a for i, a in enumerate(alts) if i != payload.alternative_index] + [current]

        elif section == "exercise":
            exercises = day.get("workout", {}).get("exercises", [])
            if not (0 <= payload.item_index < len(exercises)):
                raise HTTPException(status_code=400, detail="Niepoprawny item_index dla exercise")
            item = exercises[payload.item_index]
            alts = item.get("alternatives", [])
            if not (0 <= payload.alternative_index < len(alts)):
                raise HTTPException(status_code=400, detail="Niepoprawny alternative_index")
            current = {k: item.get(k) for k in ["name", "sets", "reps", "notes", "how_to"]}
            selected = alts[payload.alternative_index]
            item.update({k: selected.get(k) for k in ["name", "sets", "reps", "notes", "how_to"]})
            item["alternatives"] = [a for i, a in enumerate(alts) if i != payload.alternative_index] + [current]
        else:
            raise HTTPException(status_code=400, detail="section musi być meal albo exercise")

        # get_current_user() returns a detached principal loaded in its own session.
        # Always re-load the canonical row in the request session before mutating it.
        db_user = session.get(UserDB, user.id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
        db_user.set_dict("weekly_plan_json", plan)
        db_user.updated_at = datetime.now()
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return {"status": "ok", "plan": db_user.get_dict("weekly_plan_json")}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error — please try again later") from exc
