from __future__ import annotations
import base64, hashlib, hmac, json, os, re, secrets, time, uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
import certifi
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine, select, func, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from sqlalchemy.engine import make_url

class Settings(BaseSettings):
    database_url: str = "sqlite:///./jansetu_local.db"
    manus_api_url: str = ""
    manus_api_key: str = ""
    manus_jwt_secret: str = ""
    manus_project_id: str = ""
    manus_oauth_api_url: str = ""
    manus_oauth_client_id: str = Field(default="", validation_alias=AliasChoices("MANUS_PROJECT_ID", "MANUS_OAUTH_CLIENT_ID"))
    manus_oauth_authorize_url: str = Field(default="", validation_alias=AliasChoices("MANUS_OAUTH_PORTAL_URL", "MANUS_OAUTH_AUTHORIZE_URL"))
    public_app_origin: str = ""
    session_ttl_hours: int = 168
    class Config:
        env_prefix = ""
        populate_by_name = True
settings = Settings()

def normalize_database_url(raw_url: str):
    parsed = make_url(raw_url)
    if parsed.drivername == "mysql":
        parsed = parsed.set(drivername="mysql+pymysql")
    connect_args = {}
    if parsed.drivername == "mysql+pymysql":
        query = dict(parsed.query)
        ssl_value = query.pop("ssl", None)
        if ssl_value is not None:
            if isinstance(ssl_value, str):
                try:
                    ssl_options = json.loads(ssl_value)
                except json.JSONDecodeError:
                    lowered = ssl_value.lower()
                    if lowered in ("true", "1", "yes", "required"):
                        ssl_options = {"rejectUnauthorized": True}
                    elif lowered in ("false", "0", "no", "disabled"):
                        ssl_options = {"rejectUnauthorized": False}
                    else:
                        raise ValueError("Unsupported managed MySQL SSL option encoding")
            elif isinstance(ssl_value, dict):
                ssl_options = dict(ssl_value)
            else:
                raise ValueError("Unsupported managed MySQL SSL option type")
            if not isinstance(ssl_options, dict):
                raise ValueError("Managed MySQL SSL options must be an object")
            verify = ssl_options.pop("rejectUnauthorized", None)
            if verify is not None:
                ssl_options["verify_mode"] = "required" if verify else "none"
                ssl_options["check_hostname"] = bool(verify)
                if verify and not ssl_options.get("ca") and not ssl_options.get("capath"):
                    ssl_options["ca"] = certifi.where()
            connect_args["ssl"] = ssl_options
        parsed = parsed.set(query=query)
    if parsed.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return parsed, connect_args


database_url, database_connect_args = normalize_database_url(settings.database_url)
engine = create_engine(database_url, pool_pre_ping=True, future=True, connect_args=database_connect_args)
DB = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
class Base(DeclarativeBase): pass

def now(): return datetime.now(timezone.utc)
class Role(str, Enum): citizen="citizen"; staff="staff"; reviewer="reviewer"; admin="admin"
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    open_id: Mapped[str]=mapped_column(String(200),unique=True,index=True)
    display_name: Mapped[str]=mapped_column(String(200),default="")
    email: Mapped[Optional[str]]=mapped_column(String(320),nullable=True,index=True)
    role: Mapped[str]=mapped_column(String(20),default="citizen",index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class UserSession(Base):
    __tablename__="sessions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    token_hash: Mapped[str]=mapped_column(String(64),unique=True,index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Department(Base):
    __tablename__="departments"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); name: Mapped[str]=mapped_column(String(200),unique=True); description: Mapped[str]=mapped_column(Text,default="")
class Jurisdiction(Base):
    __tablename__="jurisdictions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); name: Mapped[str]=mapped_column(String(200),unique=True); level: Mapped[str]=mapped_column(String(40),default="state")
class Service(Base):
    __tablename__="services"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); slug: Mapped[str]=mapped_column(String(160),unique=True,index=True); name: Mapped[str]=mapped_column(String(240)); category: Mapped[str]=mapped_column(String(120),index=True); summary: Mapped[str]=mapped_column(Text,default=""); verification_status: Mapped[str]=mapped_column(String(40),default="partially_verified"); department_id: Mapped[Optional[int]]=mapped_column(ForeignKey("departments.id"),nullable=True); jurisdiction_id: Mapped[Optional[int]]=mapped_column(ForeignKey("jurisdictions.id"),nullable=True); source_checked_at: Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class ServiceSource(Base):
    __tablename__="service_sources"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); service_id: Mapped[int]=mapped_column(ForeignKey("services.id",ondelete="CASCADE"),index=True); title: Mapped[str]=mapped_column(String(240)); url: Mapped[str]=mapped_column(String(1000)); source_type: Mapped[str]=mapped_column(String(60),default="official"); checked_at: Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class KnowledgeDocument(Base):
    __tablename__="knowledge_documents"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); title: Mapped[str]=mapped_column(String(240)); topic: Mapped[str]=mapped_column(String(100),index=True); source_url: Mapped[str]=mapped_column(String(1000)); is_public: Mapped[bool]=mapped_column(Boolean,default=True,index=True); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class KnowledgeChunk(Base):
    __tablename__="knowledge_chunks"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); document_id: Mapped[int]=mapped_column(ForeignKey("knowledge_documents.id",ondelete="CASCADE"),index=True); topic: Mapped[str]=mapped_column(String(100),index=True); content: Mapped[str]=mapped_column(Text); is_public: Mapped[bool]=mapped_column(Boolean,default=True,index=True)
