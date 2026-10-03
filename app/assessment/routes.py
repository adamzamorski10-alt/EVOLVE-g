"""Baseline assessment API and focused setup UI."""

from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import AssessmentDB, UserDB
from app.schemas import AssessmentRequest

router = APIRouter(prefix="/app/assessment", tags=["assessment"])


def _serialize(row: AssessmentDB) -> dict:
    return {
        "id": row.id,
        "version": row.assessment_version,
        "status": row.status,
        "assessment_date": row.assessment_date.isoformat(),
        "training_level": row.training_level,
        "training_experience_years": row.training_experience_years,
        "sessions_per_week": row.sessions_per_week,
        "availability_hours_per_week": row.availability_hours_per_week,
        "recovery_score": row.recovery_score,
        "basketball_level": row.basketball_level,
        "shooting_pct": row.shooting_pct,
        "free_throw_pct": row.free_throw_pct,
        "sprint_30m_seconds": row.sprint_30m_seconds,
        "vertical_jump_cm": row.vertical_jump_cm,
        "metrics": row.data(),
        "notes": row.notes,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/latest")
def get_latest_assessment(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    row = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc(), AssessmentDB.created_at.desc())
    ).first()
    return {
        "has_assessment": row is not None,
        "assessment": _serialize(row) if row else None,
    }


