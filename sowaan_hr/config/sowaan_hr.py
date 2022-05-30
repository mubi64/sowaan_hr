from frappe import _

def get_data():
    return [
        {
            "label": _("Sowaan HR"),
            "icon": "octicon octicon-book",
            "items": [
                {
                    "type": "doctype",
                    "name": "Employee GPS Locations",
                    "label": _("Employee GPS Locations"),
                    "description": _("Employee GPS Locations")
                }
            ]
        }
    ]