class Grievance(Base):
    __tablename__="grievances"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); reference: Mapped[str]=mapped_column(String(40),unique=True,index=True); citizen_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); service_id: Mapped[Optional[int]]=mapped_column(ForeignKey("services.id"),nullable=True); title: Mapped[str]=mapped_column(String(240)); narrative: Mapped[str]=mapped_column(Text); extractive_summary: Mapped[str]=mapped_column(Text,default=""); status: Mapped[str]=mapped_column(String(40),default="submitted",index=True); assigned_to_id: Mapped[Optional[int]]=mapped_column(ForeignKey("users.id"),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class AttachmentMetadata(Base):
    __tablename__="attachment_metadata"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id",ondelete="CASCADE"),index=True); owner_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); storage_key: Mapped[str]=mapped_column(String(500),unique=True); file_name: Mapped[str]=mapped_column(String(255)); content_type: Mapped[str]=mapped_column(String(120)); size_bytes: Mapped[int]=mapped_column(Integer); sha256: Mapped[str]=mapped_column(String(64)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Assignment(Base):
    __tablename__="assignments"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id",ondelete="CASCADE"),index=True); staff_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); assigned_by_id: Mapped[int]=mapped_column(ForeignKey("users.id")); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); active: Mapped[bool]=mapped_column(Boolean,default=True)
class StatusHistory(Base):
    __tablename__="status_history"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id",ondelete="CASCADE"),index=True); actor_id: Mapped[int]=mapped_column(ForeignKey("users.id")); old_status: Mapped[str]=mapped_column(String(40)); new_status: Mapped[str]=mapped_column(String(40)); public_update: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class InternalNote(Base):
    __tablename__="internal_notes"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id",ondelete="CASCADE"),index=True); author_id: Mapped[int]=mapped_column(ForeignKey("users.id")); content: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class ActionReport(Base):
    __tablename__="action_reports"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id",ondelete="CASCADE"),index=True); author_id: Mapped[int]=mapped_column(ForeignKey("users.id")); outcome: Mapped[str]=mapped_column(String(80)); details: Mapped[str]=mapped_column(Text); public_summary: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Appeal(Base):
    __tablename__="appeals"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id"),index=True); appellant_id: Mapped[int]=mapped_column(ForeignKey("users.id")); reason: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(30),default="pending",index=True); reviewer_id: Mapped[Optional[int]]=mapped_column(ForeignKey("users.id"),nullable=True); review_decision: Mapped[str]=mapped_column(String(40),default=""); review_note: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); reviewed_at: Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class Feedback(Base):
    __tablename__="feedback"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); grievance_id: Mapped[int]=mapped_column(ForeignKey("grievances.id"),index=True); citizen_id: Mapped[int]=mapped_column(ForeignKey("users.id")); rating: Mapped[int]=mapped_column(Integer); comment: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); __table_args__=(UniqueConstraint("grievance_id","citizen_id",name="uq_feedback_grievance_citizen"),)
class SLAPolicy(Base):
    __tablename__="sla_policies"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); category: Mapped[str]=mapped_column(String(120),unique=True); target_hours: Mapped[int]=mapped_column(Integer); active: Mapped[bool]=mapped_column(Boolean,default=True)
class Notification(Base):
    __tablename__="notifications"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True); grievance_id: Mapped[Optional[int]]=mapped_column(ForeignKey("grievances.id"),nullable=True); kind: Mapped[str]=mapped_column(String(60)); message: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); read_at: Mapped[Optional[datetime]]=mapped_column(DateTime(timezone=True),nullable=True)
class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); actor_id: Mapped[Optional[int]]=mapped_column(ForeignKey("users.id"),nullable=True); event: Mapped[str]=mapped_column(String(100),index=True); entity_type: Mapped[str]=mapped_column(String(80)); entity_id: Mapped[str]=mapped_column(String(80)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class AIEvaluationRun(Base):
    __tablename__="ai_evaluation_runs"
    id: Mapped[int]=mapped_column(Integer,primary_key=True); topic: Mapped[str]=mapped_column(String(100)); evidence_count: Mapped[int]=mapped_column(Integer); model_used: Mapped[bool]=mapped_column(Boolean,default=False); outcome: Mapped[str]=mapped_column(String(40)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

app=FastAPI(title="JanSetu Backend",version="1.0.0",description="JanSetu-only Telangana public-service information and grievance support.")
if settings.public_app_origin:
    app.add_middleware(CORSMiddleware,allow_origins=[settings.public_app_origin],allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["*"])
def get_db():
    db=DB()
    try: yield db
    finally: db.close()
def token_hash(token:str)->str: return hashlib.sha256(token.encode()).hexdigest()
def validate_jwt(token:str,db:Session):
    if not settings.manus_jwt_secret or not settings.manus_project_id: return None
    try:
        h,p,sigpart=token.split(".")
        header=json.loads(base64.urlsafe_b64decode(h+"="*(-len(h)%4)))
        if header.get("alg")!="HS256": return None
        raw=f"{h}.{p}".encode()
        sig=base64.urlsafe_b64decode(sigpart+"="*(-len(sigpart)%4))
        expected=hmac.new(settings.manus_jwt_secret.encode(),raw,hashlib.sha256).digest()
        if not hmac.compare_digest(sig,expected): return None
        payload=json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4)))
        if int(payload.get("exp",0))<=int(time.time()): return None
        project=payload.get("appId",payload.get("projectId",payload.get("project_id")))
        if str(project)!=settings.manus_project_id: return None
        oid=payload.get("openId",payload.get("open_id"))
        return db.scalar(select(User).where(User.open_id==str(oid))) if oid else None
    except Exception: return None
