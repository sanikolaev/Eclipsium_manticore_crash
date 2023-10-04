from pydantic.main import BaseModel


class InsertDocumentSchema(BaseModel):
    # id: int
    index: str
    doc: dict


class BulkIReplaceDocumentSchema(BaseModel):
    replace: InsertDocumentSchema
