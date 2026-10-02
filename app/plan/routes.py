"""Plan Routes — weekly plan generation, current plan, and swaps."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.legacy_routes import (
    _build_weekly_plan,
    _enrich_exercises_with_progression,
    _is_profile_ready_for_plan,
)
from app.models import AssessmentDB, UserDB
from app.schemas import PlanGenerateRequest, PlanSwapRequest, WeeklyPlanSaveRequest

router = APIRouter(prefix="/app/plan", tags=["plan"])

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
    return {
        "ready": not missing_profile,
        "profile_ready": not missing_profile,
        "missing_profile": missing_profile,
        "assessment_ready": assessment is not None,
        "assessment_version": assessment.assessment_version if assessment else None,
        "personalization_level": "assessed" if assessment else "profile_only",
        "next": "generate_plan" if not missing_profile else "complete_profile",
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
<div class="card"><strong>Aktualny plan</strong><div id="days" class="muted" style="margin-top:12px">Ładowanie…</div></div></main>
<script>
const token=localStorage.getItem("fitai_token"), H=()=>({Authorization:"Bearer "+token}), out=document.getElementById("out");
async function api(path,opt={}){return fetch(path,{...opt,headers:{...H(),...(opt.headers||{})}})}
async function load(){if(!token){out.textContent="Zaloguj się, aby korzystać z planowania.";return}
 const rr=await api("/app/plan/readiness"), r=await rr.json(); document.getElementById("profile").textContent=r.profile_ready?"GOTOWY":"UZUPEŁNIJ"; document.getElementById("assessment").textContent=r.assessment_ready?"v"+r.assessment_version:"BRAK";
 const p=await (await api("/app/plan/current")).json(); document.getElementById("plan").textContent=p.days?.length? "GOTOWY":"BRAK"; render(p);
}
function render(p){const el=document.getElementById("days"); if(!p.days?.length){el.textContent="Brak planu. Wygeneruj pierwszy plan.";return} el.innerHTML=p.days.map(d=>'<div class="day"><b>'+d.day+'</b> · '+(d.workout?.title||'Trening')+'<div>'+((d.workout?.exercises||[]).map(e=>'<div class="ex"><span>'+e.name+'</span><span>'+(e.sets||0)+' × '+(e.reps||0)+(e.weight_kg?' · '+e.weight_kg+' kg':'')+'</span></div>').join(''))+'</div></div>').join('')}
document.getElementById("generate").onclick=async()=>{const r=await api("/app/plan/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({force:true})});const d=await r.json();out.textContent=r.ok?"Plan wygenerowany. Personalizacja: "+(d.personalization_level||"profile_only"):"Błąd: "+(d.detail||"nie udało się wygenerować");if(r.ok){render(d.plan);document.getElementById("plan").textContent="GOTOWY"}};
load();
</script></body></html>""")



@router.post("/generate", tags=["plan"])
def app_generate_plan(
    payload: PlanGenerateRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        if not _is_profile_ready_for_plan(user):
            raise HTTPException(status_code=400, detail="Najpierw uzupełnij pełny onboarding")
        if payload.force or not user.weekly_plan_json:
            plan = _build_weekly_plan(user)
            user.set_dict("weekly_plan_json", plan)
            # Wzbogać plan o sugestie progresji
            for day in plan.get("days", []):
                exercises = day.get("workout", {}).get("exercises", [])
                if exercises:
                    day["workout"]["exercises"] = _enrich_exercises_with_progression(exercises, user, session)
            user.set_dict("weekly_plan_json", plan)
            user.updated_at = datetime.now()
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                print(f"[FitAI][app_generate_plan] IntegrityError user_id={user.id}: {exc}")
                raise HTTPException(status_code=409, detail="Konflikt zapisu planu — spróbuj ponownie.")
            except SQLAlchemyError as exc:
                session.rollback()
                print(f"[FitAI][app_generate_plan] SQLAlchemyError user_id={user.id}: {exc}")
                raise HTTPException(status_code=500, detail="Database error — please try again later")
        return {
            "status": "ok",
            "plan": user.get_dict("weekly_plan_json"),
            "personalization_level": "assessed" if session.exec(
                select(AssessmentDB).where(AssessmentDB.user_id == user.id).order_by(AssessmentDB.assessment_version.desc())
            ).first() else "profile_only",
        }
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error — please try again later") from exc
    except Exception as exc:
        print(f"[FitAI][app_generate_plan] ERROR user_id={user.id} — {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Błąd generowania planu. Spróbuj ponownie.")


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
        db_user.updated_at = datetime.now().isoformat()
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

        user.set_dict("weekly_plan_json", plan)
        user.updated_at = datetime.now().isoformat()
        session.commit()
        return {"status": "ok", "plan": plan}
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error — please try again later") from exc
