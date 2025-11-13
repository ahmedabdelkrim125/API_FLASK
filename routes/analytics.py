from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Field, Booking, Payment, Review, Analytics
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Query
import csv
import io
from utils import t, create_response, create_error_response

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Initialize response data
        dashboard_data: dict = {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
        
        # For admins, show overall platform stats
        if user.role == 'admin':
            # Total users
            total_users = User.query.count()
            
            # Total fields
            total_fields = Field.query.count()
            
            # Total bookings
            total_bookings = Booking.query.filter(
                Booking.date.between(start_date, end_date)
            ).count()
            
            # Total revenue
            total_revenue = db.session.query(func.sum(Payment.amount)).filter(
                Payment.status == 'completed',
                Payment.completed_at >= datetime.combine(start_date, datetime.min.time()),
                Payment.completed_at <= datetime.combine(end_date, datetime.max.time())
            ).scalar() or 0
            
            # Average field rating
            avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
            
            dashboard_data.update({
                'total_users': total_users,
                'total_fields': total_fields,
                'total_bookings': total_bookings,
                'total_revenue': round(float(total_revenue), 2),
                'average_field_rating': round(float(avg_rating), 2)
            })
        
        # For field owners, show their field stats
        elif user.role == 'owner':
            # Get owner's fields
            fields = Field.query.filter_by(owner_id=user.id).all()
            field_ids = [field.id for field in fields]
            
            # Total bookings for owner's fields
            total_bookings = Booking.query.filter(
                Booking.field_id.in_(field_ids),
                Booking.date.between(start_date, end_date)
            ).count()
            
            # Total revenue from owner's fields
            total_revenue = db.session.query(func.sum(Payment.amount)).join(Booking).filter(
                Booking.field_id.in_(field_ids),
                Payment.status == 'completed',
                Payment.completed_at >= datetime.combine(start_date, datetime.min.time()),
                Payment.completed_at <= datetime.combine(end_date, datetime.max.time())
            ).scalar() or 0
            
            # Average rating for owner's fields
            avg_rating = db.session.query(func.avg(Review.rating)).filter(
                Review.field_id.in_(field_ids)
            ).scalar() or 0
            
            # Field utilization (total booked hours / total available hours)
            total_booked_hours = 0
            total_available_hours = 0
            
            for field in fields:
                # Get bookings for this field in the date range
                bookings = Booking.query.filter(
                    Booking.field_id == field.id,
                    Booking.date.between(start_date, end_date),
                    Booking.status != 'cancelled'
                ).all()
                
                # Calculate booked hours
                for booking in bookings:
                    booked_duration = datetime.combine(date.min, booking.end_time) - datetime.combine(date.min, booking.start_time)
                    total_booked_hours += booked_duration.total_seconds() / 3600
                
                # Calculate available hours (assuming 14 hours per day: 8AM-10PM)
                days_in_range = (end_date - start_date).days + 1
                total_available_hours += days_in_range * 14  # 14 hours per day
            
            utilization_rate = (total_booked_hours / total_available_hours * 100) if total_available_hours > 0 else 0
            
            dashboard_data.update({
                'total_fields': len(fields),
                'total_bookings': total_bookings,
                'total_revenue': round(float(total_revenue), 2),
                'average_field_rating': round(float(avg_rating), 2),
                'field_utilization_rate': round(utilization_rate, 2)
            })
        
        # For regular users, show their booking stats
        else:
            # Total bookings by user
            total_bookings = Booking.query.filter(
                Booking.user_id == user.id,
                Booking.date.between(start_date, end_date)
            ).count()
            
            # Total spent by user
            total_spent = db.session.query(func.sum(Payment.amount)).filter(
                Payment.user_id == user.id,
                Payment.status == 'completed',
                Payment.completed_at >= datetime.combine(start_date, datetime.min.time()),
                Payment.completed_at <= datetime.combine(end_date, datetime.max.time())
            ).scalar() or 0
            
            # Average rating given by user
            avg_rating = db.session.query(func.avg(Review.rating)).filter(
                Review.user_id == user.id
            ).scalar() or 0
            
            dashboard_data.update({
                'total_bookings': total_bookings,
                'total_spent': round(float(total_spent), 2),
                'average_rating_given': round(float(avg_rating), 2)
            })
        
        return jsonify(create_response('analytics_dashboard_retrieved_successfully', {
            'user_role': user.role,
            'summary': dashboard_data
        })), 200
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@analytics_bp.route('/analytics/bookings/trends', methods=['GET'])
@jwt_required()
def get_booking_trends():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Build query based on user role
        query = db.session.query(
            func.date(Booking.date).label('booking_date'),
            func.count(Booking.id).label('booking_count')
        )
        
        # Filter based on user role
        if user.role == 'admin':
            # Admin sees all bookings
            query = query.filter(Booking.date.between(start_date, end_date))
        elif user.role == 'owner':
            # Owner sees bookings for their fields
            field_ids = db.session.query(Field.id).filter(Field.owner_id == user.id).subquery()
            query = query.join(Field).filter(
                Booking.field_id.in_(field_ids),
                Booking.date.between(start_date, end_date)
            )
        else:
            # Regular user sees their own bookings
            query = query.filter(
                Booking.user_id == user.id,
                Booking.date.between(start_date, end_date)
            )
        
        # Group by date
        query = query.group_by(func.date(Booking.date)).order_by(func.date(Booking.date))
        
        # Execute query
        results = query.all()
        
        # Format results
        trends_data = []
        for result in results:
            trends_data.append({
                'date': result.booking_date.isoformat(),
                'bookings': result.booking_count
            })
        
        return jsonify({
            'trends': trends_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'group_by': group_by
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching booking trends', 'error': str(e)}), 500

@analytics_bp.route('/analytics/revenue/trends', methods=['GET'])
@jwt_required()
def get_revenue_trends():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Build query based on user role
        query = db.session.query(
            func.date(Payment.completed_at).label('payment_date'),
            func.sum(Payment.amount).label('revenue')
        ).filter(Payment.status == 'completed')
        
        # Filter based on user role
        if user.role == 'admin':
            # Admin sees all payments
            query = query.filter(
                func.date(Payment.completed_at).between(start_date, end_date)
            )
        elif user.role == 'owner':
            # Owner sees payments for their fields
            field_ids = db.session.query(Field.id).filter(Field.owner_id == user.id).subquery()
            query = query.join(Booking).filter(
                Booking.field_id.in_(field_ids),
                func.date(Payment.completed_at).between(start_date, end_date)
            )
        else:
            # Regular user sees their own payments
            query = query.filter(
                Payment.user_id == user.id,
                func.date(Payment.completed_at).between(start_date, end_date)
            )
        
        # Group by date
        query = query.group_by(func.date(Payment.completed_at)).order_by(func.date(Payment.completed_at))
        
        # Execute query
        results = query.all()
        
        # Format results
        trends_data = []
        for result in results:
            trends_data.append({
                'date': result.payment_date.isoformat(),
                'revenue': float(result.revenue) if result.revenue else 0
            })
        
        return jsonify({
            'trends': trends_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'group_by': group_by
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching revenue trends', 'error': str(e)}), 500

@analytics_bp.route('/analytics/fields/performance', methods=['GET'])
@jwt_required()
def get_field_performance():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Only owners and admins can access field performance
        if user.role not in ['owner', 'admin']:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get fields based on user role
        if user.role == 'admin':
            fields = Field.query.all()
        else:
            fields = Field.query.filter_by(owner_id=user.id).all()
        
        # Calculate performance metrics for each field
        performance_data = []
        for field in fields:
            # Total bookings for this field
            total_bookings = Booking.query.filter(
                Booking.field_id == field.id,
                Booking.date.between(start_date, end_date),
                Booking.status != 'cancelled'
            ).count()
            
            # Total revenue from this field
            total_revenue = db.session.query(func.sum(Payment.amount)).join(Booking).filter(
                Booking.field_id == field.id,
                Payment.status == 'completed',
                Payment.completed_at >= datetime.combine(start_date, datetime.min.time()),
                Payment.completed_at <= datetime.combine(end_date, datetime.max.time())
            ).scalar() or 0
            
            # Average rating for this field
            avg_rating = db.session.query(func.avg(Review.rating)).filter(
                Review.field_id == field.id
            ).scalar() or 0
            
            # Calculate utilization rate
            # Get bookings for this field in the date range
            bookings = Booking.query.filter(
                Booking.field_id == field.id,
                Booking.date.between(start_date, end_date),
                Booking.status != 'cancelled'
            ).all()
            
            # Calculate booked hours
            total_booked_hours = 0
            for booking in bookings:
                booked_duration = datetime.combine(date.min, booking.end_time) - datetime.combine(date.min, booking.start_time)
                total_booked_hours += booked_duration.total_seconds() / 3600
            
            # Calculate available hours (assuming 14 hours per day: 8AM-10PM)
            days_in_range = (end_date - start_date).days + 1
            total_available_hours = days_in_range * 14  # 14 hours per day
            
            utilization_rate = (total_booked_hours / total_available_hours * 100) if total_available_hours > 0 else 0
            
            performance_data.append({
                'field_id': field.id,
                'field_name': field.name,
                'total_bookings': total_bookings,
                'total_revenue': round(float(total_revenue), 2),
                'average_rating': round(float(avg_rating), 2),
                'utilization_rate': round(utilization_rate, 2)
            })
        
        return jsonify({
            'performance': performance_data,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching field performance', 'error': str(e)}), 500

@analytics_bp.route('/analytics/export/bookings', methods=['GET'])
@jwt_required()
def export_bookings_data():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Only admins and owners can export data
        if user.role not in ['admin', 'owner']:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Build query based on user role
        query: Query = db.session.query(
            func.coalesce(Booking.id, Booking.id).label('id'),
            func.coalesce(Booking.date, Booking.date).label('date'),
            func.coalesce(Booking.start_time, Booking.start_time).label('start_time'),
            func.coalesce(Booking.end_time, Booking.end_time).label('end_time'),
            func.coalesce(Booking.total_price, Booking.total_price).label('total_price'),
            func.coalesce(Booking.status, Booking.status).label('status'),
            User.name.label('user_name'),
            User.email.label('user_email'),
            Field.name.label('field_name')
        ).join(User, Booking.user_id == User.id).join(Field, Booking.field_id == Field.id)
        
        # Filter based on user role
        if user.role == 'admin':
            # Admin sees all bookings
            query = query.filter(Booking.date.between(start_date, end_date))
        else:
            # Owner sees bookings for their fields
            field_ids = db.session.query(Field.id).filter(Field.owner_id == user.id).subquery()
            query = query.filter(
                Booking.field_id.in_(field_ids),
                Booking.date.between(start_date, end_date)
            )
        
        # Order by date
        query = query.order_by(Booking.date.desc())
        
        # Execute query
        results = query.all()
        
        # Build CSV response
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Booking ID', 'Date', 'Start Time', 'End Time', 'Total Price', 
            'Status', 'User Name', 'User Email', 'Field Name'
        ])
        
        # Write data
        for row in results:
            writer.writerow([
                row.id, row.date, row.start_time, row.end_time, 
                row.total_price, row.status, row.user_name, 
                row.user_email, row.field_name
            ])
            
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        headers = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=bookings_export.csv'
        }
        
        return Response(csv_data, headers=headers)
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@analytics_bp.route('/analytics/export/payments', methods=['GET'])
@jwt_required()
def export_payments_data():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Only admins and owners can export data
        if user.role not in ['admin', 'owner']:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Set default date range (last 30 days)
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Build query based on user role
        query: Query = db.session.query(
            func.coalesce(Payment.id, Payment.id).label('id'),
            func.coalesce(Payment.amount, Payment.amount).label('amount'),
            func.coalesce(Payment.currency, Payment.currency).label('currency'),
            func.coalesce(Payment.payment_method, Payment.payment_method).label('payment_method'),
            func.coalesce(Payment.status, Payment.status).label('status'),
            func.coalesce(Payment.created_at, Payment.created_at).label('created_at'),
            func.coalesce(Payment.completed_at, Payment.completed_at).label('completed_at'),
            User.name.label('user_name'),
            User.email.label('user_email'),
            Field.name.label('field_name')
        ).join(User, Payment.user_id == User.id).join(Booking, Payment.booking_id == Booking.id).join(Field, Booking.field_id == Field.id)
        
        # Filter based on user role
        if user.role == 'admin':
            # Admin sees all payments
            query = query.filter(
                func.date(Payment.completed_at).between(start_date, end_date)
            )
        else:
            # Owner sees payments for their fields
            field_ids = db.session.query(Field.id).filter(Field.owner_id == user.id).subquery()
            query = query.filter(
                Booking.field_id.in_(field_ids),
                func.date(Payment.completed_at).between(start_date, end_date)
            )
        
        # Order by date
        query = query.order_by(Payment.completed_at.desc())
        
        # Execute query
        results = query.all()
        
        # Build CSV response
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Payment ID', 'Amount', 'Currency', 'Payment Method', 'Status',
            'Created At', 'Completed At', 'User Name', 'User Email', 'Field Name'
        ])
        
        # Write data
        for row in results:
            writer.writerow([
                row.id, row.amount, row.currency, row.payment_method,
                row.status, row.created_at, row.completed_at,
                row.user_name, row.user_email, row.field_name
            ])
            
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        headers = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=payments_export.csv'
        }
        
        return Response(csv_data, headers=headers)
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500

@analytics_bp.route('/analytics/export/users', methods=['GET'])
@jwt_required()
def export_users_data():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        
        # Check if user exists
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Only admins can export user data
        if user.role != 'admin':
            return jsonify({'message': 'Access denied'}), 403
        
        # Build query for all users
        query: Query = db.session.query(
            func.coalesce(User.id, User.id).label('id'),
            func.coalesce(User.name, User.name).label('name'),
            func.coalesce(User.email, User.email).label('email'),
            func.coalesce(User.role, User.role).label('role'),
            func.coalesce(User.phone, User.phone).label('phone'),
            func.coalesce(User.created_at, User.created_at).label('created_at')
        )
        
        # Order by creation date
        query = query.order_by(User.created_at.desc())
        
        # Execute query
        results = query.all()
        
        # Build CSV response
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'User ID', 'Name', 'Email', 'Phone', 'Role', 'Created At',
            'Total Bookings', 'Total Payments', 'Total Reviews'
        ])
        
        # Write data
        for row in results:
            writer.writerow([
                row.id, row.name, row.email, row.phone, row.role,
                row.created_at, row.total_bookings, row.total_payments, row.total_reviews
            ])
            
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        headers = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=users_export.csv'
        }
        
        return Response(csv_data, headers=headers)
        
    except Exception as e:
        return jsonify(create_error_response('internal_server_error', str(e))), 500
