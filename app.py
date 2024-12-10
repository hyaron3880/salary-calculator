from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def calculate_tax_credits(data):
    gender = data.get('gender', 'male')
    points = 2.25 if gender == 'male' else 2.75
    
    # מצב משפחתי
    if data.get('single_parent', False):
        points += 1
    if data.get('marital_status') == 'married' and not data.get('spouse_income', False):
        points += 1

    # חישוב נקודות לילדים
    children_0 = int(data.get('children_0', 0))
    children_1_5 = int(data.get('children_1_5', 0))
    children_6_17 = int(data.get('children_6_17', 0))
    children_18 = int(data.get('children_18', 0))

    points += children_0 * (1.5 if gender == 'male' else 0.5)
    points += children_1_5 * (2.5 if gender == 'male' else 2)
    points += children_6_17 * 1
    points += children_18 * 0.5

    # עולה חדש
    new_immigrant_years = data.get('new_immigrant_years')
    if new_immigrant_years:
        if new_immigrant_years == 1:
            points += 3
        elif new_immigrant_years == 2:
            points += 2
        elif new_immigrant_years == 3:
            points += 1

    # השכלה
    if data.get('education_completed', False):
        points += 1

    # שירות צבאי או לאומי
    if data.get('military_service_completed', False):
        points += 2

    return points

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        gross_salary = float(data.get('gross_salary', 0))
        points_of_credit = calculate_tax_credits(data)
        is_over_60 = data.get('is_over_60', False)
        non_personal_income = data.get('non_personal_income', False)

        # חישוב המס לפי מדרגות המס
        tax_brackets = [
            (0, 7860, 0.1),
            (7861, 11320, 0.14),
            (11321, 14960, 0.2),
            (14961, 22280, 0.31),
            (22281, 48160, 0.35),
            (48161, 75040, 0.47),
            (75041, float('inf'), 0.5)
        ]

        total_tax = 0
        remaining_salary = gross_salary

        for min_bracket, max_bracket, tax_rate in tax_brackets:
            if remaining_salary <= 0:
                break
            
            taxable_amount = min(remaining_salary, max_bracket - min_bracket + 1)
            tax = taxable_amount * tax_rate
            total_tax += tax
            remaining_salary -= taxable_amount

        # חישוב זיכוי מס
        credit_point_value = 243
        tax_credit = points_of_credit * credit_point_value

        # הפחתת זיכוי מס מהמס הכולל
        final_tax = max(0, total_tax - tax_credit)

        # חישוב ביטוח לאומי
        national_insurance_brackets = [
            (0, 7122, 0.004),
            (7123, 49828, 0.07),
            (49829, float('inf'), 0)
        ]

        total_ni = 0
        remaining_salary_ni = gross_salary

        for min_bracket, max_bracket, ni_rate in national_insurance_brackets:
            if remaining_salary_ni <= 0:
                break
            
            ni_amount = min(remaining_salary_ni, max_bracket - min_bracket + 1)
            ni = ni_amount * ni_rate
            total_ni += ni
            remaining_salary_ni -= ni_amount

        # חישוב ביטוח בריאות
        health_insurance_brackets = [
            (0, 7122, 0.031),
            (7123, 49828, 0.05),
            (49829, float('inf'), 0)
        ]

        total_health = 0
        remaining_salary_health = gross_salary

        for min_bracket, max_bracket, health_rate in health_insurance_brackets:
            if remaining_salary_health <= 0:
                break
            
            health_amount = min(remaining_salary_health, max_bracket - min_bracket + 1)
            health = health_amount * health_rate
            total_health += health
            remaining_salary_health -= health_amount

        # חישוב שכר נטו
        net_salary = gross_salary - final_tax - total_ni - total_health

        return jsonify({
            'gross_salary': gross_salary,
            'tax_credit_points': points_of_credit,
            'tax_credit_amount': tax_credit,
            'income_tax': final_tax,
            'national_insurance': total_ni,
            'health_insurance': total_health,
            'net_salary': net_salary
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5004)
