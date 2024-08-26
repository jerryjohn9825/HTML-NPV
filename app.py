from flask import Flask, request, render_template_string
import numpy as np
import pandas as pd

app = Flask(__name__)

def calculate_pv(rate, term, rental):
    monthly_rate = rate / 12
    pv = sum([rental / (1 + monthly_rate) ** i for i in range(1, term + 1)])
    return pv

def calculate_cbr(current_full_rental, remaining_term):
    cbr = current_full_rental * remaining_term
    return cbr

def calculate_npv_sl_paydown_and_cbr(slc_securitized_rental, slc_interest_rate, inhouse_interest_rate, slc_nper, full_rental, full_term, start_date, rental_increase_percentage, rental_increase_month):
    monthly_interest_rate = slc_interest_rate / 12
    inhouse_monthly_interest_rate = inhouse_interest_rate / 12
    
    slc_npv_values = []
    slc_paydown_values = []
    cbr_values = []
    inhouse_pv_values = []
    cash_collection_original_rental_values = []
    cash_collection_escalated_rental_values = []
    
    dates = pd.date_range(start=start_date, periods=full_term, freq='MS')
    
    cumulative_rental = 0
    cumulative_rental_with_increase = 0
    current_full_rental = full_rental

    for t in range(full_term):
        current_date = dates[t]
        
        if current_date.month == rental_increase_month and t > 0:
            current_full_rental *= (1 + rental_increase_percentage / 100)
        
        if t < slc_nper:
            slc_npv = sum([slc_securitized_rental / (1 + monthly_interest_rate) ** i for i in range(1 + t, slc_nper)]) + slc_securitized_rental / (1 + monthly_interest_rate) ** t
        else:
            slc_npv = 0
        
        slc_paydown = sum([slc_securitized_rental for _ in range(t, slc_nper)]) if t < slc_nper else 0
        
        cbr = calculate_cbr(current_full_rental, full_term - t)
        
        inhouse_pv = calculate_pv(inhouse_interest_rate, full_term - t, full_rental)
        
        cumulative_rental += full_rental
        cumulative_rental_with_increase += current_full_rental
        
        slc_npv_values.append(slc_npv)
        slc_paydown_values.append(slc_paydown)
        cbr_values.append(cbr)
        inhouse_pv_values.append(inhouse_pv)
        cash_collection_original_rental_values.append(cumulative_rental)
        cash_collection_escalated_rental_values.append(cumulative_rental_with_increase)
    
    first_slc_npv = slc_npv_values[0]
    first_cbr = cbr_values[0]
    first_inhouse_pv = inhouse_pv_values[0]
    last_slc_paydown = slc_paydown_values[-1]
    last_cash_collection_original_rental = cash_collection_original_rental_values[-1]
    last_cash_collection_escalated_rental = cash_collection_escalated_rental_values[-1]
    
    return first_slc_npv, first_cbr, first_inhouse_pv, last_slc_paydown, last_cash_collection_original_rental, last_cash_collection_escalated_rental

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        full_rental = float(request.form['full_rental'])
        slc_interest_rate = float(request.form['slc_interest_rate']) / 100
        inhouse_interest_rate = float(request.form['inhouse_interest_rate']) / 100
        slc_nper = int(request.form['slc_nper'])
        full_term = int(request.form['full_term'])
        start_date = request.form['start_date']
        rental_increase_percentage = float(request.form['rental_increase_percentage'])
        rental_increase_month = int(request.form['rental_increase_month'])
        
        slc_securitized_rental = 0.96 * full_rental
        
        first_slc_npv, first_cbr, first_inhouse_pv, last_slc_paydown, last_cash_collection_original_rental, last_cash_collection_escalated_rental = calculate_npv_sl_paydown_and_cbr(
            slc_securitized_rental, slc_interest_rate, inhouse_interest_rate, slc_nper, full_rental, full_term, start_date, rental_increase_percentage, rental_increase_month)
        
        return render_template_string(html_template,
                                      full_rental=full_rental,
                                      slc_interest_rate=slc_interest_rate * 100,
                                      inhouse_interest_rate=inhouse_interest_rate * 100,
                                      slc_nper=slc_nper,
                                      full_term=full_term,
                                      start_date=start_date,
                                      rental_increase_percentage=rental_increase_percentage,
                                      rental_increase_month=rental_increase_month,
                                      first_slc_npv=first_slc_npv,
                                      first_cbr=first_cbr,
                                      first_inhouse_pv=first_inhouse_pv,
                                      last_slc_paydown=last_slc_paydown,
                                      last_cash_collection_original_rental=last_cash_collection_original_rental,
                                      last_cash_collection_escalated_rental=last_cash_collection_escalated_rental)
    else:
        return render_template_string(html_template)

html_template = """
<html>
<head>
    <title>Financial Calculations</title>
</head>
<body>
    <h1>Financial Calculations Input</h1>
    <form method="POST">
        <label for="full_rental">Full Rental:</label>
        <input type="number" id="full_rental" name="full_rental" value="{{ full_rental }}" step="0.01"><br><br>

        <label for="slc_interest_rate">SLC Interest Rate (%):</label>
        <input type="number" id="slc_interest_rate" name="slc_interest_rate" value="{{ slc_interest_rate }}" step="0.01"><br><br>

        <label for="inhouse_interest_rate">Inhouse Interest Rate (%):</label>
        <input type="number" id="inhouse_interest_rate" name="inhouse_interest_rate" value="{{ inhouse_interest_rate }}" step="0.01"><br><br>

        <label for="slc_nper">SLC NPER:</label>
        <input type="number" id="slc_nper" name="slc_nper" value="{{ slc_nper }}"><br><br>

        <label for="full_term">Full Term (months):</label>
        <input type="number" id="full_term" name="full_term" value="{{ full_term }}"><br><br>

        <label for="start_date">Start Date:</label>
        <input type="date" id="start_date" name="start_date" value="{{ start_date }}"><br><br>

        <label for="rental_increase_percentage">Rental Increase Percentage:</label>
        <input type="number" id="rental_increase_percentage" name="rental_increase_percentage" value="{{ rental_increase_percentage }}" step="0.01"><br><br>

        <label for="rental_increase_month">Rental Increase Month:</label>
        <input type="number" id="rental_increase_month" name="rental_increase_month" value="{{ rental_increase_month }}" min="1" max="12"><br><br>

        <input type="submit" value="Calculate">
    </form>

    {% if first_slc_npv is not none %}
    <h2>Results</h2>
    <p><strong>First SLC NPV:</strong> {{ first_slc_npv:.2f }}</p>
    <p><strong>First CBR:</strong> {{ first_cbr:.2f }}</p>
    <p><strong>First Inhouse PV:</strong> {{ first_inhouse_pv:.2f }}</p>
    <p><strong>Last SLC Paydown:</strong> {{ last_slc_paydown:.2f }}</p>
    <p><strong>Last Cash Collection (@Original Rental):</strong> {{ last_cash_collection_original_rental:.2f }}</p>
    <p><strong>Last Cash Collection (@Escalated Rental):</strong> {{ last_cash_collection_escalated_rental:.2f }}</p>
    {% endif %}
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