def current_user(request:Request,db:Session=Depends(get_db)):
    opaque=request.cookies.get("webdev_app_session")
    if opaque:
        sess=db.scalar(select(UserSession).where(UserSession.token_hash==token_hash(opaque)))
        if sess and sess.expires_at.replace(tzinfo=timezone.utc)>now():
            user=db.get(User,sess.user_id)
            if user: return user
        # Preview may supply a signed project JWT under the fixed application cookie name.
        if opaque.count(".")==2:
            user=validate_jwt(opaque,db)
            if user: return user
    auth=request.headers.get("authorization","")
    if auth.lower().startswith("bearer "):
        user=validate_jwt(auth[7:],db)
        if user: return user
    raise HTTPException(401,"Authentication required")
def require_roles(*roles):
    def dep(user:User=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403,"Insufficient role")
        return user
    return dep
def audit(db,actor,event,kind,eid):
    db.add(AuditLog(actor_id=actor.id if actor else None,event=event,entity_type=kind,entity_id=str(eid)))
def service_dicts(rows,db):
    if not rows: return []
    ids=[row.id for row in rows]
    jurisdiction_ids={row.jurisdiction_id for row in rows if row.jurisdiction_id}
    sources_by_service={}
    for source in db.scalars(select(ServiceSource).where(ServiceSource.service_id.in_(ids))).all():
        sources_by_service.setdefault(source.service_id,[]).append(source)
    jurisdictions={row.id:row for row in db.scalars(select(Jurisdiction).where(Jurisdiction.id.in_(jurisdiction_ids))).all()} if jurisdiction_ids else {}
    result=[]
    for service in rows:
        jurisdiction=jurisdictions.get(service.jurisdiction_id)
        result.append({"id":service.id,"slug":service.slug,"name":service.name,"category":service.category,"summary":service.summary,"verificationStatus":service.verification_status,"jurisdiction":jurisdiction.name if jurisdiction else "Not verified","sources":[{"id":hashlib.sha256(source.url.encode()).hexdigest()[:12],"title":source.title,"url":source.url,"type":source.source_type,"checkedAt":source.checked_at.isoformat() if source.checked_at else None} for source in sources_by_service.get(service.id,[])]})
    return result
def service_dict(service,db): return service_dicts([service],db)[0]
class GrievanceCreate(BaseModel):
    service_slug:Optional[str]=None; title:str=Field(min_length=4,max_length=240); narrative:str=Field(min_length=10,max_length=20000)
class StatusIn(BaseModel): status:str; public_update:str=Field(min_length=1,max_length=3000)
class NoteIn(BaseModel): content:str=Field(min_length=1,max_length=10000)
class ReportIn(BaseModel): outcome:str=Field(min_length=2,max_length=80); details:str=Field(min_length=1,max_length=10000); public_summary:str=Field(default="",max_length=3000)
class FeedbackIn(BaseModel): rating:int=Field(ge=1,le=5); comment:str=Field(default="",max_length=3000)
class AppealIn(BaseModel): reason:str=Field(min_length=10,max_length=10000)
class AppealReview(BaseModel): decision:str; note:str=Field(min_length=1,max_length=5000)
class AssistantIn(BaseModel): question:str=Field(min_length=2,max_length=4000); language:str=Field(default="en",max_length=30); topic:Optional[str]=None
TOPIC_TERMS={
    "water":("water","tap","drinking","supply","pipeline","leak"),
    "electricity":("electricity","power","outage","transformer","current"),
    "sanitation":("garbage","waste","drain","sewer","sanitation"),
    "roads":("road","pothole","street","footpath"),
    "health":("hospital","clinic","health","medicine","ehs","nehs","tims"),
    "housing":("housing","house","property","building","2bhk","flat"),
    "revenue":("land","revenue","pattadar","mutation","survey","nala","valuation"),
    "identity":("birth","death","caste","certificate","meeseva","income"),
    "social":("pension","aasara","ration","food security","kalyana","shaadi","welfare"),
    "education":("school","student","ssc","exam","education","scholarship","epass"),
    "agriculture":("seed","farmer","crop","agriculture","rythu","extension")
}
def route_topic(question,explicit):
    if explicit and explicit.lower() in TOPIC_TERMS:return explicit.lower()
    q=question.lower(); scores={k:sum(1 for t in terms if t in q) for k,terms in TOPIC_TERMS.items()}; best=max(scores,key=scores.get)
    return best if scores[best] else "general"