@router.post("")
def create_assessment(
    payload: AssessmentRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not payload.has_baseline:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Podaj co najmniej jeden wynik bazowy assessmentu.")

    previous = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc())
    ).first()
    version = (previous.assessment_version + 1) if previous else 1
    row = AssessmentDB(
        user_id=user.id,
        assessment_version=version,
        status="completed",
        assessment_date=date.today(),
        training_level=payload.training_level,
        training_experience_years=payload.training_experience_years,
        sessions_per_week=payload.sessions_per_week,
        availability_hours_per_week=payload.availability_hours_per_week,
        recovery_score=payload.recovery_score,
        basketball_level=payload.basketball_level,
        shooting_pct=payload.shooting_pct,
        free_throw_pct=payload.free_throw_pct,
        sprint_30m_seconds=payload.sprint_30m_seconds,
        vertical_jump_cm=payload.vertical_jump_cm,
        assessment_json=json.dumps(payload.metrics, ensure_ascii=False),
        notes=payload.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return {"status": "created", "assessment": _serialize(row)}


@router.get("/ui", response_class=HTMLResponse)
def assessment_ui():
    return HTMLResponse("""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVOLVE · Assessment</title>
<style>
body{margin:0;background:#090b10;color:#f5f7fb;font:15px system-ui;display:flex;justify-content:center;padding:32px}
main{width:min(760px,100%)}.card{background:#121620;border:1px solid #283041;border-radius:18px;padding:24px;margin-bottom:16px}
h1{margin:0 0 6px}p{color:#aeb7c8}label{display:block;margin:14px 0 6px;color:#cbd3e1}
input,select,textarea{width:100%;box-sizing:border-box;background:#0d1118;color:#fff;border:1px solid #30394a;border-radius:10px;padding:11px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:620px){.grid{grid-template-columns:1fr}}
button{border:0;border-radius:11px;padding:12px 16px;background:#8b5cf6;color:#fff;font-weight:800;cursor:pointer}
.badge{display:inline-block;background:#1b2331;border-radius:999px;padding:6px 10px;color:#cdd6e6}
#status{margin-top:14px;color:#aeb7c8}.links{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.links a{color:#ddd;text-decoration:none;border:1px solid #30394a;padding:10px 13px;border-radius:10px}
</style></head><body><main>
<div class="card"><span class="badge">EVOLVE · CORE</span><h1>Assessment początkowy</h1><p>Zapisz realny punkt startowy. Kolejne assessmenty tworzą wersje i nie nadpisują historii.</p></div>
<div class="card"><form id="f">
<div class="grid">
<div><label>Poziom treningowy</label><select name="training_level"><option value="">—</option><option>początkujący</option><option>średniozaawansowany</option><option>zaawansowany</option></select></div>
<div><label>Lata doświadczenia</label><input name="training_experience_years" type="number" min="0" step=".5"></div>
<div><label>Sesje / tydzień</label><input name="sessions_per_week" type="number" min="0" max="14"></div>
<div><label>Dostępność h / tydzień</label><input name="availability_hours_per_week" type="number" min="0" max="168" step=".5"></div>
<div><label>Recovery 1–10</label><input name="recovery_score" type="number" min="1" max="10"></div>
<div><label>Poziom koszykarski</label><select name="basketball_level"><option value="">—</option><option>początkujący</option><option>średniozaawansowany</option><option>zaawansowany</option></select></div>
<div><label>Skuteczność rzutów %</label><input name="shooting_pct" type="number" min="0" max="100" step=".1"></div>
<div><label>FT %</label><input name="free_throw_pct" type="number" min="0" max="100" step=".1"></div>
<div><label>Sprint 30 m (s)</label><input name="sprint_30m_seconds" type="number" min=".1" max="30" step=".01"></div>
<div><label>Wyskok (cm)</label><input name="vertical_jump_cm" type="number" min="0" max="150" step=".1"></div>
</div>
<label>Notatki</label><textarea name="notes" rows="4" maxlength="3000"></textarea>
<div style="margin-top:18px"><button>Zapisz assessment</button></div><div id="status"></div></form></div>
<div class="card"><strong>Ostatni assessment</strong><pre id="latest" style="white-space:pre-wrap;color:#aeb7c8"></pre><pre id="history" style="white-space:pre-wrap;color:#7f8aa0"></pre>
<div class="links"><a href="/app/plan/ui">Planowanie</a><a href="/app/training/today-ui">Mój dzień</a><a href="/">Aplikacja</a></div></div>
<script>
const token=localStorage.getItem("fitai_token"), statusEl=document.getElementById("status"), latest=document.getElementById("latest");
const n=v=>v===""?null:Number(v);
async function load(){if(!token){statusEl.textContent="Zaloguj się, aby zapisać assessment.";return}
 const r=await fetch("/app/assessment/latest",{headers:{Authorization:"Bearer "+token}}); const d=await r.json();
 latest.textContent=d.has_assessment?JSON.stringify(d.assessment,null,2):"Brak assessmentu — pierwszy zapis utworzy wersję 1.";
}
document.getElementById("f").addEventListener("submit",async e=>{e.preventDefault(); if(!token){statusEl.textContent="Brak sesji logowania.";return}
 const f=new FormData(e.target), p={training_level:f.get("training_level")||null,training_experience_years:n(f.get("training_experience_years")),sessions_per_week:n(f.get("sessions_per_week")),availability_hours_per_week:n(f.get("availability_hours_per_week")),recovery_score:n(f.get("recovery_score")),basketball_level:f.get("basketball_level")||null,shooting_pct:n(f.get("shooting_pct")),free_throw_pct:n(f.get("free_throw_pct")),sprint_30m_seconds:n(f.get("sprint_30m_seconds")),vertical_jump_cm:n(f.get("vertical_jump_cm")),notes:f.get("notes")||"",metrics:{}};
 const r=await fetch("/app/assessment",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+token},body:JSON.stringify(p)}); const d=await r.json(); statusEl.textContent=r.ok?"Assessment zapisany — wersja "+d.assessment.version+".":"Błąd: "+(d.detail||"nie udało się zapisać"); if(r.ok) load();
});
load();
async function loadAssessmentHistory(){
 if(!token || !history){return}
 const r=await fetch("/app/assessment/history",{headers:{Authorization:"Bearer "+token}});
 if(!r.ok){return}
 const d=await r.json();
 history.textContent=d.count?d.assessments.map(a=>"v"+a.version+" · "+a.assessment_date+" · "+(a.status||"completed")).join("\n"):"Brak zapisanych wersji.";
}
loadAssessmentHistory();
</script></main></body></html>""")


@router.get("/history")
def get_assessment_history(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc(), AssessmentDB.created_at.desc())
    ).all()
    return {"count": len(rows), "assessments": [_serialize(row) for row in rows]}