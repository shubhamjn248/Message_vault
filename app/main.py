from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import require_auth
from .database import Base, engine, get_db
from .models import Message
from .redaction import redact_message

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Message Vault",
    description="A small authenticated message API with server-side sensitive-data redaction.",
    version="1.0.0",
    lifespan=lifespan,
)

class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

class MessageOut(BaseModel):
    id: int
    message: str = Field(serialization_alias="message")
    created_at: str

    @classmethod
    def from_model(cls, item: Message):
        return cls(id=item.id, message=item.content, created_at=item.created_at.isoformat())

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

@app.post("/api/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(payload: MessageCreate, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    # The raw request is never written to the database; only this redacted value is persisted.
    safe_content = redact_message(payload.message)
    item = Message(content=safe_content)
    db.add(item)
    db.commit()
    db.refresh(item)
    return MessageOut.from_model(item)

@app.get("/api/messages", response_model=list[MessageOut])
def list_messages(db: Session = Depends(get_db), _: str = Depends(require_auth)):
    items = db.scalars(select(Message).order_by(Message.id.asc())).all()
    return [MessageOut.from_model(item) for item in items]

@app.get("/api/messages/{message_id}", response_model=MessageOut)
def get_message(message_id: int, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    item = db.get(Message, message_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageOut.from_model(item)

@app.delete("/api/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    item = db.get(Message, message_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    items = db.scalars(select(Message).order_by(Message.id.desc())).all()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context={"messages": items},
    )