def local_extractive_summary(text):
    # Deterministic local sentence selection: no external model and no narrative transmission.
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",text.strip()) if s.strip()]
    if len(sentences)<=2:return " ".join(sentences)[:600]
    scored=[]
    for i,s in enumerate(sentences):
        words=set(re.findall(r"[\w']+",s.lower())); scored.append((len(words),-i,s))
    return " ".join(x[2] for x in sorted(sorted(scored,reverse=True)[:2],key=lambda x:-x[1]))[:600]
@app.get("/api/v1/health")
def health(): return {"status":"ok","service":"jansetu-backend"}
@app.get("/api/v1/services")
def services(q:Optional[str]=None,category:Optional[str]=None,db:Session=Depends(get_db)):
    stmt=select(Service)
    if category: stmt=stmt.where(func.lower(Service.category)==category.lower())
    if q: stmt=stmt.where((Service.name.ilike(f"%{q}%"))|(Service.summary.ilike(f"%{q}%"))|(Service.category.ilike(f"%{q}%")))
    rows=db.scalars(stmt.order_by(Service.name)).all()
    return {"items":service_dicts(rows,db)}
@app.get("/api/v1/services/{slug}")
def service_detail(slug:str,db:Session=Depends(get_db)):
    s=db.scalar(select(Service).where(Service.slug==slug))
    if not s: raise HTTPException(404,"Service not found")
    return service_dict(s,db)
class AssistantReply(BaseModel):
    answer:str=Field(min_length=1,max_length=5000)
    source_ids:list[str]=Field(default_factory=list,max_length=12)
    uncertainty:str=Field(default="",max_length=1200)

@app.post("/api/v1/assistant")
async def assistant(body:AssistantIn,db:Session=Depends(get_db)):
    # The raw question stays in this process for local routing/scoring; it is never placed in the model payload.
    topic=route_topic(body.question,body.topic)
    terms=set(re.findall(r"[a-z0-9]{3,}",body.question.lower()))
    chunks=db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.is_public==True,KnowledgeChunk.topic==topic).limit(30)).all()
    documents={d.id:d for d in db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.id.in_({c.document_id for c in chunks}),KnowledgeDocument.is_public==True)).all()} if chunks else {}
    scored=[]
    for c in chunks:
        d=documents.get(c.document_id)
        if not d or not d.is_public: continue
        overlap=len(terms & set(re.findall(r"[a-z0-9]{3,}",c.content.lower())))
        if overlap>0:
            source_id=hashlib.sha256(d.source_url.encode()).hexdigest()[:12]
            scored.append((overlap,c,d,source_id))
    # Evidence gate: require a topic-routed public record and at least one meaningful keyword overlap.
    top=sorted(scored,key=lambda x:(-x[0],x[2].title))[:4]
    evidence=[{"id":sid,"title":doc.title,"text":chunk.content,"url":doc.source_url} for _,chunk,doc,sid in top if len(chunk.content.strip())>=20]
    answer="I could not find sufficiently relevant verified public information for this topic in the JanSetu directory. Please consult an official Telangana department source."
    uncertainty="No sufficiently relevant public source matched this topic."
    accepted_ids=[]; model_used=False
    language="te" if body.language.lower().startswith("te") else "en"
    if evidence:
        answer="I found public source material related to this topic. Review the cited page for current details; unsupported eligibility, fees, documents and timelines are not verified."
        uncertainty="The source records are partial and may not describe current requirements or local applicability."
        if settings.manus_api_url and settings.manus_api_key:
            payload={"normalized_topic":topic,"response_language":language,"public_evidence":[{"id":e["id"],"title":e["title"],"text":e["text"],"url":e["url"]} for e in evidence]}
            prompt=("Return one JSON object with answer (string), source_ids (array of IDs from the evidence only), and uncertainty (string). "
                    "Answer in the requested language, use only the public evidence, state what is not verified, and never invent eligibility, fees, documents, deadlines or guarantees. "
                    "Do not add facts not supported by the evidence.\n"+json.dumps(payload,ensure_ascii=False))
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    r=await client.post(settings.manus_api_url.rstrip("/")+"/v1/chat/completions",headers={"Authorization":"Bearer "+settings.manus_api_key},json={"messages":[{"role":"user","content":prompt}],"temperature":0.1})
                    r.raise_for_status(); data=r.json()
                    if data.get("error"): raise ValueError("Managed model returned an error")
                    content=data.get("choices",[{}])[0].get("message",{}).get("content")
                    if not isinstance(content,str) or not content.strip(): raise ValueError("Managed model returned no content")
                    cleaned=content.strip().removeprefix("```json").removesuffix("```").strip().removeprefix("```").removesuffix("```").strip()
                    reply=AssistantReply.model_validate(json.loads(cleaned))
                    allowed={e["id"] for e in evidence}
                    accepted_ids=[sid for sid in reply.source_ids if sid in allowed]
                    if not accepted_ids: raise ValueError("Assistant cited no valid public source")
                    answer=reply.answer; uncertainty=reply.uncertainty or uncertainty; model_used=True
            except Exception:
                # Keep the cited, conservative local fallback. Never resend the original question.
                pass
    selected=[e for e in evidence if not accepted_ids or e["id"] in accepted_ids]
    db.add(AIEvaluationRun(topic=topic,evidence_count=len(selected),model_used=model_used,outcome="answered" if selected else "no_evidence")); db.commit()
    return {"answer":answer,"topic":topic,"evidence":selected,"sources":selected,"sourceIds":[e["id"] for e in selected],"uncertainty":uncertainty,"disclaimer":"JanSetu is an independent civic information and grievance-support service, not a government authority. Verify current requirements with the linked official source."}
