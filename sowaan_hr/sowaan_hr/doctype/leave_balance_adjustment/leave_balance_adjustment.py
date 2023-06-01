# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import (
    flt,
    formatdate,
    get_datetime,
    getdate,
    today
)
from frappe.model.document import Document

class LeaveBalanceAdjustment(Document):
	def on_submit(self):
		update_previous_leave_allocation(self.leave_allocation, self.balance_allocation)

def update_previous_leave_allocation(allocation, earned_leaves):
    allocation = frappe.get_doc("Leave Allocation", allocation)
    new_allocation = flt(
        allocation.total_leaves_allocated) + flt(earned_leaves)

    
    if new_allocation != allocation.total_leaves_allocated:
        today_date = today()

        allocation.db_set("total_leaves_allocated",
                          new_allocation, update_modified=False)
        create_additional_leave_ledger_entry(
            allocation, earned_leaves, today_date)

        text = _("allocated {0} leave(s) via leave balance adjustment on {1}").format(
			frappe.bold(earned_leaves), frappe.bold(formatdate(today_date))
		)

        allocation.add_comment(comment_type="Info", text=text)

def create_additional_leave_ledger_entry(allocation, leaves, date):
    """Create leave ledger entry for leave types"""
    allocation.new_leaves_allocated = leaves
    allocation.from_date = date
    allocation.unused_leaves = 0
    allocation.create_leave_ledger_entry()
