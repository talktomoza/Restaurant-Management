from pydantic import BaseModel


class ColumnMapping(BaseModel):
    date_column: str
    item_column: str
    quantity_column: str
    amount_column: str