@app.get("/api/v1/auth/me")
def auth_me(user:User=Depends(current_user)): return {"authenticated":True,"id":user.id,"displayName":user.display_name,"email":user.email,"role":user.role}
def cookie_secure(origin): return urlparse(origin).scheme=="https"
def _oauth_state(redirect_uri,nonce):
    raw=json.dumps({"redirectUri":redirect_uri,"nonce":nonce},separators=(",",":" )).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")
def _decode_oauth_state(value):
    payload=json.loads(base64.urlsafe_b64decode(value+"="*(-len(value)%4)))
    redirect_uri=payload.get("redirectUri"); nonce=payload.get("nonce")
    parsed=urlparse(redirect_uri or "")
    if not nonce or parsed.path!="/api/v1/auth/callback" or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Invalid OAuth state")
    if parsed.scheme!="https" and not (parsed.scheme=="http" and parsed.hostname in ("localhost","127.0.0.1")):
        raise ValueError("Invalid callback scheme")
    origin=f"{parsed.scheme}://{parsed.netloc}"
    if settings.public_app_origin and origin.rstrip("/")!=settings.public_app_origin.rstrip("/"):
        raise ValueError("OAuth callback origin is not configured")
    return redirect_uri,nonce,origin
@app.get("/api/v1/auth/login")
def auth_login(origin:str,request:Request):
    parsed=urlparse(origin)
    if not parsed.scheme or not parsed.netloc or parsed.path not in ("","/") or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise HTTPException(400,"Invalid browser application origin")
    if parsed.scheme!="https" and not (parsed.scheme=="http" and parsed.hostname in ("localhost","127.0.0.1")):
        raise HTTPException(400,"Login requires the HTTPS application origin")
    if settings.public_app_origin and origin.rstrip("/")!=settings.public_app_origin.rstrip("/"):
        raise HTTPException(400,"Unapproved application origin")
    request_origin=request.headers.get("origin")
    if request_origin and request_origin.rstrip("/")!=origin.rstrip("/"):
        raise HTTPException(400,"Browser origin does not match the application origin")
    if not settings.manus_oauth_authorize_url or not settings.manus_oauth_client_id:
        raise HTTPException(503,"Manus OAuth is not configured")
    redirect_uri=origin.rstrip("/")+"/api/v1/auth/callback"; nonce=secrets.token_urlsafe(32); state=_oauth_state(redirect_uri,nonce)
    portal=settings.manus_oauth_authorize_url.rstrip("/")
    if not portal.endswith("/app-auth"): portal+="/app-auth"
    authorization=portal+"?"+urlencode({"appId":settings.manus_oauth_client_id,"redirectUri":redirect_uri,"state":state,"responseType":"code"})
    res=RedirectResponse(authorization,status_code=302)
    secure=cookie_secure(origin)
    res.set_cookie("jansetu_oauth_nonce",nonce,httponly=True,secure=secure,samesite="none" if secure else "lax",max_age=600,path="/")
    return res
@app.get("/api/v1/auth/callback")
async def auth_callback(request:Request,code:str,state:str,db:Session=Depends(get_db)):
    nonce=request.cookies.get("jansetu_oauth_nonce")
    try: redirect,expected_nonce,origin=_decode_oauth_state(state)
    except Exception: raise HTTPException(400,"Invalid or expired OAuth state")
    if not nonce or not hmac.compare_digest(nonce,expected_nonce): raise HTTPException(400,"OAuth state/nonce did not match this browser")
    if not settings.manus_oauth_api_url or not settings.manus_oauth_client_id: raise HTTPException(503,"Manus OAuth is not configured")
    base=settings.manus_oauth_api_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            tokenr=await client.post(base+"/webdev.v1.WebDevAuthPublicService/ExchangeToken",json={"clientId":settings.manus_oauth_client_id,"grantType":"authorization_code","code":code,"redirectUri":redirect}); tokenr.raise_for_status(); token=tokenr.json().get("accessToken")
            if not token: raise ValueError("OAuth exchange returned no access token")
            ur=await client.post(base+"/webdev.v1.WebDevAuthPublicService/GetUserInfo",json={"accessToken":token}); ur.raise_for_status(); info=ur.json()
    except Exception: raise HTTPException(502,"Manus identity verification failed; no JanSetu account was created")
    oid=info.get("openId") or info.get("open_id")
    if not oid: raise HTTPException(401,"Verified identity did not include an openId")
    user=db.scalar(select(User).where(User.open_id==str(oid)))
    if not user:
        user=User(open_id=str(oid),display_name=info.get("name") or info.get("displayName") or "",email=info.get("email"),role="citizen"); db.add(user); db.flush()
    opaque=secrets.token_urlsafe(48); db.add(UserSession(token_hash=token_hash(opaque),user_id=user.id,expires_at=now()+timedelta(hours=settings.session_ttl_hours))); audit(db,user,"login","user",user.id); db.commit()
    res=RedirectResponse(origin.rstrip("/")+"/dashboard",status_code=303)
    secure=cookie_secure(origin)
    res.set_cookie("webdev_app_session",opaque,httponly=True,secure=secure,samesite="none" if secure else "lax",max_age=settings.session_ttl_hours*3600,path="/")
    res.delete_cookie("jansetu_oauth_nonce",path="/",httponly=True,secure=secure,samesite="none" if secure else "lax")
    return res
