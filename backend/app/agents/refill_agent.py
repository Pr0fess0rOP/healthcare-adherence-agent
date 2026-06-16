def refill_agent(state: dict) -> dict:
    patient = state["patient"]

    last_refill = patient["last_refill_days_ago"]
    supply_days = patient["supply_days"]

    if last_refill > supply_days:
        refill = {
            "refill_status": "overdue",
            "days_overdue": last_refill - supply_days
        }
    elif last_refill >= supply_days - 5:
        refill = {
            "refill_status": "due_soon",
            "days_until_due": supply_days - last_refill
        }
    else:
        refill = {
            "refill_status": "not_due",
            "days_until_due": supply_days - last_refill
        }

    return {"refill": refill}