from flask import Blueprint, jsonify, request, current_app
from flask_restx import Resource, Api, fields
import datetime
import pytz
from database.database import DatabaseManager

app_blueprint = Blueprint('app', __name__)

api = Api(app_blueprint, version='1.0', title='Model Serving API', description='API for AI model predictions.')
ns = api.namespace('prediction', description='Prediction related operations')

prediction_model = api.model("prediction", {
    "feature_1": fields.Float(description="Feature 1"),
    "feature_2": fields.Float(description="Feature 2")
})

@ns.route('/results')
class PredictResource(Resource):
    @api.expect(prediction_model)
    def post(self):
        """
        Handle POST requests via JSON body to collect the prediction of the ML model.

        Returns:
        - A JSON response with prediction results or error messages.
        """
        
        model = current_app.model
        desired_timezone = current_app.desired_timezone
        logger = current_app.logger
        database_path = current_app.database_path

        db_manager = DatabaseManager(database_path)

        current_time = datetime.datetime.now(pytz.timezone(desired_timezone)).isoformat()

        try:
            feature_1 = float(request.json['feature_1'])
            feature_2 = float(request.json['feature_2'])
            prediction = model.predict([[feature_1, feature_2]])[0]

            last_id = db_manager.write(current_time, feature_1, feature_2, prediction)

            response = {
                "data": current_time,
                "predicao": round(prediction, 5),
                "id": last_id
            }
            
            logger.info(f"status: 200, id: {last_id}, feature_1: {feature_1}, feature_2: {feature_2}, predição: {prediction}")
            return jsonify(response)

        except ValueError as ve: 
            # Handling value errors caused by invalid input data
            error_message = f"Invalid input data: {str(ve)}"
            last_id = db_manager.write(current_time, feature_1=None, feature_2=None, prediction=None)
            logger.error(f"status: 400, id: {last_id}, mensagem de erro: {error_message}")
            return jsonify({"error": error_message}), 400

        except Exception as e:
            # Handling unexpected errors
            error_message = f"Unexpected error: {str(e)}"
            last_id = db_manager.write(current_time, feature_1=None, feature_2=None, prediction=None)
            logger.error(f"status: 500, id: {last_id}, mensagem de erro: {error_message}")
            return jsonify({"error": error_message}), 500