@app.post("/api/v1/auth/logout")
def auth_logout(request:Request,response:Response,db:Session=Depends(get_db)):
    opaque=request.cookies.get("webdev_app_session")
    if opaque:
        sess=db.scalar(select(UserSession).where(UserSession.token_hash==token_hash(opaque)))
        if sess: db.delete(sess); db.commit()
    origin=request.headers.get("origin") or settings.public_app_origin or ""
    secure=cookie_secure(origin)
    response.delete_cookie("webdev_app_session",path="/",httponly=True,secure=secure,samesite="none" if secure else "lax")
    return {"ok":True}
def owned_grievance(reference,user,db):
    g=db.scalar(select(Grievance).where(Grievance.reference==reference))
    if not g: raise HTTPException(404,"Grievance not found")
    if g.citizen_id!=user.id and user.role not in ("staff","reviewer","admin"): raise HTTPException(404,"Grievance not found")
    return g
def grievance_out(g,db,private=False):
    hist=db.scalars(select(StatusHistory).where(StatusHistory.grievance_id==g.id).order_by(StatusHistory.created_at)).all()
    attachments=db.scalars(select(AttachmentMetadata).where(AttachmentMetadata.grievance_id==g.id)).all()
    actions=db.scalars(select(ActionReport).where(ActionReport.grievance_id==g.id).order_by(ActionReport.created_at)).all()
    history=[]
    for event in hist:
        actor=db.get(User,event.actor_id)
        history.append({"status":event.new_status,"publicUpdate":event.public_update,"actor":"JanSetu staff" if actor and actor.role in ("staff","admin") else "Citizen","createdAt":event.created_at.isoformat()})
    result={"reference":g.reference,"title":g.title,"summary":g.extractive_summary,"status":g.status,"createdAt":g.created_at.isoformat(),"updatedAt":g.updated_at.isoformat(),"statusHistory":history,"actionReports":[{"outcome":a.outcome,"publicSummary":a.public_summary,"createdAt":a.created_at.isoformat()} for a in actions if a.public_summary.strip()],"attachments":[{"id":a.id,"fileName":a.file_name,"contentType":a.content_type,"sizeBytes":a.size_bytes,"downloadUrl":f"/api/v1/grievances/{g.reference}/attachments/{a.id}/download"} for a in attachments]}
    if private:
        result["narrative"]=g.narrative
        result["internalNotes"]=[{"content":n.content,"createdAt":n.created_at.isoformat()} for n in db.scalars(select(InternalNote).where(InternalNote.grievance_id==g.id)).all()]
        result["actionReports"]=[{"outcome":a.outcome,"details":a.details,"publicSummary":a.public_summary,"createdAt":a.created_at.isoformat()} for a in actions]
    return result
@app.post("/api/v1/grievances",status_code=201)
def create_grievance(body:GrievanceCreate,user:User=Depends(require_roles("citizen")),db:Session=Depends(get_db)):
    svc=db.scalar(select(Service).where(Service.slug==body.service_slug)) if body.service_slug else None
    if body.service_slug and not svc: raise HTTPException(422,"Unknown service_slug")
    reference="JS-"+now().strftime("%y%m%d")+"-"+secrets.token_hex(4).upper()
    g=Grievance(reference=reference,citizen_id=user.id,service_id=svc.id if svc else None,title=body.title.strip(),narrative=body.narrative.strip(),extractive_summary=local_extractive_summary(body.narrative));db.add(g);db.flush();db.add(StatusHistory(grievance_id=g.id,actor_id=user.id,old_status="",new_status="submitted",public_update="Grievance submitted to JanSetu."));audit(db,user,"grievance_created","grievance",reference);db.commit();return grievance_out(g,db)
@app.get("/api/v1/grievances/mine")
def my_grievances(user:User=Depends(require_roles("citizen")),db:Session=Depends(get_db)):
    return {"items":[grievance_out(g,db) for g in db.scalars(select(Grievance).where(Grievance.citizen_id==user.id).order_by(Grievance.created_at.desc())).all()]}
