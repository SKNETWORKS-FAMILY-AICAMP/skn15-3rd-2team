# llm.py — OpenAI LLM(파싱/질문/매핑) + 로컬 임베딩 + expanded_roles 강화
from __future__ import annotations
import os, sys, json, hashlib, pathlib, time, re
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import httpx
import numpy as np
import faiss
from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "jobkorea_cli"

from .prompts import (
    PARSE_SYS,
    ASK_REQUIRED_BATCH_SYS,
    ASK_OPTIONAL_BATCH_SYS,
    MAP_SYS,
    PROJECT_KEYWORD_SYS,
)
from .models import Spec, AskTurn

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","").strip()
OPENAI_MODEL   = os.getenv("OPENAI_MODEL","gpt-4o-mini").strip()

EMBED_BACKEND  = os.getenv("EMBED_BACKEND","local").strip().lower()
EMBED_MODEL_ID = os.getenv("EMBED_MODEL","intfloat/multilingual-e5-base").strip()
ALLOW_TRUST_REMOTE_CODE = os.getenv("ALLOW_TRUST_REMOTE_CODE","0")=="1"

PROJECT_KEYWORD_SOURCE = os.getenv("PROJECT_KEYWORD_SOURCE","llm").strip().lower()
PROJECT_KEYWORD_TOPK   = int(os.getenv("PROJECT_KEYWORD_TOPK","12"))

CHAT_URL  = "https://api.openai.com/v1/chat/completions"

CACHE_DIR = pathlib.Path(".cache_llm"); CACHE_DIR.mkdir(exist_ok=True)

# ---------- HTTP ----------
_client: Optional[httpx.AsyncClient] = None
def _headers():
    if not OPENAI_API_KEY:
        return {"Content-Type": "application/json"}
    return {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

@asynccontextmanager
async def get_client():
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            headers=_headers(),
            timeout=httpx.Timeout(connect=5, read=60, write=10, pool=60),
            http2=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=10),
        )
    yield _client

# ---------- Cache ----------
def _cache_key(prefix: str, payload: dict) -> pathlib.Path:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha1(raw).hexdigest()
    return CACHE_DIR / f"{prefix}-{h}.json"
def _cache_get(p: pathlib.Path, ttl_sec: int) -> Optional[str]:
    try:
        if not p.exists(): return None
        if ttl_sec and (time.time() - p.stat().st_mtime) > ttl_sec: return None
        return p.read_text(encoding="utf-8")
    except Exception:
        return None
def _cache_set(p: pathlib.Path, content: str):
    try: p.write_text(content, encoding="utf-8")
    except Exception: pass

# ---------- JSON-safe ----------
def _find_json_block(s: str) -> Optional[str]:
    if not s: return None
    n=len(s); i=0
    while i<n:
        ch=s[i]
        if ch not in "{[}":
            i+=1; continue
        stack=[ch]; j=i+1; in_str=False; esc=False
        while j<n and stack:
            c=s[j]
            if in_str:
                if esc: esc=False
                elif c=="\\": esc=True
                elif c=='"': in_str=False
            else:
                if c=='"': in_str=True
                elif c in "{[": stack.append(c)
                elif c in "}]":
                    top=stack[-1]
                    if (top=="{" and c=="}") or (top=="[" and c=="]"): stack.pop()
            j+=1
        if not stack: return s[i:j]
        i+=1
    return None
def _safe_json_loads(s: str, default):
    if not s: return default
    try:
        return json.loads(s)
    except Exception:
        pass
    blk=_find_json_block(s)
    if blk:
        try: return json.loads(blk)
        except Exception: return default
    return default

# ---------- Chat ----------
async def call_llm(messages: List[Dict[str,str]], temperature: Optional[float]=None) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY가 필요합니다 (.env).")
    payload={"model":OPENAI_MODEL,"messages":messages}
    if temperature is not None and temperature!=1:
        payload["temperature"]=temperature
    ck=_cache_key("chat", payload)
    cached=_cache_get(ck, ttl_sec=180)
    if cached is not None: return cached
    async with get_client() as c:
        r=await c.post(CHAT_URL,json=payload)
    if r.status_code>=400:
        payload.pop("temperature", None)
        async with get_client() as c:
            r=await c.post(CHAT_URL,json=payload)
        if r.status_code>=400:
            try:
                data=r.json(); msg=data.get("error",{}).get("message") or data
            except Exception:
                msg=r.text
            raise httpx.HTTPStatusError(f"{r.status_code} {r.reason_phrase}: {msg}", request=r.request, response=r)
    out=r.json()["choices"][0]["message"]["content"]
    _cache_set(ck,out)
    return out

