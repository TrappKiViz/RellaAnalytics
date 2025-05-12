from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from ..models.analytics_schema import Transaction, Client, Staff, Appointment, MarketingMetrics, FinancialMetrics
from ..database import db_session

analytics = Blueprint('analytics', __name__)

@analytics.route('/api/v1/kpis/revenue', methods=['GET'])
def get_revenue_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Total sales and breakdown by category
    sales_by_category = db_session.query(
        Transaction.service_category,
        func.sum(Transaction.gross_sales).label('gross_sales'),
        func.sum(Transaction.net_sales).label('net_sales'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(Transaction.service_category).all()
    
    # Average ticket size
    avg_ticket = db_session.query(
        func.avg(Transaction.net_sales)
    ).filter(
        Transaction.date.between(start_date, end_date),
        Transaction.net_sales > 0
    ).scalar()
    
    return jsonify({
        'sales_by_category': [
            {
                'category': cat,
                'gross_sales': gross,
                'net_sales': net,
                'transaction_count': count
            } for cat, gross, net, count in sales_by_category
        ],
        'average_ticket_size': float(avg_ticket) if avg_ticket else 0
    })

@analytics.route('/api/v1/kpis/patient', methods=['GET'])
def get_patient_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # New patients
    new_patients = db_session.query(
        func.count(Client.id)
    ).filter(
        Client.first_visit_date.between(start_date, end_date)
    ).scalar()
    
    # Marketing ROI
    marketing_metrics = db_session.query(
        MarketingMetrics.channel,
        func.sum(MarketingMetrics.revenue).label('revenue'),
        func.sum(MarketingMetrics.cost).label('cost'),
        func.sum(MarketingMetrics.leads).label('leads'),
        func.sum(MarketingMetrics.bookings).label('bookings')
    ).filter(
        MarketingMetrics.date.between(start_date, end_date)
    ).group_by(MarketingMetrics.channel).all()
    
    return jsonify({
        'new_patients': new_patients,
        'marketing_metrics': [
            {
                'channel': channel,
                'revenue': revenue,
                'cost': cost,
                'roi': (revenue - cost) / cost if cost > 0 else 0,
                'cost_per_lead': cost / leads if leads > 0 else 0,
                'cost_per_booking': cost / bookings if bookings > 0 else 0
            } for channel, revenue, cost, leads, bookings in marketing_metrics
        ]
    })

@analytics.route('/api/v1/kpis/retention', methods=['GET'])
def get_retention_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Patient return rate (patients with >1 visit / total patients)
    return_rate = db_session.query(
        func.count(Client.id).filter(Client.total_visits > 1).label('returning'),
        func.count(Client.id).label('total')
    ).first()
    
    # Membership conversion
    membership_stats = db_session.query(
        func.count(Client.id).filter(Client.is_member == True).label('members'),
        func.count(Client.id).label('total')
    ).first()
    
    # Upsell rate (transactions with multiple services/products)
    upsell_data = db_session.query(
        func.count(Transaction.client_id).label('transactions_with_upsell')
    ).filter(
        Transaction.date.between(start_date, end_date),
        Transaction.net_sales > 0
    ).group_by(Transaction.client_id).having(func.count(Transaction.id) > 1).count()
    
    return jsonify({
        'return_rate': return_rate[0] / return_rate[1] if return_rate[1] > 0 else 0,
        'membership_rate': membership_stats[0] / membership_stats[1] if membership_stats[1] > 0 else 0,
        'upsell_rate': upsell_data
    })

@analytics.route('/api/v1/kpis/productivity', methods=['GET'])
def get_productivity_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Revenue per provider per hour
    provider_metrics = db_session.query(
        Staff.name,
        func.sum(Transaction.net_sales).label('revenue'),
        func.sum(Appointment.duration_minutes).label('total_minutes')
    ).join(Transaction, Staff.id == Transaction.staff_id
    ).join(Appointment, Staff.id == Appointment.provider_id
    ).filter(
        Transaction.date.between(start_date, end_date)
    ).group_by(Staff.id).all()
    
    # Room utilization
    room_utilization = db_session.query(
        Appointment.room_id,
        func.count(Appointment.id).label('appointments'),
        func.sum(Appointment.duration_minutes).label('total_minutes')
    ).filter(
        Appointment.date.between(start_date, end_date)
    ).group_by(Appointment.room_id).all()
    
    return jsonify({
        'provider_productivity': [
            {
                'provider': name,
                'revenue_per_hour': (revenue / (minutes / 60)) if minutes > 0 else 0,
                'total_revenue': revenue
            } for name, revenue, minutes in provider_metrics
        ],
        'room_utilization': [
            {
                'room_id': room,
                'utilization_rate': (minutes / (8 * 60 * 30)) if minutes else 0  # Assuming 8-hour days
            } for room, appts, minutes in room_utilization
        ]
    })

@analytics.route('/api/v1/kpis/operations', methods=['GET'])
def get_operations_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Calculate no-show and cancellation rates
    appointment_stats = db_session.query(
        Appointment.status,
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.date.between(start_date, end_date)
    ).group_by(Appointment.status).all()
    
    total_appointments = sum(count for _, count in appointment_stats)
    status_counts = {status: count for status, count in appointment_stats}
    
    # Calculate time to first available appointment
    next_available = db_session.query(
        func.min(Appointment.date)
    ).filter(
        Appointment.date > datetime.now(),
        Appointment.status == 'scheduled'
    ).scalar()
    
    return jsonify({
        'no_show_rate': status_counts.get('no-show', 0) / total_appointments if total_appointments > 0 else 0,
        'cancellation_rate': status_counts.get('cancelled', 0) / total_appointments if total_appointments > 0 else 0,
        'days_to_next_available': (next_available - datetime.now()).days if next_available else None
    })

@analytics.route('/api/v1/kpis/financial', methods=['GET'])
def get_financial_metrics():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Revenue
    revenue = db_session.query(
        func.sum(Transaction.net_sales)
    ).filter(
        Transaction.date.between(start_date, end_date)
    ).scalar() or 0
    
    # Expenses by category
    expenses = db_session.query(
        FinancialMetrics.category,
        func.sum(FinancialMetrics.amount).label('amount')
    ).filter(
        FinancialMetrics.date.between(start_date, end_date),
        FinancialMetrics.is_expense == True
    ).group_by(FinancialMetrics.category).all()
    
    total_expenses = sum(amount for _, amount in expenses)
    expense_breakdown = {category: amount for category, amount in expenses}
    
    return jsonify({
        'revenue': revenue,
        'total_expenses': total_expenses,
        'profit_margin': (revenue - total_expenses) / revenue if revenue > 0 else 0,
        'payroll_percentage': expense_breakdown.get('payroll', 0) / revenue if revenue > 0 else 0,
        'rent_percentage': expense_breakdown.get('rent', 0) / revenue if revenue > 0 else 0,
        'supplies_percentage': expense_breakdown.get('supplies', 0) / revenue if revenue > 0 else 0
    }) 