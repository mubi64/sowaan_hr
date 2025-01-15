# Copyright (c) 2024, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime


class LoanRepaymentReschedule(Document):


	def before_save(self) :

		next_row = []
		indx = 0

		loan_rp_sch_list = frappe.db.get_list("Loan Repayment Schedule",
								filters = {
									'loan' : self.loan ,
									'docstatus' : 1 ,
									'status' : 'Active' ,
								}
							)

		if loan_rp_sch_list :

			if len(loan_rp_sch_list) > 1 :
				frappe.throw("More than one Active Repayment Schedule found.")


			loan_rp_sch_doc = frappe.get_doc("Loan Repayment Schedule", loan_rp_sch_list[0].name)
			self.loan_repayment_schedule = loan_rp_sch_list[0].name
			
			values = {
						'loan_rep_sch': loan_rp_sch_list[0].name,
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
			last_balance = loan_rp_sch_doc.loan_amount

			if self.adjustment_type == 'Leading Installments' :
					
				same_date_sig = 0
				row_inserted = 0
				same_date_sig = 0
				less_amount = 0
				next_row_amount = 0
				extra_amount = 0
				extra_amount_end = 0


				for row in repayment_schedule_table :

					if str(self.payment_date) > str(row.payment_date) :
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

					elif str(self.payment_date) < str(row.payment_date) :

						if same_date_sig == 1 :
							
							if less_amount == 2 :
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
							
							if less_amount == 1 :
								self.append('repayment_schedule',{
									'payment_date' : row.payment_date ,
									'number_of_days' : row.number_of_days ,
									'principal_amount' : row.principal_amount + next_row_amount ,
									'interest_amount' : row.interest_amount ,
									'total_payment' : row.total_payment + next_row_amount ,
									'balance_loan_amount' : row.balance_loan_amount ,
									'is_accrued' : row.is_accrued ,
								})
								last_balance = row.balance_loan_amount
								less_amount = 2

							if less_amount == 0 :

								if next_row_amount <= row.principal_amount :
									self.append('repayment_schedule',{
										'payment_date' : row.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : row.principal_amount - next_row_amount ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : row.total_payment - next_row_amount ,
										'balance_loan_amount' : row.balance_loan_amount ,
										'is_accrued' : row.is_accrued ,
									})
									last_balance = row.balance_loan_amount
									less_amount = 2

								else :
									self.append('repayment_schedule',{
										'payment_date' : row.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : 0  ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : 0 ,
										'balance_loan_amount' : last_balance ,
										'is_accrued' : row.is_accrued ,
									})
									last_balance = last_balance
									next_row_amount = next_row_amount - row.principal_amount

						elif same_date_sig == 0 :

							if row_inserted == 0 :

								if self.payment_amount > last_balance :
									frappe.throw("Payment Amount cannot be greater than Balance Amount.")
								
								else :
									cur_balance = last_balance - self.payment_amount
									self.append('repayment_schedule',{
										'payment_date' : self.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : self.payment_amount ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : self.payment_amount ,
										'balance_loan_amount' : cur_balance ,
										'is_accrued' : row.is_accrued ,
									})
									last_balance = cur_balance
									extra_amount = self.payment_amount
									row_inserted = 1
									
							if row_inserted == 1 :

								if extra_amount_end == 1 :
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
								
								elif extra_amount <= row.principal_amount :
									self.append('repayment_schedule',{
										'payment_date' : row.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : row.principal_amount - extra_amount ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : row.total_payment - extra_amount ,
										'balance_loan_amount' : row.balance_loan_amount ,
										'is_accrued' : row.is_accrued ,
									})
									last_balance = row.balance_loan_amount
									extra_amount_end = 1
									
								else :
									self.append('repayment_schedule',{
										'payment_date' : row.payment_date ,
										'number_of_days' : row.number_of_days ,
										'principal_amount' : 0  ,
										'interest_amount' : row.interest_amount ,
										'total_payment' : 0 ,
										'balance_loan_amount' : last_balance ,
										'is_accrued' : row.is_accrued ,
									})
									last_balance = last_balance
									extra_amount = extra_amount - row.principal_amount
									
					elif str(self.payment_date) == str(row.payment_date) :

						same_date_sig = 1
						
						if self.payment_amount <= row.total_payment :
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
							next_row_amount = row.principal_amount - self.payment_amount
							less_amount = 1

						elif self.payment_amount > row.total_payment :

							if self.payment_amount > last_balance :
								frappe.throw("Payment Amount cannot be greater than Loan Balance.")

							else :
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
								next_row_amount = self.payment_amount - row.principal_amount
				
				final_amount = self.repayment_schedule[-1].principal_amount + self.repayment_schedule[-1].balance_loan_amount
				self.repayment_schedule[-1].principal_amount = final_amount
				self.repayment_schedule[-1].total_payment = final_amount
				self.repayment_schedule[-1].balance_loan_amount = 0


			elif self.adjustment_type == 'Last Installments' :

				same_date_sig = 0
				installments = []

				for row in repayment_schedule_table :
					installment = {
						'last_balance' : last_balance ,
						'date' : row.payment_date ,
						'amount' : row.principal_amount ,
						'is_accrued' : row.is_accrued ,
						'number_of_days' : row.number_of_days ,
						'interest_amount' : row.interest_amount ,
					}
					installments.append(installment)
					last_balance = row.balance_loan_amount

				
				for i in range(len(installments)) :

					if str(installments[i]['date']) == str(self.payment_date) :
						if installments[i]['last_balance'] < self.payment_amount :
							frappe.throw("Balance Amount cannot be greater than Loan Balance.")
						else :	
							installments[i] = {
								'last_balance' : installments[i]['last_balance'] ,
								'date': self.payment_date,
								'amount': self.payment_amount,
								'is_accrued' : installments[i]['is_accrued'] ,
								'number_of_days' : installments[i]['number_of_days'] ,
								'interest_amount' : installments[i]['interest_amount'] ,
							}
							break

					elif str(installments[i]['date']) > str(self.payment_date) :
						if installments[i]['last_balance'] < self.payment_amount :
							frappe.throw("Balance Amount cannot be greater than Loan Balance.")
						else :	
							installments.insert(i, {
								'last_balance' : installments[i]['last_balance'] ,
								'date': self.payment_date,
								'amount': self.payment_amount,
								'is_accrued' : installments[i]['is_accrued'] ,
								'number_of_days' : installments[i]['number_of_days'] ,
								'interest_amount' : installments[i]['interest_amount'] ,
							})
							break


				balance = loan_rp_sch_doc.loan_amount
				
				for x in installments :	

					if round(balance,2) > round(x['amount'],2) :
						self.append('repayment_schedule',{
							'payment_date' : x['date'] ,
							'number_of_days' : x['number_of_days'] ,
							'principal_amount' : round(x['amount'],2) ,
							'interest_amount' : x['interest_amount'] ,
							'total_payment' : round(x['amount'],2) ,
							'balance_loan_amount' : round(balance,2) - round(x['amount'],2) ,
							'is_accrued' : x['is_accrued'] ,
						})
						balance = balance - x['amount']

					elif balance <= x['amount'] :
						self.append('repayment_schedule',{
							'payment_date' : x['date'] ,
							'number_of_days' : x['number_of_days'] ,
							'principal_amount' : round(balance,2) ,
							'interest_amount' : x['interest_amount'] ,
							'total_payment' : round(balance,2) ,
							'balance_loan_amount' : 0 ,
							'is_accrued' : x['is_accrued'] ,
						})
						break
				

				final_amount = self.repayment_schedule[-1].principal_amount + self.repayment_schedule[-1].balance_loan_amount
				self.repayment_schedule[-1].principal_amount = final_amount
				self.repayment_schedule[-1].total_payment = final_amount
				self.repayment_schedule[-1].balance_loan_amount = 0		

			for xy in self.repayment_schedule :
				if xy.balance_loan_amount == 0 :
					indx = xy.idx
					break

			self.repayment_schedule = [
				row for row in self.repayment_schedule if row.idx <= indx
			]	


							

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
						'idx': x.idx ,
						'docstatus' : 1 ,
					
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