# ---------- Embedding (local only) ----------
_local_model=None
def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        extra={}
        if ALLOW_TRUST_REMOTE_CODE: extra["trust_remote_code"]=True
        _local_model=SentenceTransformer(EMBED_MODEL_ID, **extra)
    return _local_model

async def embed_texts(texts: List[str]) -> np.ndarray:
    if EMBED_BACKEND!="local":
        raise RuntimeError("임베딩은 로컬(EMBED_BACKEND=local)만 지원합니다.")
    model=_get_local_model()
    emb=model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    vecs=emb.astype("float32"); faiss.normalize_L2(vecs); return vecs

# ---------- LLM-derived ----------
async def parse_spec(user_text: str) -> Spec:
    out=await call_llm(
        [{"role":"system","content":PARSE_SYS},
         {"role":"user","content":user_text}]
    )
    return Spec(**_safe_json_loads(out, default={}))

_DEF_OPTS = {
    "location": ["서울","경기","인천","부산","대구","광주","대전","세종","울산","무관","모름"],
    "education": ["고졸","초대졸","대졸(4년)","석사","박사","무관","모름"],
    "employment_type": ["정규직","계약직","인턴","무관","모름"],
    "career.level": ["신입","경력","무관","모름"],
    "skills": ["Python","SQL","PyTorch","TensorFlow","Docker","AWS","모름"],
}
_DEF_ASK = {
    "location": "근무 희망 지역을 선택/입력해 주세요. (예: 서울)",
    "education": "최종 학력은 무엇인가요? (예: 대졸(4년))",
    "skills": "사용 가능한 기술 스택을 입력해 주세요. (예: Python, SQL, PyTorch)",
    "major": "전공은 무엇인가요? (예: 컴퓨터공학)",
    "certifications": "보유한 자격증이 있나요? (예: 정보처리기사, SQLD)",
    "career.level": "경력 수준을 선택해 주세요. (예: 신입/경력/무관)",
    "employment_type": "희망 고용형태를 선택해 주세요. (예: 정규직/계약직/인턴/무관)",
}

def _dedup_options(options: list[str]) -> list[str]:
    seen, out = set(), []
    for o in options or []:
        if not o: continue
        key = "무관" if o in {"모름","무관"} else o
        if key not in seen:
            seen.add(key); out.append(o)
    return out

def _make_turn(field: str) -> AskTurn:
    return AskTurn(
        field=field,
        ask=_DEF_ASK.get(field, "값을 입력해 주세요."),
        options=_dedup_options(_DEF_OPTS.get(field, ["무관","모름"]))
    )

async def ask_required_batch(current: Spec, missing: List[str]) -> List[AskTurn]:
    try:
        out=await call_llm(
            [{"role":"system","content":ASK_REQUIRED_BATCH_SYS},
             {"role":"user","content":json.dumps({"current": current.model_dump(), "missing": missing}, ensure_ascii=False)}]
        )
        data=_safe_json_loads(out, default=None)
        turns: List[AskTurn]=[]
        if data:
            arr=data if isinstance(data,list) else [data]
            for d in arr:
                turns.append(AskTurn(
                    field=d.get("field"),
                    ask=(d.get("ask") or "").splitlines()[0].strip() or _DEF_ASK.get(d.get("field") or "", "값을 입력해 주세요."),
                    options=_dedup_options(d.get("options") or _DEF_OPTS.get(d.get("field") or "", ["무관","모름"]))
                ))
        else:
            turns=[_make_turn(f) for f in missing]
    except Exception:
        turns=[_make_turn(f) for f in missing]

    fields=[(t.field or "").lower() for t in turns]
    if "skills" not in fields:
        turns.append(_make_turn("skills"))
    return turns

async def ask_optional_batch(current: Dict[str, Any], limit: int = 5, exclude: Optional[List[str]] = None) -> List[AskTurn]:
    payload={"current": current, "limit": limit, "exclude": exclude or []}
    out=await call_llm(
        [{"role":"system","content":ASK_OPTIONAL_BATCH_SYS},
         {"role":"user","content":json.dumps(payload, ensure_ascii=False)}]
    )
    data=_safe_json_loads(out, default=[])
    arr=data if isinstance(data,list) else [data]
    return [
        AskTurn(field=d.get("field"),
                ask=(d.get("ask") or "").splitlines()[0].strip(),
                options=_dedup_options(d.get("options") or []))
        for d in (arr[:limit] if arr else [])
    ]

