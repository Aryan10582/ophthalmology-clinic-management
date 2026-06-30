from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.supply import MedicalSupply, Notification, NotificationType
from app.schemas.supply import MedicalSupplyCreate, MedicalSupplyUpdate


class CRUDMedicalSupply(CRUDBase[MedicalSupply, MedicalSupplyCreate, MedicalSupplyUpdate]):
    def create(self, db: Session, *, obj_in: MedicalSupplyCreate) -> MedicalSupply:
        supply = super().create(db, obj_in=obj_in)
        create_low_stock_notification(db, supply=supply)
        return supply

    def update(self, db: Session, *, db_obj: MedicalSupply, obj_in: MedicalSupplyUpdate) -> MedicalSupply:
        supply = super().update(db, db_obj=db_obj, obj_in=obj_in)
        create_low_stock_notification(db, supply=supply)
        return supply


def create_low_stock_notification(db: Session, *, supply: MedicalSupply) -> None:
    if supply.current_stock >= supply.minimum_stock:
        return
    title = "Low Stock"
    message = f"{supply.name} remaining: {supply.current_stock} {supply.unit}. Minimum required: {supply.minimum_stock}."
    existing = (
        db.query(Notification)
        .filter(
            Notification.notification_type == NotificationType.LOW_STOCK,
            Notification.title == title,
            Notification.message == message,
            Notification.is_demo_data == supply.is_demo_data,
        )
        .first()
    )
    if existing:
        return
    db.add(Notification(notification_type=NotificationType.LOW_STOCK, title=title, message=message, is_demo_data=supply.is_demo_data))
    db.commit()


supply_crud = CRUDMedicalSupply(MedicalSupply)
