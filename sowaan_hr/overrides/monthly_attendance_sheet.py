import frappe


def apply():
	"""hrms's "Monthly Attendance Sheet" report groups each employee's days by `shift`. When
	attendance is marked without a shift (e.g. via the Employee Attendance Tool with no shift
	selected), the employee ends up with a second, mostly-blank row instead of one combined row.

	Frappe has no declarative hook for overriding a Script Report's python module, so this
	patches `get_attendance_map` at runtime (called once from sowaan_hr/__init__.py on app load)
	to fold blank-shift days into the employee's other shift before the report renders. The
	report keeps its original name; nothing in hrms is modified on disk.
	"""
	from hrms.hr.report.monthly_attendance_sheet import monthly_attendance_sheet as mas

	if getattr(mas.get_attendance_map, "_sowaan_patched", False):
		return

	original_get_attendance_map = mas.get_attendance_map

	def patched_get_attendance_map(filters=None):
		attendance_map = original_get_attendance_map(filters)
		_merge_unassigned_shift_records(attendance_map)
		return attendance_map

	patched_get_attendance_map._sowaan_patched = True
	mas.get_attendance_map = patched_get_attendance_map


def _merge_unassigned_shift_records(attendance_map: dict) -> None:
	for employee, shift_map in attendance_map.items():
		if "" not in shift_map or len(shift_map) == 1:
			continue

		unassigned_days = shift_map.pop("")
		primary_shift = max(shift_map, key=lambda shift: len(shift_map[shift]))
		shift_map[primary_shift].update(unassigned_days)