async def map_filters(current: Spec) -> Dict[str, Any]:
    out=await call_llm(
        [{"role":"system","content":MAP_SYS},
         {"role":"user","content":json.dumps(current.model_dump(), ensure_ascii=False)}]
    )
    res=_safe_json_loads(out, default={})

    # 산업 콤마 보정
    ind=res.get("industry")
    if isinstance(ind,str) and "," in ind:
        res["industry"]=ind.replace(",","").replace(" ","")

    # duty 보정: 입력 role 또는 expanded_roles 기반으로 안전 폴백
    if not res.get("duty") and current.role:
        res["duty"]=current.role
    if not res.get("duty") and res.get("expanded_roles"):
        res["duty"]=res["expanded_roles"][0]

    res.setdefault("expanded_keywords", [])
    res.setdefault("expanded_roles", [])
    return res

# ---------- Query builder ----------
def build_query_text(spec: Spec, applied: Dict[str,Any]|None=None) -> str:
    """
    expanded_roles를 선두에, role/keywords/skills를 뒤에.
    불필요 패턴은 -토큰으로 배제.
    """
    role_terms: List[str] = []
    if applied:
        role_terms += [r for r in (applied.get("expanded_roles") or []) if r]
    if spec.role:
        role_terms.append(spec.role)
    for k in (spec.keywords or []):
        if k and len(k) <= 20:
            role_terms.append(k)
    role_terms = list(dict.fromkeys([t.strip() for t in role_terms if t]))[:5]

    skills = [s.strip() for s in (spec.skills or []) if s][:3]
    quoted_skills = [f'"{s}"' if (' ' in s or len(s) > 2) else s for s in skills]

    parts = []
    if role_terms:     parts.append(" ".join(role_terms))
    if quoted_skills:  parts.append(" ".join(quoted_skills))
    if spec.major:     parts.append(spec.major)
    if spec.location:  parts.append(spec.location)
    if spec.education and spec.education != "무관":
        parts.append(spec.education)

    q = " ".join(parts).strip()
    NEG_HINTS = ["콜센터","상담","판매","운전","배송","생산직","서빙","조리","주방","원무","고객센터","CS","교사","튜터"]
    minus = " ".join([f"-{t}" for t in NEG_HINTS])
    return (q + " " + minus).strip()

# ---------- Project → keywords ----------
def _uniq_keep(seq, limit=None):
    seen=set(); out=[]
    for x in seq or []:
        x=(x or "").strip()
        if not x or x in seen: continue
        seen.add(x); out.append(x)
        if limit and len(out)>=limit: break
    return out

async def extract_project_keywords(project_text: str) -> dict:
    if not project_text.strip():
        return {"roles":[], "skills":[], "domains":[]}

    if PROJECT_KEYWORD_SOURCE == "local":
        text = project_text.lower()
        skill_lex = [
            "python","java","c++","sql","pytorch","tensorflow","scikit-learn","pandas","numpy",
            "spark","hadoop","kafka","docker","kubernetes","aws","gcp","azure","django","flask",
            "fastapi","react","node","git","mlflow","airflow","redis","elasticsearch","rabbitmq",
            "postgres","mysql","streamlit","beautifulsoup"
        ]
        role_lex  = ["백엔드 개발자","프론트엔드 개발자","데이터 엔지니어","데이터 사이언티스트",
                     "ml 엔지니어","ai 엔지니어","딥러닝 엔지니어","머신러닝 엔지니어","소프트웨어 개발자"]
        domain_lex= ["자연어처리","nlp","컴퓨터비전","recommendation","추천","시계열","anomaly","보안","핀테크","커머스","광고","검색"]

        skills  = [w for w in skill_lex  if re.search(rf"\b{re.escape(w)}\b", text)]
        roles   = [w for w in role_lex   if w in text]
        domains = [w for w in domain_lex if w in text]

        return {
            "roles": _uniq_keep(roles, 5),
            "skills": _uniq_keep(skills, PROJECT_KEYWORD_TOPK),
            "domains": _uniq_keep(domains, 8),
        }

    out = await call_llm(
        [{"role":"system","content":PROJECT_KEYWORD_SYS},
         {"role":"user","content":project_text}],
        temperature=None
    )
    data = _safe_json_loads(out, default={"roles":[], "skills":[], "domains":[]})

    roles   = _uniq_keep([str(x).lower() for x in (data.get("roles") or [])], 5)
    skills  = _uniq_keep([str(x).lower() for x in (data.get("skills") or [])], PROJECT_KEYWORD_TOPK)
    domains = _uniq_keep([str(x).lower() for x in (data.get("domains") or [])], 8)
    return {"roles":roles, "skills":skills, "domains":domains}
