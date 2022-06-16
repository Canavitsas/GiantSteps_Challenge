from datetime import datetime
import pandas as pd
from pandas.tseries.offsets import BMonthEnd, BYearEnd

# Constants section
MIN_DATE = datetime.strptime("01/01/1995", "%d/%m/%Y")

# Helper functions

# Get calendar date
# Expected format dd/mm/yyyy
def get_date(raise_min_date_error:bool = False) -> datetime:
    try:
        x = input()
        date = datetime.strptime(x, '%d/%m/%Y')
        if (date < MIN_DATE and raise_min_date_error):
            raise MinDateError
        return date
    
    except MinDateError:
        print(f"Start date must be after {MIN_DATE}")

    except ValueError:
        print('You have entered an invalid value. Expected value: dd/mm/yyyy')

# Get both start_date and end_date
def get_period():
    print("Start date: ")
    start_date = get_date(True)
    while (not start_date):
        print("Start date: ")
        start_date = get_date(True)

    print("End date: ")
    end_date = get_date()
    while (not end_date):
        print("End date: ")
        end_date = get_date()

    return start_date, end_date

# Returns true if end_date comes after start_date, false otherwide
def validate_period(start_date: datetime, end_date:datetime) -> bool:
    if (start_date >= end_date):
        print('End date must be later than start date')
        return False
    return True

# Get initial investment amount
def get_capital():
    try:
        capital = float(input("Insert capital: "))
        return capital
    except ValueError:
        print('You have entered an invalid value. Expected value: float')


# How often accrued interest will be displayed for user
# Expected values are "day", "month" and "year"
def get_frequency():
    return str(input("Insert frequency: "))

# Returns true if text entered is one of the expected values
# Expected values are "day", "month" and "year"
def validate_frequency(text):
    if (text == "day" or text == "month" or text == "year"):
        return True
    return False

# Exception raised when start date 
class MinDateError(Exception):
    pass

start_date, end_date = get_period()
while (not validate_period(start_date, end_date)):
  start_date, end_date = get_period()

capital = get_capital()
while (not capital):
  capital = get_capital()

frequency = get_frequency()
while (not validate_frequency(frequency)):
  frequency = get_frequency()

url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={start_date.day}/{start_date.month}/{start_date.year}&dataFinal={end_date.day}/{end_date.month}/{end_date.year}"
selic_rates = pd.read_json(url)
print(selic_rates)

# Converting 'data' column values to datetime format
selic_rates['data'] = pd.to_datetime(selic_rates['data'], format='%d/%m/%Y')

#removing any selic rates from before the start_date.  For some reason if we use 'x' date, we get the before date as well.
selic_rates = selic_rates.loc[selic_rates['data'] >= start_date]
print(selic_rates)

# creating a list of dictionaries where each dict is a row of the final table
final_table = []
amount_earned = 0
offset_m = BMonthEnd() # to find last/first business day
offset_y = BYearEnd() # to find last/first business day
# iterating through the dataframe using to_dict('records') because it appears to be multiple times faster than using iterrows (https://towardsdatascience.com/heres-the-most-efficient-way-to-iterate-through-your-pandas-dataframe-4dad88ac92ee#:~:text=Vectorization%20is%20always%20the%20first,up%20for%2020%20million%20records.)
for row in selic_rates.to_dict('records'):
    #appends when frequency == day or when current date is either the end_date or the last business day for that month/year
    if (frequency == 'day' or
       (frequency == 'month' and (row['data'] == offset_m.rollforward(row['data']) or row['data'] == end_date)) or
       (frequency == 'year' and (row['data'] == offset_y.rollforward(row['data']) or row['data'] == end_date ))):
        final_table.append({'Date': row['data'], 'Capital': capital + amount_earned, 'Amount Earned': amount_earned })
    amount_earned += (capital + amount_earned) * row['valor']/100

final_df = pd.DataFrame(final_table)
print(final_df)

highestProfit = 0
currStartDate = start_date
startIndex = 0 # index from which we will start looking for the first selic rate inside the 500 days period
endIndex = 0 # index from which we will start looking for the last selic rate inside the 500 days period
while(currStartDate != end_date):
    currEndDate = currStartDate + DateOffset(days=499)
    #get first date in our rates table that is after currStartDate
    for i in range(startIndex, len(final_table)):
        if final_table[i]['Date'] >= currStartDate:
            currStartCapital= final_table[i]['Capital']
            startIndex = i
            break

    #get last date in our rates table that is still before currEndDate
    for i in range(endIndex, len(final_table)):
        if final_table[i]['Date'] > currEndDate:
            currEndCapital = final_table[i-1]['Capital']
            endIndex = i-1
            # print(f"endINdex {endIndex}")
            break

    currIntervalProfit = (currEndCapital - currStartCapital)/currStartCapital
    if currIntervalProfit > highestProfit:
        highestProfit = currIntervalProfit
        highestProfitStartDate = currStartDate
        highestProfitEndDate = currEndDate

    currStartDate += DateOffset(days = 1)

print(highestProfit)
print(highestProfitStartDate)
print(highestProfitEndDate)