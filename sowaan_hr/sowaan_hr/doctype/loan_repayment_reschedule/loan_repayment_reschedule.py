# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime


class LoanRepaymentReschedule(Document):

	


	def before_save(self) :

		next_row = []

		leave_rp_sch_list = frappe.db.get_list("Loan Repayment Schedule",
								filters = {
									'loan' : self.loan ,
									'docstatus' : 1 ,
									'status' : 'Active' ,
								}
							)

		if leave_rp_sch_list :

			if len(leave_rp_sch_list) > 1 :
				frappe.throw("More than one Active Repayment Schedule found.")

			else :
				leave_rp_sch_doc = frappe.get_doc("Loan Repayment Schedule", leave_rp_sch_list[0].name)
				self.loan_repayment_schedule = leave_rp_sch_list[0].name
				
				values = {
							'loan_rep_sch': leave_rp_sch_list[0].name,
						}

				check_accrued_date = frappe.db.sql("""
												SELECT payment_date
												FROM `tabRepayment Schedule`
												WHERE parent = %(loan_rep_sch)s AND is_accrued = 1
												ORDER BY payment_date DESC
												LIMIT 1"""
												, values=values , as_dict=1)

				if check_accrued_date :								

					if str(check_accrued_date[0].payment_date) >= str(self.payment_date) :
						frappe.throw("Advance Payment can not be before last Accrued Date.")					

				
				repayment_schedule_table = frappe.db.sql("""
												SELECT *
												FROM `tabRepayment Schedule`
												WHERE parent = %(loan_rep_sch)s
												ORDER BY payment_date ASC"""
												, values=values , as_dict=1)

				
				
				self.repayment_schedule = []
				sig = 0
				same_date_case = 0
				last_balance = leave_rp_sch_doc.loan_amount

				for row in repayment_schedule_table :

					if same_date_case == 1 :
						cur_balance = last_balance - row.principal_amount
						self.append('repayment_schedule',{
							'payment_date' : row.payment_date ,
							'number_of_days' : row.number_of_days ,
							'principal_amount' : row.principal_amount ,
							'interest_amount' : row.interest_amount ,
							'total_payment' : row.total_payment ,
							'balance_loan_amount' : cur_balance ,
							'is_accrued' : row.is_accrued ,
						})
						last_balance = cur_balance
				
					elif str(row.payment_date) == str(self.payment_date) :
						cur_balance = last_balance - self.payment_amount
						self.append('repayment_schedule',{
							'payment_date' : row.payment_date ,
							'number_of_days' : row.number_of_days ,
							'principal_amount' : self.payment_amount ,
							'interest_amount' : row.interest_amount ,
							'total_payment' : self.payment_amount ,
							'balance_loan_amount' : cur_balance ,
							'is_accrued' : row.is_accrued ,
						})
						last_balance = cur_balance
						same_date_case = 1
						sig = 1
						

					
					elif str(row.payment_date) < str(self.payment_date) :
						self.append('repayment_schedule',{
							'payment_date' : row.payment_date ,
							'number_of_days' : row.number_of_days ,
							'principal_amount' : row.principal_amount ,
							'interest_amount' : row.interest_amount ,
							'total_payment' : row.total_payment ,
							'balance_loan_amount' : row.balance_loan_amount ,
							'is_accrued' : row.is_accrued ,
						})
						last_balance = row.balance_loan_amount
						
					
					else :

						if sig == 1 :
							
							if last_balance > 0 :
								if last_balance <= next_row['total_payment'] :
									self.append('repayment_schedule',{
										'payment_date' : next_row['payment_date'] ,
										'number_of_days' : next_row['number_of_days'] ,
										'principal_amount' : last_balance ,
										'interest_amount' : next_row['interest_amount'] ,
										'total_payment' : last_balance ,
										'balance_loan_amount' : 0 ,
										'is_accrued' : next_row['is_accrued'] ,
									})
									break
								else :
									
									cur_balance = last_balance - next_row['total_payment']
									self.append('repayment_schedule',{
										'payment_date' : next_row['payment_date'] ,
										'number_of_days' : next_row['number_of_days'] ,
										'principal_amount' : next_row['principal_amount'] ,
										'interest_amount' : next_row['interest_amount'] ,
										'total_payment' : next_row['total_payment'] ,
										'balance_loan_amount' : cur_balance ,
										'is_accrued' : next_row['is_accrued'] ,
									})
									next_row = {
										'payment_date' : row.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : row.principal_amount ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : row.total_payment ,
										'is_accrued' : row.is_accrued ,
									}
									last_balance = cur_balance

							else :
								break


						if sig == 0 :
							if self.payment_amount <= last_balance :
								cur_balance = last_balance - self.payment_amount
								self.append('repayment_schedule',{
									'payment_date' : self.payment_date ,
									'number_of_days' : 1 ,
									'principal_amount' : self.payment_amount ,
									'interest_amount' : 0 ,
									'total_payment' : self.payment_amount ,
									'balance_loan_amount' : cur_balance ,
									'is_accrued' : 0 ,
								})
								sig = 1
								last_balance = cur_balance
								
								next_row = {
									'payment_date' : row.payment_date ,
									'number_of_days' : row.number_of_days ,
									'principal_amount' : row.principal_amount ,
									'interest_amount' : row.interest_amount ,
									'total_payment' : row.total_payment ,
									'is_accrued' : row.is_accrued ,
								}
								

							else :
								frappe.throw("Payment amount cannot be greater than Loan Balance.")


				
				final_amount = self.repayment_schedule[-1].principal_amount + self.repayment_schedule[-1].balance_loan_amount
				self.repayment_schedule[-1].principal_amount = final_amount
				self.repayment_schedule[-1].total_payment = final_amount
				self.repayment_schedule[-1].balance_loan_amount = 0
						

		else :
			frappe.throw("No Active Repayment Schedule found.")



	def before_submit(self) :

		loan_rep_sch_doc = frappe.get_doc('Loan Repayment Schedule', self.loan_repayment_schedule)

		if len(loan_rep_sch_doc.repayment_schedule) >= len(self.repayment_schedule) :

			resch_table_len = len(self.repayment_schedule)
			sch_table_len = len(loan_rep_sch_doc.repayment_schedule)


			for row in self.repayment_schedule :
				values = {
							'loan_rep_sch': self.loan_repayment_schedule ,
							'payment_date' : row.payment_date ,
							'number_of_days' : row.number_of_days ,
							'principal_amount' : row.principal_amount ,
							'interest_amount' : row.interest_amount ,
							'total_payment' : row.total_payment ,
							'balance_loan_amount' : row.balance_loan_amount ,
							'is_accrued' : row.is_accrued ,
							'id' : row.idx ,
						}
				query = frappe.db.sql("""
						UPDATE `tabRepayment Schedule`
						SET payment_date = %(payment_date)s ,
							number_of_days = %(number_of_days)s  ,
							principal_amount = %(principal_amount)s ,
							interest_amount = %(interest_amount)s ,
							total_payment = %(total_payment)s ,
							balance_loan_amount = %(balance_loan_amount)s ,
							is_accrued = %(is_accrued)s
						WHERE parent = %(loan_rep_sch)s and idx = %(id)s
					""", values=values , as_dict=1)

			for i in range(resch_table_len + 1 , sch_table_len + 1) :

				values = {
							'loan_rep_sch': self.loan_repayment_schedule ,
							'id' : i ,
						}

				frappe.db.sql(""" 
					DELETE FROM `tabRepayment Schedule`
					WHERE parent = %(loan_rep_sch)s 
					AND idx = %(id)s
					AND parenttype = 'Loan Repayment Schedule'
				""", values=values , as_dict=1)		

		elif len(loan_rep_sch_doc.repayment_schedule) < len(self.repayment_schedule) :
			
			resch_table_len = len(self.repayment_schedule)
			sch_table_len = len(loan_rep_sch_doc.repayment_schedule)

			for row in self.repayment_schedule :
				values = {
							'loan_rep_sch': self.loan_repayment_schedule ,
							'payment_date' : row.payment_date ,
							'number_of_days' : row.number_of_days ,
							'principal_amount' : row.principal_amount ,
							'interest_amount' : row.interest_amount ,
							'total_payment' : row.total_payment ,
							'balance_loan_amount' : row.balance_loan_amount ,
							'is_accrued' : row.is_accrued ,
							'id' : row.idx ,
						}
				query = frappe.db.sql("""
						UPDATE `tabRepayment Schedule`
						SET payment_date = %(payment_date)s ,
							number_of_days = %(number_of_days)s  ,
							principal_amount = %(principal_amount)s ,
							interest_amount = %(interest_amount)s ,
							total_payment = %(total_payment)s ,
							balance_loan_amount = %(balance_loan_amount)s ,
							is_accrued = %(is_accrued)s
						WHERE parent = %(loan_rep_sch)s and idx = %(id)s
					""", values=values , as_dict=1)
				
				if sch_table_len == row.idx :
					break

			for x in self.repayment_schedule :

				sch_table_len = len(loan_rep_sch_doc.repayment_schedule)

				if x.idx > sch_table_len :
					
					repayment_schedule_doc = frappe.get_doc({ 
						'doctype': 'Repayment Schedule',
						'parent': self.loan_repayment_schedule,
						'parentfield': 'repayment_schedule',
						'parenttype': 'Loan Repayment Schedule',
						'payment_date': x.payment_date ,
						'principal_amount': x.principal_amount ,
						'number_of_days' : x.number_of_days ,
						'interest_amount' : x.interest_amount ,
						'total_payment' : x.total_payment ,
						'balance_loan_amount' : x.balance_loan_amount ,
						'is_accrued' : x.is_accrued ,
						'idx': x.idx
					
					})
					repayment_schedule_doc.insert()
					

			







				




		# values = {
		# 			'loan_rep_sch' : self.loan_repayment_schedule
		# 		}
				

		# frappe.db.sql(""" 
		# 	DELETE FROM `tabRepayment Schedule`
		# 	WHERE parent = %(loan_rep_sch)s
		# 	AND parenttype = 'Loan Repayment Schedule'
		# """, values=values , as_dict=1)



		# insert_position = 1
		# for x in self.repayment_schedule :

		# 	repayment_schedule_doc = frappe.get_doc({ 
		# 		'doctype': 'Repayment Schedule',
		# 		'parent': self.loan_repayment_schedule,
		# 		'parentfield': 'repayment_schedule',
		# 		'parenttype': 'Loan Repayment Schedule',
		# 		'payment_date': x.payment_date ,
		# 		'principal_amount': x.principal_amount ,
		# 		'number_of_days' : x.number_of_days ,
		# 		'interest_amount' : x.interest_amount ,
		# 		'total_payment' : x.total_payment ,
		# 		'balance_loan_amount' : x.balance_loan_amount ,
		# 		'is_accrued' : x.is_accrued ,
		# 		'idx': insert_position
			
		# 	})

		# 	insert_position = insert_position + 1

		# 	repayment_schedule_doc.insert()

		# insert_position = insert_position - 1
		# frappe.db.set_value('Loan Repayment Schedule', self.loan_repayment_schedule, 'repayment_periods', insert_position)	







