from pydantic import BaseModel


class GmailMessage(BaseModel):
    message_id: str
    from_addr: str
    to: str
    date: str
    subject: str
    body_content: str
    thread_id: str | None = None


class GmailMessagesList(BaseModel):
    messages: list[dict]  
    next_page_token: str | None = None 