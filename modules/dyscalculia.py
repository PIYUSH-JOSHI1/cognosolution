from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import random
import csv
import os
from datetime import datetime

dyscalculia_bp = Blueprint('dyscalculia', __name__)

class DyscalculiaAI:
    def __init__(self):
        self.difficulty_levels = {
            'easy': {'range': (1, 10), 'operations': ['+', '-']},
            'medium': {'range': (1, 50), 'operations': ['+', '-', '*']},
            'hard': {'range': (1, 100), 'operations': ['+', '-', '*', '/']}
        }
    
    def generate_math_problem(self, difficulty='easy', operation=None):
        """Generate math problems based on difficulty"""
        level = self.difficulty_levels[difficulty]
        min_val, max_val = level['range']
        ops = level['operations']
        
        if operation and operation in ops:
            op = operation
        else:
            op = random.choice(ops)
        
        a = random.randint(min_val, max_val)
        b = random.randint(min_val, max_val)
        
        if op == '+':
            answer = a + b
            problem = f"{a} + {b}"
        elif op == '-':
            if a < b:
                a, b = b, a  # Ensure positive result
            answer = a - b
            problem = f"{a} - {b}"
        elif op == '*':
            answer = a * b
            problem = f"{a} × {b}"
        elif op == '/':
            # Ensure clean division
            answer = random.randint(1, 12)
            a = answer * b
            problem = f"{a} ÷ {b}"
        
        return {
            'problem': problem,
            'answer': answer,
            'operation': op,
            'difficulty': difficulty
        }
    
    def generate_number_sequence(self, start=1, step=1, length=5):
        """Generate number sequences for pattern recognition"""
        sequence = []
        current = start
        for _ in range(length):
            sequence.append(current)
            current += step
        
        return {
            'sequence': sequence[:-1],  # Hide last number
            'missing': sequence[-1],
            'pattern': f"Add {step}"
        }
    
    def generate_visual_math(self, difficulty='easy'):
        """Generate visual math problems with objects"""
        objects = ['🍎', '🐕', '⭐', '🚗', '🏠', '🌸', '📚', '⚽']
        obj = random.choice(objects)
        
        if difficulty == 'easy':
            a = random.randint(1, 5)
            b = random.randint(1, 5)
            operation = random.choice(['+', '-'])
        else:
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = a + b
            visual = f"{obj * a} + {obj * b} = ?"
        elif operation == '-':
            if a < b:
                a, b = b, a
            answer = a - b
            visual = f"{obj * a} - {obj * b} = ?"
        elif operation == '*':
            answer = a * b
            visual = f"{a} groups of {obj * b} = ?"
        
        return {
            'visual': visual,
            'answer': answer,
            'objects_count': {'a': a, 'b': b},
            'operation': operation
        }

dyscalculia_ai = DyscalculiaAI()

@dyscalculia_bp.route('/')
def main():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dyscalculia/main.html')

@dyscalculia_bp.route('/practice')
def practice():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dyscalculia/practice.html')

@dyscalculia_bp.route('/generate-problem', methods=['POST'])
def generate_problem():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    difficulty = data.get('difficulty', 'easy')
    problem_type = data.get('type', 'arithmetic')
    
    if problem_type == 'arithmetic':
        problem = dyscalculia_ai.generate_math_problem(difficulty)
    elif problem_type == 'sequence':
        problem = dyscalculia_ai.generate_number_sequence()
    elif problem_type == 'visual':
        problem = dyscalculia_ai.generate_visual_math(difficulty)
    
    return jsonify({'success': True, 'problem': problem})

@dyscalculia_bp.route('/math-practice')
def math_practice():
    if 'user_id' not in session:
        return redirect('/auth/login')
    return render_template('dyscalculia/math_practice.html')

@dyscalculia_bp.route('/practice/<activity_type>')
def practice_activity(activity_type):
    if 'user_id' not in session:
        return redirect('/auth/login')
    
    # Initialize session variables for the practice
    session['current_activity'] = activity_type
    session['current_score'] = 0
    session['current_question'] = 1
    session['total_questions'] = 10
    session['practice_start_time'] = datetime.now().isoformat()
    
    # Generate first question
    question_data = generate_question(activity_type)
    session['current_answer'] = question_data['answer']
    
    return render_template('dyscalculia/practice_session.html', 
                         activity_type=activity_type,
                         question=question_data['question'],
                         question_num=1,
                         total_questions=10,
                         score=0)