@app.get("/api/v1/grievances/{reference}")
def grievance_detail(reference:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    g=owned_grievance(reference,user,db);return grievance_out(g,db,private=user.role in ("staff","reviewer","admin"))
@app.get("/api/v1/staff/grievances")
def staff_grievances(status:Optional[str]=None,user:User=Depends(require_roles("staff","reviewer","admin")),db:Session=Depends(get_db)):
    stmt=select(Grievance)
    if status:stmt=stmt.where(Grievance.status==status)
    return {"items":[grievance_out(g,db,True) for g in db.scalars(stmt.order_by(Grievance.created_at)).all()]}
ALLOWED_TRANSITIONS={"submitted":{"acknowledged","in_review","rejected"},"acknowledged":{"in_review","resolved","rejected"},"in_review":{"awaiting_information","resolved","rejected"},"awaiting_information":{"in_review","resolved"},"resolved":{"closed","in_review"},"rejected":{"in_review","closed"},"closed":set()}
@app.post("/api/v1/staff/grievances/{reference}/status")
def set_status(reference:str,body:StatusIn,user:User=Depends(require_roles("staff","admin")),db:Session=Depends(get_db)):
    g=db.scalar(select(Grievance).where(Grievance.reference==reference))
    if not g:raise HTTPException(404,"Grievance not found")
    if body.status not in ALLOWED_TRANSITIONS or body.status not in ALLOWED_TRANSITIONS.get(g.status,set()):raise HTTPException(409,f"Invalid transition from {g.status} to {body.status}")
    old=g.status;g.status=body.status;g.updated_at=now();db.add(StatusHistory(grievance_id=g.id,actor_id=user.id,old_status=old,new_status=body.status,public_update=body.public_update));db.add(Notification(user_id=g.citizen_id,grievance_id=g.id,kind="status",message="JanSetu grievance status updated."));audit(db,user,"status_changed","grievance",reference);db.commit();return grievance_out(g,db)
@app.post("/api/v1/staff/grievances/{reference}/notes",status_code=201)
def add_note(reference:str,body:NoteIn,user:User=Depends(require_roles("staff","admin")),db:Session=Depends(get_db)):
    g=db.scalar(select(Grievance).where(Grievance.reference==reference))
    if not g:raise HTTPException(404,"Grievance not found")
    n=InternalNote(grievance_id=g.id,author_id=user.id,content=body.content);db.add(n);audit(db,user,"internal_note_added","grievance",reference);db.commit();return {"id":n.id,"createdAt":n.created_at.isoformat()}
@app.post("/api/v1/staff/grievances/{reference}/action-reports",status_code=201)
def add_report(reference:str,body:ReportIn,user:User=Depends(require_roles("staff","admin")),db:Session=Depends(get_db)):
    g=db.scalar(select(Grievance).where(Grievance.reference==reference))
    if not g:raise HTTPException(404,"Grievance not found")
    a=ActionReport(grievance_id=g.id,author_id=user.id,outcome=body.outcome,details=body.details,public_summary=body.public_summary);db.add(a);audit(db,user,"action_report_added","grievance",reference);db.commit();return {"id":a.id,"outcome":a.outcome,"publicSummary":a.public_summary,"createdAt":a.created_at.isoformat()}
@app.post("/api/v1/grievances/{reference}/feedback",status_code=201)
def feedback(reference:str,body:FeedbackIn,user:User=Depends(require_roles("citizen")),db:Session=Depends(get_db)):
    g=owned_grievance(reference,user,db)
    if db.scalar(select(Feedback).where(Feedback.grievance_id==g.id,Feedback.citizen_id==user.id)):raise HTTPException(409,"Feedback already submitted")
    f=Feedback(grievance_id=g.id,citizen_id=user.id,rating=body.rating,comment=body.comment);db.add(f);db.commit();return {"ok":True,"id":f.id}
@app.post("/api/v1/grievances/{reference}/appeals",status_code=201)
def appeal(reference:str,body:AppealIn,user:User=Depends(require_roles("citizen")),db:Session=Depends(get_db)):
    g=owned_grievance(reference,user,db)
    if g.status not in ("resolved","rejected","closed"):raise HTTPException(409,"Appeal is available after a decision")
    if db.scalar(select(Appeal).where(Appeal.grievance_id==g.id,Appeal.status=="pending")):raise HTTPException(409,"A pending appeal already exists")
    a=Appeal(grievance_id=g.id,appellant_id=user.id,reason=body.reason);db.add(a);db.commit();return {"id":a.id,"status":a.status,"createdAt":a.created_at.isoformat()}
@app.get("/api/v1/staff/appeals")
def staff_appeals(user:User=Depends(require_roles("reviewer","admin")),db:Session=Depends(get_db)):
    # Appeal reviewers are distinct from ordinary case staff; review process enforced below.
    return {"items":[{"id":a.id,"reference":db.get(Grievance,a.grievance_id).reference,"reason":a.reason,"status":a.status,"createdAt":a.created_at.isoformat()} for a in db.scalars(select(Appeal).where(Appeal.status=="pending")).all()]}
@app.post("/api/v1/staff/appeals/{appeal_id}/review")
def review_appeal(appeal_id:int,body:AppealReview,user:User=Depends(require_roles("reviewer","admin")),db:Session=Depends(get_db)):
    a=db.get(Appeal,appeal_id)
    if not a:raise HTTPException(404,"Appeal not found")
    g=db.get(Grievance,a.grievance_id)
    if a.appellant_id==user.id or g.assigned_to_id==user.id:raise HTTPException(403,"Reviewer must be independent of appellant and case assignment")
    if a.status!="pending":raise HTTPException(409,"Appeal already reviewed")
    decision=body.decision.lower()
    if decision not in ("upheld","varied","dismissed"):raise HTTPException(422,"decision must be upheld, varied, or dismissed")
    a.status="reviewed";a.review_decision=decision;a.review_note=body.note;a.reviewer_id=user.id;a.reviewed_at=now();audit(db,user,"appeal_reviewed","appeal",a.id);db.commit();return {"id":a.id,"status":a.status,"decision":decision}
@app.get("/api/v1/staff/analytics")
def analytics(user:User=Depends(require_roles("staff","reviewer","admin")),db:Session=Depends(get_db)):
    statuses={k:v for k,v in db.execute(select(Grievance.status,func.count()).group_by(Grievance.status)).all()}
    return {"label":"JanSetu operational counts only; not government statistics. No synthetic case records are included.","synthetic":False,"governmentStatistics":False,"countsByStatus":statuses,"total":sum(statuses.values())}

def load_catalog(path:Path|None=None,db:Session|None=None):
    path=path or Path(__file__).parent/"data"/"service_catalog.json"; own=db is None; db=db or DB()
    if not path.exists():
        if own:db.close()
        return {"inserted":0,"reason":"catalog file absent; no service claims fabricated"}
    data=json.loads(path.read_text()); inserted=0
    topic_by_category={"Identity & certificates":"identity","Land & revenue":"revenue","Social protection":"social","Health":"health","Education":"education","Housing":"housing","Agriculture":"agriculture"}
    for row in data.get("services",[]):
        if not all(row.get(k) for k in ("slug","name","category")):continue
        checked=None
        try: checked=datetime.fromisoformat(row.get("sourceDate","")+"T00:00:00+00:00") if row.get("sourceDate") else None
        except ValueError: checked=None
        jurisdiction_name=row.get("jurisdiction") or "Not verified"
        jurisdiction=db.scalar(select(Jurisdiction).where(Jurisdiction.name==jurisdiction_name))
        if not jurisdiction:
            jurisdiction=Jurisdiction(name=jurisdiction_name,level="source_scope");db.add(jurisdiction);db.flush()
        s=db.scalar(select(Service).where(Service.slug==row["slug"]))
        if not s:
            s=Service(slug=row["slug"],name=row["name"],category=row["category"],summary=row.get("summary", ""),verification_status=row.get("verificationStatus","partially_verified"),jurisdiction_id=jurisdiction.id,source_checked_at=checked);db.add(s);db.flush();inserted+=1
        else:
            # Keep any established user edits; only fill metadata that was previously absent.
            if not s.jurisdiction_id:s.jurisdiction_id=jurisdiction.id
            if not s.source_checked_at:s.source_checked_at=checked
        topic=topic_by_category.get(row["category"],"general")
        for source in row.get("sources",[]):
            if not source.get("url"):continue
            db_source=db.scalar(select(ServiceSource).where(ServiceSource.service_id==s.id,ServiceSource.url==source["url"]))
            if not db_source:
                db_source=ServiceSource(service_id=s.id,title=source.get("title",s.name),url=source["url"],source_type=source.get("type","official"),checked_at=checked);db.add(db_source)
            doc=db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.source_url==source["url"],KnowledgeDocument.topic==topic))
            if not doc:
                doc=KnowledgeDocument(title=source.get("title",s.name),topic=topic,source_url=source["url"],is_public=True,updated_at=now());db.add(doc);db.flush()
            evidence=(row.get("sourceSupport","")+" "+row.get("summary","")).strip()
            if evidence and not db.scalar(select(KnowledgeChunk).where(KnowledgeChunk.document_id==doc.id,KnowledgeChunk.content==evidence)):
                db.add(KnowledgeChunk(document_id=doc.id,topic=topic,content=evidence,is_public=True))
    db.commit()
    if own:db.close()
    return {"inserted":inserted,"catalog_records":len(data.get("services",[]))}
def provision_staff(open_id:str,role:str,display_name:str=""):
    if role not in ("staff","reviewer","admin"):raise ValueError("role must be staff, reviewer, or admin")
    db=DB()
    try:
        u=db.scalar(select(User).where(User.open_id==open_id))
        if not u:raise ValueError("User must first sign in through Manus OAuth")
        u.role=role
        if display_name:u.display_name=display_name
        db.commit()
    finally:db.close()
from app.civic_routes import router as civic_router
app.include_router(civic_router)

if __name__=="__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="0.0.0.0",port=int(os.getenv("PORT","8000")))
