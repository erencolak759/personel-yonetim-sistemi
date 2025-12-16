from api.auth import auth_bp
from api.home import home_bp
from api.employee import employee_bp
from api.leave import leave_bp
from api.attendance import attendance_bp
from api.salary import salary_bp
from api.settings import settings_bp
from api.announcement import announcement_bp
from api.candidate import candidate_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(salary_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(candidate_bp)