@dyscalculia_bp.route('/check-answer', methods=['POST'])
def check_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    try:
        data = request.get_json()
        user_answer = data.get('answer')
        correct_answer = session.get('current_answer')
        current_question = session.get('current_question', 1)
        current_score = session.get('current_score', 0)
        total_questions = session.get('total_questions', 10)
        activity_type = session.get('current_activity')
        
        # Check if answer is correct
        is_correct = False
        if user_answer is not None and correct_answer is not None:
            try:
                is_correct = float(user_answer) == float(correct_answer)
            except (ValueError, TypeError):
                is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        
        if is_correct:
            current_score += 1
            session['current_score'] = current_score
        
        # Check if this was the last question
        if current_question >= total_questions:
            # Save results to CSV
            save_practice_result(session['user_id'], activity_type, current_score, total_questions)
            
            # Clear session variables
            session.pop('current_activity', None)
            session.pop('current_answer', None)
            session.pop('current_question', None)
            session.pop('current_score', None)
            session.pop('total_questions', None)
            session.pop('practice_start_time', None)
            
            return jsonify({
                'correct': is_correct,
                'correct_answer': correct_answer,
                'finished': True,
                'final_score': current_score,
                'total_questions': total_questions,
                'percentage': round((current_score / total_questions) * 100, 1)
            })
        
        # Generate next question
        current_question += 1
        session['current_question'] = current_question
        
        question_data = generate_question(activity_type)
        session['current_answer'] = question_data['answer']
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'finished': False,
            'next_question': question_data['question'],
            'question_num': current_question,
            'score': current_score,
            'total_questions': total_questions
        })
        
    except Exception as e:
        print(f"Error in check_answer: {e}")
        return jsonify({'error': 'An error occurred'})

def generate_question(activity_type):
    """Generate a question based on activity type"""
    
    if activity_type == 'addition':
        a = random.randint(1, 50)
        b = random.randint(1, 50)
        question = f"{a} + {b} = ?"
        answer = a + b
        
    elif activity_type == 'subtraction':
        a = random.randint(10, 100)
        b = random.randint(1, a)
        question = f"{a} - {b} = ?"
        answer = a - b
        
    elif activity_type == 'multiplication':
        a = random.randint(1, 12)
        b = random.randint(1, 12)
        question = f"{a} × {b} = ?"
        answer = a * b
        
    elif activity_type == 'division':
        b = random.randint(1, 12)
        answer = random.randint(1, 12)
        a = b * answer
        question = f"{a} ÷ {b} = ?"
        
    elif activity_type == 'fractions':
        numerator1 = random.randint(1, 10)
        denominator1 = random.randint(2, 10)
        numerator2 = random.randint(1, 10)
        denominator2 = denominator1  # Same denominator for simplicity
        
        result_numerator = numerator1 + numerator2
        question = f"{numerator1}/{denominator1} + {numerator2}/{denominator2} = ?"
        
        # Simplify if possible
        from math import gcd
        common_divisor = gcd(result_numerator, denominator1)
        answer = f"{result_numerator // common_divisor}/{denominator1 // common_divisor}"
        
    elif activity_type == 'decimals':
        a = round(random.uniform(1, 10), 1)
        b = round(random.uniform(1, 10), 1)
        question = f"{a} + {b} = ?"
        answer = round(a + b, 1)
        
    elif activity_type == 'word-problems':
        scenarios = [
            {
                'question': f"Sarah has {random.randint(10, 50)} apples. She gives away {random.randint(5, 20)} apples. How many apples does she have left?",
                'type': 'subtraction'
            },
            {
                'question': f"A box contains {random.randint(5, 15)} rows of {random.randint(3, 8)} cookies each. How many cookies are in the box?",
                'type': 'multiplication'
            }
        ]
        
        scenario = random.choice(scenarios)
        question = scenario['question']
        
        # Extract numbers and calculate answer
        import re
        numbers = [int(x) for x in re.findall(r'\d+', question)]
        if scenario['type'] == 'subtraction':
            answer = numbers[0] - numbers[1]
        elif scenario['type'] == 'multiplication':
            answer = numbers[0] * numbers[1]
    
    else:
        # Default to simple addition
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        question = f"{a} + {b} = ?"
        answer = a + b
    
    return {'question': question, 'answer': answer}

def save_practice_result(user_id, activity_type, score, total_questions):
    """Save practice results to CSV file"""
    try:
        # Ensure data directory exists
        os.makedirs('data/dyscalculia', exist_ok=True)
        
        # File path for math practice results
        file_path = f'data/dyscalculia/math_practice_{user_id}.csv'
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(file_path)
        
        # Save result
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write headers if file is new
            if not file_exists:
                writer.writerow(['timestamp', 'activity_type', 'score', 'total_questions', 'percentage'])
            
            # Write result
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            percentage = round((score / total_questions) * 100, 1)
            writer.writerow([timestamp, activity_type, score, total_questions, percentage])
            
        print(f"Saved math practice result: {activity_type}, Score: {score}/{total_questions}")
        
    except Exception as e:
        print(f"Error saving math practice result: {e}")
