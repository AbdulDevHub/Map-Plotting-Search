"""
CSC148, Winter 2022
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call

# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """
    A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """
        Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class MTMContract(Contract):
    """
    A Month to Month contract for a phone line. It is an inherited
    class from the Contract class

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    month:
        the current month of the bill
    year:
        the current year of the bill
    """
    month: int
    year: int

    def __init__(self, start: datetime.date) -> None:
        """
        Create a new MTM Contract with the <start> date, starts as inactive
        """
        Contract.__init__(self, start)
        self.month = None
        self.year = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """
        Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        self.month = month
        self.year = year
        self.bill = bill
        self.bill.set_rates("MTM", MTM_MINS_COST)
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)


class TermContract(Contract):
    """
    A Term contract for a phone line. It is an inherited
    class from the Contract class

    === Public Attributes ===
    start:
         starting date for the contract
    end:
        ending date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    month:
        the current month of the bill
    year:
        the current year of the bill
    """
    end: datetime.date
    month: int
    year: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """
        Create a new Term Contract with the <start> & <end> date, starts as
        inactive
        """
        Contract.__init__(self, start)
        self.end = end
        self.month = None
        self.year = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """
        Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost. The fixed cost also accounts for Term deposit
        in the first month.
        """
        self.month = month
        self.year = year
        self.bill = bill
        self.bill.set_rates("TERM", TERM_MINS_COST)
        if self.year == self.start.year and self.month == self.start.month:
            self.bill.add_fixed_cost(TERM_DEPOSIT + TERM_MONTHLY_FEE)
        else:
            self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
        self.bill.add_free_minutes(0)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.

        The bill also has to account for free minutes
        """
        super().bill_call(call)
        min_used = ceil(call.duration / 60.0)

        if self.bill.billed_min <= TERM_MINS:
            self.bill.set_rates("TERM", 0)
            self.bill.add_free_minutes(min_used)
        else:
            remaining_min = self.bill.billed_min - self.bill.free_min
            actual = TERM_MINS_COST * remaining_min + TERM_MONTHLY_FEE
            rate = (actual - TERM_MONTHLY_FEE) / remaining_min
            self.bill.set_rates("TERM", rate)
            self.bill.add_free_minutes(TERM_MINS - self.bill.free_min)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract. Account for balance if cancelled after end date.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.end = None
        if self.year > self.end.year or \
                (self.month > self.end.month and self.year >= self.end.year):
            return super().cancel_contract() - TERM_DEPOSIT
        return super().cancel_contract()


class PrepaidContract(Contract):
    """
    A prepaid contract for a phone line. It is an inherited
    class from the Contract class

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    month:
        the current month of the bill
    year:
        the current year of the bill
    balance:
        The credit (prepaid amount) of the customer. It also represents
        the amount owed by the customer
    """
    month: int
    year: int
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """
        Create a new Prepaid Contract with the <start> date and <balance>,
        starts as inactive
        """
        Contract.__init__(self, start)
        self.month = None
        self.year = None
        self.balance = -balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """
        Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost. The fixed cost correlates with the balance
        and the balance gets $25 top up if balance under $10.
        """
        self.month = month
        self.year = year
        self.bill = bill
        self.bill.set_rates("PREPAID", PREPAID_MINS_COST)
        if self.balance > -10:
            self.balance -= 25
        self.bill.add_fixed_cost(self.balance)
        self.balance = bill.get_cost()

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract. Return balance if positive else return 0 to indicate
        no amount owed.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        if self.balance >= 0:
            return self.balance
        return 0


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
