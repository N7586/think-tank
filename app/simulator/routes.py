from flask import Blueprint, render_template, request
from app.simulator import simulator_bp


@simulator_bp.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            investment = float(request.form.get('investment', 0))
            unit_price = float(request.form.get('unit_price', 100))
            expected_return = float(request.form.get('expected_return', 8.5))
            duration = int(request.form.get('duration', 12))

            units = int(investment / unit_price)
            monthly_rate = expected_return / 100 / 12
            final_value = investment * ((1 + monthly_rate) ** duration)
            gain = final_value - investment
            monthly_income = (investment * monthly_rate) if monthly_rate > 0 else 0

            result = {
                'investment': investment,
                'units': units,
                'unit_price': unit_price,
                'expected_return': expected_return,
                'duration': duration,
                'final_value': round(final_value, 2),
                'gain': round(gain, 2),
                'monthly_income': round(monthly_income, 2),
                'return_percentage': round((gain / investment) * 100, 2) if investment > 0 else 0
            }
        except (ValueError, TypeError, ZeroDivisionError):
            result = None

    return render_template('simulator/index.html', result=result)
